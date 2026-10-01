#!/usr/bin/env python3
"""Launch-day analysis for CAN-Team-25 -- the packets the organizers' ground station logged.

    python analysis/flight-2026-09-30/launch_analysis.py LOG.xlsx --out analysis/flight-2026-09-30

The workbook is what the Physics Club's receiving station exports: one row per received
LoRa packet, with the host timestamp, the packet text, and the radio's own RSSI and SNR.
The same packet appears several times because the file was exported several times, and the
rows are not in time order, so the first job is to make the log into what it should have been:

1. parse every row with the ground station's own parser (``telemetry.parse_packet``) --
   one packet format, one definition;
2. drop the repeated exports (the key is packet number + mission clock);
3. split the rest into **sessions** at every restart of the mission clock;
4. analyse each session on its own, because every session has its own power-on baseline.

Everything the report quotes about the flights is computed here and written to
``results.json``, so a number in the report can be traced to a line of this file.

The altitude correction is the one ``analysis/flight_analysis.py`` documents: the firmware
converts pressure to altitude with the ISA formula, and real height per pascal scales with
the real temperature, so the analysis re-derives height with the hypsometric equation from the
pressure and temperature the vehicle itself measured.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ground-station" / "software" / "src"))
from telemetry import parse_packet  # noqa: E402

G0 = 9.80665
R_DRY = 287.05
P_ISA0 = 101325.0
IST = pd.Timedelta(hours=5, minutes=30)
TEAM = "CAN-Team-25"
LORA_SENSITIVITY_DBM = -123.0   # SX127x typical, SF7 / 125 kHz (Semtech datasheet)
RULEBOOK_MAX_DESCENT = 5.0
CANOPY_DIAMETER_M = 6 * 0.3048          # the flown canopy: 6 ft flat diameter
CANOPY_AREA_M2 = np.pi * (CANOPY_DIAMETER_M / 2) ** 2


# ------------------------------------------------------------------------------------------
# Loading and cleaning
# ------------------------------------------------------------------------------------------

def _ti_seconds(s: str) -> float:
    h, m, sec, ms = s.split(":")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0


def load_raw(xlsx: Path) -> pd.DataFrame:
    """Every row of the workbook, parsed. A row the parser rejects is an error, not a skip."""
    df = pd.read_excel(xlsx)
    rows = []
    for i, r in df.iterrows():
        res = parse_packet(str(r["Data"]), TEAM)
        if res.error is not None:
            raise ValueError(f"row {i}: {res.error}")
        rec, t = res.record, res.record.tags
        rows.append(dict(
            row=i, file=r["_source_file"],
            host_utc=pd.Timestamp(r["Timestamp"]), bytes=r["PacketSize"],
            rssi=float(r["RSSI_dBm"]), snr=float(r["SNR_dB"]),
            P=rec.packet_number, ti=_ti_seconds(rec.timestamp),
            A=rec.altitude, Pr=rec.pressure, T=rec.temperature,
            Ro=rec.roll, Pi=rec.pitch, Ya=rec.yaw,
            AX=rec.ax, AY=rec.ay, AZ=rec.az,
            lat=float(t["GP-Lat"]) if "GP-Lat" in t else np.nan,
            lon=float(t["GP-Lon"]) if "GP-Lon" in t else np.nan,
            galt=float(t["GP-Alt"]) if "GP-Alt" in t else np.nan,
            SN=float(t["SN"]) if "SN" in t else np.nan,
            ST=t.get("ST"), MODE=t.get("MODE"), ARM=t.get("ARM"),
            CAL=t.get("CAL"), FAULTS=t.get("FAULTS"),
            text=str(r["Data"]),
        ))
    return pd.DataFrame(rows)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per distinct packet, in the order the vehicle sent them within each session."""
    d = raw.drop_duplicates(["P", "ti"]).copy()
    # A session is a run of packets whose mission clock is continuous. The log is not in
    # time order (two exports were concatenated), so order by the host clock first and
    # break wherever the mission clock steps backwards or the packet counter jumps.
    d = d.sort_values(["host_utc", "ti"]).reset_index(drop=True)
    new = (d["ti"].diff() < 0) | (d["P"].diff().abs() > 400) | (d["host_utc"].diff().dt.total_seconds() > 120)
    # the mission clock of one power cycle only ever grows, so sort each by it
    d["session"] = new.cumsum()
    d = d.sort_values(["session", "ti"]).reset_index(drop=True)
    d["a_mag"] = np.sqrt(d.AX ** 2 + d.AY ** 2 + d.AZ ** 2)
    d["rich"] = d["ST"].notna()
    d["host_ist"] = d["host_utc"] + IST
    return d


# ------------------------------------------------------------------------------------------
# Physics helpers
# ------------------------------------------------------------------------------------------

def isa_altitude(p):
    """The firmware's conversion: sensors::pressure_altitude_m()."""
    return 44330.0 * (1.0 - (np.asarray(p) / P_ISA0) ** (1.0 / 5.255))


def isa_pressure(h):
    return P_ISA0 * (1.0 - np.asarray(h) / 44330.0) ** 5.255


def hypsometric_height(p, p_ref, t_c):
    """Height of pressure p above the level where the pressure is p_ref, for air at t_c."""
    tk = np.asarray(t_c) + 273.15
    return (R_DRY * tk / G0) * np.log(p_ref / np.asarray(p))


def air_density(p, t_c):
    return np.asarray(p) / (R_DRY * (np.asarray(t_c) + 273.15))


def baseline_from_reported(session: pd.DataFrame) -> tuple[float, float]:
    """Recover the firmware's ground baseline from the altitudes it reported.

    reported = isa(p) - c, so c is the mean difference and the baseline pressure is isa^-1(c).
    The residual says how well the ISA formula reproduces the vehicle's own numbers."""
    c = (isa_altitude(session.Pr) - session.A)
    c0 = float(c.median())
    resid = (isa_altitude(session.Pr) - c0 - session.A)
    return float(isa_pressure(c0)), float(resid.std())


def local_rate(t: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Central-difference vertical speed (m/s, + up) on an irregular grid."""
    v = np.full(len(t), np.nan)
    for i in range(len(t)):
        a, b = max(i - 1, 0), min(i + 1, len(t) - 1)
        if b > a:
            v[i] = (h[b] - h[a]) / (t[b] - t[a])
    return v


@dataclass
class Fit:
    slope: float
    intercept: float
    se: float
    r2: float
    n: int


def linfit(t, y) -> Fit:
    res = stats.linregress(t, y)
    return Fit(res.slope, res.intercept, res.stderr, res.rvalue ** 2, len(t))


# ------------------------------------------------------------------------------------------
# The analysis proper
# ------------------------------------------------------------------------------------------

def analyse(d: pd.DataFrame, raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out: dict = {}

    # ---- data quality -------------------------------------------------------------------
    out["rows_in_workbook"] = int(len(raw))
    out["distinct_packets"] = int(len(d))
    out["duplicate_rows"] = int(len(raw) - len(d))
    out["source_files"] = int(raw["file"].nunique())
    out["packets_parsed_ok"] = int(len(raw))          # load_raw raises on the first failure
    out["team_id_correct_in_all"] = bool(raw["text"].str.startswith(TEAM + ";").all())
    out["sessions"] = int(d["session"].nunique())

    sess_meta = []
    for s, g in d.groupby("session"):
        sess_meta.append(dict(
            session=int(s), first_packet=int(g.P.iloc[0]), last_packet=int(g.P.iloc[-1]),
            packets=int(len(g)), t0=float(g.ti.iloc[0]), t1=float(g.ti.iloc[-1]),
            host_start_ist=str(g.host_ist.min()), host_end_ist=str(g.host_ist.max()),
        ))
    out["session_table"] = sess_meta

    # name the sessions by what they contain
    names = {}
    for m in sess_meta:
        if m["packets"] <= 3:
            names[m["session"]] = "S0"
        elif m["first_packet"] > 1000:
            names[m["session"]] = "F1"
        elif m["first_packet"] == 1:
            names[m["session"]] = "G1"
        else:
            names[m["session"]] = "F2"
    d["name"] = d["session"].map(names)
    out["names"] = {str(k): v for k, v in names.items()}

    # ---- per-session reconstruction of altitude -----------------------------------------
    d["h_base"] = np.nan      # corrected height above the vehicle's own baseline
    d["p_base"] = np.nan
    base_info = {}
    for nm, g in d.groupby("name"):
        if nm == "G1":
            # G1's reported altitude includes the uncalibrated first 5.5 s; use the calibrated part
            gc = g[g.A.abs() < 3]
            pb, res = baseline_from_reported(gc)
        else:
            pb, res = baseline_from_reported(g)
        base_info[nm] = dict(p_base_pa=pb, isa_residual_m=res)
        d.loc[g.index, "p_base"] = pb
        d.loc[g.index, "h_base"] = hypsometric_height(g.Pr, pb, g["T"])
    out["baseline"] = base_info

    # ---- packet stream ------------------------------------------------------------------
    stream = {}
    for nm, g in d.groupby("name"):
        P = g.P.to_numpy()
        expected = int(P.max() - P.min() + 1)
        missing = sorted(set(range(int(P.min()), int(P.max()) + 1)) - set(P.tolist()))
        dt = np.diff(g.ti.to_numpy())
        stream[nm] = dict(
            received=int(len(g)), expected=expected, missing=[int(x) for x in missing],
            reception_pct=100.0 * len(g) / expected,
            duration_s=float(g.ti.iloc[-1] - g.ti.iloc[0]),
            rate_hz=float((len(g) - 1) / (g.ti.iloc[-1] - g.ti.iloc[0])) if len(g) > 1 else None,
            median_dt=float(np.median(dt)) if len(dt) else None,
            mean_bytes=float(g.bytes.mean()) if g.bytes.notna().any() else None,
        )
    out["stream"] = stream

    # ---- flight 1 ----------------------------------------------------------------------
    f1 = d[d.name == "F1"].reset_index()
    out["F1"] = analyse_flight1(f1, d)
    f2 = d[d.name == "F2"].reset_index()
    out["F2"] = analyse_flight2(f2)
    g1 = d[d.name == "G1"].reset_index()
    out["G1"] = analyse_ground(g1)
    s0 = d[d.name == "S0"].reset_index()
    out["S0"] = dict(packets=int(len(s0)), ti_s=[float(x) for x in s0.ti],
                     altitude_m=[float(x) for x in s0.A], rssi=[float(x) for x in s0.rssi],
                     snr=[float(x) for x in s0.snr], state=list(s0.ST.dropna().unique()))

    # landing-site height in F1 relative to the F1 baseline, from G1's settled pressure
    pg = out["G1"]["pressure_mean_pa"]
    pb1 = base_info["F1"]["p_base_pa"]
    out["F1"]["landing_site_above_baseline_m"] = float(hypsometric_height(pg, pb1, f1["T"].mean()))

    # ---- cross-session numbers ----------------------------------------------------------
    out["link"] = analyse_link(d)
    out["correlations"] = analyse_correlations(d)
    return d, out


def _descent_window(g: pd.DataFrame, t_start: float, t_end: float):
    return g[(g.ti >= t_start) & (g.ti <= t_end)]


def analyse_flight1(f1: pd.DataFrame, d: pd.DataFrame) -> dict:
    r: dict = {}
    t = f1.ti.to_numpy()
    h = f1.h_base.to_numpy()
    # the hover: before the release shock
    hover = f1[f1.ti < 677.3]
    r["hover"] = dict(
        packets=int(len(hover)), t0=float(hover.ti.iloc[0]), t1=float(hover.ti.iloc[-1]),
        reported_alt_mean=float(hover.A.mean()), reported_alt_sd=float(hover.A.std()),
        corrected_height_m=float(hover.h_base.mean()),
        corrected_height_ft=float(hover.h_base.mean() / 0.3048),
        pressure_mean_pa=float(hover.Pr.mean()),
    )
    # release shock: the largest specific force of the record
    k = int(f1.a_mag.idxmax())
    rel = f1.loc[k]
    r["release"] = dict(packet=int(rel.P), ti=float(rel.ti), a_mag=float(rel.a_mag), a_g=float(rel.a_mag / G0),
                        ax=float(rel.AX), ay=float(rel.AY), az=float(rel.AZ), rssi_before=float(f1.loc[k - 1, "rssi"]),
                        rssi_after=float(f1.loc[k, "rssi"]))
    # apogee of the release: the highest height
    kp = int(f1.h_base.idxmax())
    r["peak"] = dict(packet=int(f1.loc[kp, "P"]), ti=float(f1.loc[kp, "ti"]),
                     reported_m=float(f1.loc[kp, "A"]), corrected_m=float(f1.loc[kp, "h_base"]))
    # the throw: the vehicle rises above its hold height before it falls -- a projectile arc
    rise = float(f1.loc[kp, "h_base"] - hover.h_base.mean())
    r["throw"] = dict(rise_m=rise, v0_mps=float(np.sqrt(2 * G0 * rise)), t_to_apex_s=float(np.sqrt(2 * G0 * rise) / G0),
                      observed_t_s=float(f1.loc[kp, "ti"] - hover.ti.iloc[-1]),
                      hold_s=float(hover.ti.iloc[-1] - hover.ti.iloc[0]))
    # canopy opening: the largest specific force after the peak
    after = f1[f1.index > kp]
    kc = int(after.a_mag.iloc[:6].idxmax())
    r["canopy_opening"] = dict(packet=int(f1.loc[kc, "P"]), ti=float(f1.loc[kc, "ti"]),
                               a_mag=float(f1.loc[kc, "a_mag"]), a_g=float(f1.loc[kc, "a_mag"] / G0),
                               height_m=float(f1.loc[kc, "h_base"]))
    # vertical speed
    f1["v"] = local_rate(t, h)
    # steady descent: from the first sample after the canopy-opening sample to the last
    steady = f1[f1.index > kc]
    fit = linfit(steady.ti, steady.h_base)
    r["steady"] = dict(t0=float(steady.ti.iloc[0]), t1=float(steady.ti.iloc[-1]), n=int(len(steady)),
                       rate_mps=float(-fit.slope), rate_se=float(fit.se), r2=float(fit.r2),
                       rate_reported_mps=float(-linfit(steady.ti, steady.A).slope),
                       height_start_m=float(steady.h_base.iloc[0]), height_end_m=float(steady.h_base.iloc[-1]))
    # core steady segment (stop before the touchdown dynamics of the last three packets)
    core = steady.iloc[:-3]
    fc = linfit(core.ti, core.h_base)
    r["steady_core"] = dict(t0=float(core.ti.iloc[0]), t1=float(core.ti.iloc[-1]), n=int(len(core)),
                            rate_mps=float(-fc.slope), rate_se=float(fc.se), r2=float(fc.r2))
    # the fastest local speed (free fall, before the canopy filled)
    ff = f1[(f1.index > kp) & (f1.index <= kc)]
    r["peak_speed"] = dict(mps=float(-ff.v.min()), at_packet=int(ff.loc[ff.v.idxmin(), "P"]))
    # free-fall check: height lost between the peak and the canopy opening
    r["freefall"] = dict(t=float(f1.loc[kc, "ti"] - f1.loc[kp, "ti"]),
                         drop_m=float(f1.loc[kp, "h_base"] - f1.loc[kc, "h_base"]))
    # descent totals
    r["descent"] = dict(
        from_release_to_last_packet_s=float(f1.ti.iloc[-1] - f1.loc[kp, "ti"]),
        drop_recorded_m=float(f1.loc[kp, "h_base"] - f1.h_base.iloc[-1]),
        last_packet=int(f1.P.iloc[-1]), last_height_m=float(f1.h_base.iloc[-1]),
    )
    # attitude and loads in the steady descent
    sd = core                      # the steady descent proper -- not the touchdown packets
    r["attitude"] = dict(
        roll_mean=float(sd.Ro.mean()), roll_sd=float(sd.Ro.std()), roll_min=float(sd.Ro.min()), roll_max=float(sd.Ro.max()),
        pitch_mean=float(sd.Pi.mean()), pitch_sd=float(sd.Pi.std()), pitch_min=float(sd.Pi.min()), pitch_max=float(sd.Pi.max()),
        tilt_p50=float(np.percentile(tilt_deg(sd), 50)), tilt_p95=float(np.percentile(tilt_deg(sd), 95)),
        tilt_max=float(tilt_deg(sd).max()),
        a_mag_mean=float(sd.a_mag.mean()), a_mag_sd=float(sd.a_mag.std()),
        az_mean=float(sd.AZ.mean()), az_sd=float(sd.AZ.std()),
        frac_tilt_lt_45=float((tilt_deg(sd) < 45).mean()),
    )
    r["hover_attitude"] = dict(roll_mean=float(hover.Ro.mean()), pitch_mean=float(hover.Pi.mean()),
                               a_mag_mean=float(hover.a_mag.mean()), a_mag_sd=float(hover.a_mag.std()),
                               ay_mean=float(hover.AY.mean()))
    r["rssi"] = dict(hover_mean=float(hover.rssi.mean()), descent_mean=float(sd.rssi.mean()),
                     hover_snr=float(hover.snr.mean()), descent_snr=float(sd.snr.mean()))
    r["sound"] = dict(
        hover_mean=float(hover.SN.mean()), descent_mean=float(sd.SN.mean()),
        peak=float(f1.SN.max()), peak_packet=int(f1.loc[f1.SN.idxmax(), "P"]), n=int(f1.SN.notna().sum()),
    )
    r["temperature"] = dict(mean=float(f1["T"].mean()), min=float(f1["T"].min()), max=float(f1["T"].max()))
    r["pressure"] = dict(min=float(f1.Pr.min()), max=float(f1.Pr.max()), span_pa=float(f1.Pr.max() - f1.Pr.min()))
    r["gps"] = dict(n=int(f1.lat.notna().sum()),
                    lat=[float(x) for x in f1.lat.dropna()], lon=[float(x) for x in f1.lon.dropna()],
                    alt=[float(x) for x in f1.galt.dropna()], packets=[int(x) for x in f1.P[f1.lat.notna()]])
    r["states"] = [str(x) for x in f1.ST.dropna().unique()]
    # ground-track drift under canopy, from the GPS fixes after the canopy opened
    gp = f1[f1.lat.notna() & (f1.ti >= r["canopy_opening"]["ti"])]
    if len(gp) >= 3:
        lat0 = gp.lat.iloc[0]
        dn = (gp.lat.iloc[-1] - gp.lat.iloc[0]) * 111_320.0
        de = (gp.lon.iloc[-1] - gp.lon.iloc[0]) * 111_320.0 * np.cos(np.radians(lat0))
        dt_g = float(gp.ti.iloc[-1] - gp.ti.iloc[0])
        r["gps_drift"] = dict(north_m=float(dn), east_m=float(de), dist_m=float(np.hypot(dn, de)), dt_s=dt_g,
                              speed_mps=float(np.hypot(dn, de) / dt_g), bearing_deg=float((np.degrees(np.arctan2(de, dn)) + 360) % 360))
    # physics of the descent
    rho = float(air_density(sd.Pr.mean(), sd["T"].mean()))
    v = r["steady_core"]["rate_mps"]
    r["physics"] = physics(v, rho)
    return r


def tilt_deg(g: pd.DataFrame) -> np.ndarray:
    """Angle between the vehicle's z axis and the measured specific force -- the swing angle."""
    return np.degrees(np.arccos(np.clip(g.AZ / g.a_mag, -1, 1)))


def physics(v: float, rho: float) -> dict:
    """What a steady descent rate implies, for each mass in the 450-550 g band."""
    res = {"rho_kgm3": rho, "rate_mps": v, "canopy_area_m2": CANOPY_AREA_M2, "canopy_diameter_m": CANOPY_DIAMETER_M, "by_mass": {}}
    # what the descent model predicts for this canopy (vented flat, Cd 0.75) at this air density
    res["model_rate_by_mass"] = {f"{int(m*1000)}": float(np.sqrt(2 * m * G0 / (rho * 0.75 * CANOPY_AREA_M2))) for m in (0.45, 0.50, 0.55)}
    for m in (0.45, 0.50, 0.55):
        cds = 2 * m * G0 / (rho * v ** 2)
        ke = 0.5 * m * v ** 2
        res["by_mass"][f"{int(m*1000)}"] = dict(
            cds_m2=cds, cd_6ft=cds / CANOPY_AREA_M2, ke_J=ke, momentum_Ns=m * v,
            equiv_fall_height_m=v ** 2 / (2 * G0),
            force_25ms_N=m * v / 0.025, force_10ms_N=m * v / 0.010,
            d_cd075_cm=100 * 2 * np.sqrt(cds / 0.75 / np.pi),
            d_cd140_cm=100 * 2 * np.sqrt(cds / 1.40 / np.pi),
        )
    return res


def analyse_flight2(f2: pd.DataFrame) -> dict:
    r: dict = {}
    t = f2.ti.to_numpy()
    h = f2.h_base.to_numpy()
    f2["v"] = local_rate(t, h)
    r["start"] = dict(packet=int(f2.P.iloc[0]), ti=float(f2.ti.iloc[0]), reported_m=float(f2.A.iloc[0]))
    r["end"] = dict(packet=int(f2.P.iloc[-1]), ti=float(f2.ti.iloc[-1]), reported_m=float(f2.A.iloc[-1]))
    r["drop"] = dict(reported_m=float(f2.A.iloc[0] - f2.A.iloc[-1]),
                     corrected_m=float(f2.h_base.iloc[0] - f2.h_base.iloc[-1]),
                     corrected_ft=float((f2.h_base.iloc[0] - f2.h_base.iloc[-1]) / 0.3048),
                     pressure_rise_pa=float(f2.Pr.iloc[-1] - f2.Pr.iloc[0]))
    # touchdown: first packet at the lowest pressure-height
    kl = int(f2.A.idxmin())
    first_low = int(f2.index[f2.A <= f2.A.min() + 0.05][0])
    r["touchdown"] = dict(packet=int(f2.loc[first_low, "P"]), ti=float(f2.loc[first_low, "ti"]),
                          a_mag_after=float(f2.loc[first_low + 1, "a_mag"]) if first_low + 1 < len(f2) else None)
    # steady descent: everything from the second packet to the first low packet
    st = f2[(f2.index >= 1) & (f2.index <= first_low)]
    fit = linfit(st.ti, st.h_base)
    r["steady"] = dict(t0=float(st.ti.iloc[0]), t1=float(st.ti.iloc[-1]), n=int(len(st)),
                       rate_mps=float(-fit.slope), rate_se=float(fit.se), r2=float(fit.r2),
                       rate_reported_mps=float(-linfit(st.ti, st.A).slope))
    r["descent_time_s"] = float(f2.loc[first_low, "ti"] - f2.ti.iloc[0])
    r["mean_rate_mps"] = float((f2.h_base.iloc[0] - f2.loc[first_low, "h_base"]) / r["descent_time_s"])
    r["peak_speed_mps"] = float(-f2.v.min())
    # first-half / second-half rates
    half = len(st) // 2
    r["rate_first_half"] = float(-linfit(st.ti.iloc[:half + 1], st.h_base.iloc[:half + 1]).slope)
    r["rate_second_half"] = float(-linfit(st.ti.iloc[half:], st.h_base.iloc[half:]).slope)
    # the loads: canopy inflation near the start, touchdown at the end
    k_in = int(f2.a_mag.iloc[:6].idxmax())
    r["inflation"] = dict(packet=int(f2.loc[k_in, "P"]), ti=float(f2.loc[k_in, "ti"]), a_mag=float(f2.loc[k_in, "a_mag"]),
                          a_g=float(f2.loc[k_in, "a_mag"] / G0))
    r["touchdown_load"] = dict(a_mag=float(f2.a_mag.iloc[-1]), a_g=float(f2.a_mag.iloc[-1] / G0),
                               ax=float(f2.AX.iloc[-1]), pitch=float(f2.Pi.iloc[-1]))
    sd = st.iloc[:-1]              # without the touchdown packet
    r["attitude"] = dict(
        roll_mean=float(sd.Ro.mean()), roll_sd=float(sd.Ro.std()), roll_min=float(sd.Ro.min()), roll_max=float(sd.Ro.max()),
        pitch_mean=float(sd.Pi.mean()), pitch_sd=float(sd.Pi.std()), pitch_min=float(sd.Pi.min()), pitch_max=float(sd.Pi.max()),
        tilt_p50=float(np.percentile(tilt_deg(sd), 50)), tilt_p95=float(np.percentile(tilt_deg(sd), 95)),
        tilt_max=float(tilt_deg(sd).max()),
        a_mag_mean=float(sd.a_mag.mean()), a_mag_sd=float(sd.a_mag.std()),
        az_mean=float(sd.AZ.mean()), az_sd=float(sd.AZ.std()),
        frac_tilt_lt_45=float((tilt_deg(sd) < 45).mean()),
    )
    r["rssi"] = dict(mean=float(f2.rssi.mean()), min=float(f2.rssi.min()), max=float(f2.rssi.max()),
                     snr_mean=float(f2.snr.mean()), snr_min=float(f2.snr.min()))
    r["sound"] = dict(mean=float(f2.SN.mean()), peak=float(f2.SN.max()), peak_packet=int(f2.loc[f2.SN.idxmax(), "P"]),
                      n=int(f2.SN.notna().sum()))
    r["temperature"] = dict(mean=float(f2["T"].mean()), min=float(f2["T"].min()), max=float(f2["T"].max()))
    r["pressure"] = dict(min=float(f2.Pr.min()), max=float(f2.Pr.max()), span_pa=float(f2.Pr.max() - f2.Pr.min()))
    rho = float(air_density(sd.Pr.mean(), sd["T"].mean()))
    r["physics"] = physics(r["steady"]["rate_mps"], rho)
    r["states"] = [str(x) for x in f2.ST.dropna().unique()]
    r["cadence_s"] = float(np.median(np.diff(f2.ti)))
    return r


def analyse_ground(g1: pd.DataFrame) -> dict:
    """The post-landing session: 13 s of a stationary vehicle -- an unplanned noise measurement."""
    cal = g1[g1.A.abs() < 3]
    unc = g1[g1.A.abs() >= 3]
    r = dict(
        packets=int(len(g1)), duration_s=float(g1.ti.iloc[-1] - g1.ti.iloc[0]),
        first_packet_delay_note="mission clock restarts at 0",
        uncalibrated_packets=int(len(unc)), calibrated_packets=int(len(cal)),
        first_calibrated_ti=float(cal.ti.iloc[0]),
        state_sequence=[str(x) for x in g1.ST.dropna().unique()],
        pressure_mean_pa=float(g1.Pr.mean()), pressure_sd_pa=float(g1.Pr.std()),
        pressure_sd_calibrated_pa=float(cal.Pr.std()),
        altitude_cal_mean=float(cal.A.mean()), altitude_cal_sd=float(cal.A.std()),
        altitude_cal_range=[float(cal.A.min()), float(cal.A.max())],
        alt_uncal_mean=float(unc.A.mean()),
        accel_mag_mean=float(g1.a_mag.mean()), accel_mag_sd=float(g1.a_mag.std()),
        accel_mag_calibrated_mean=float(cal.a_mag.mean()), accel_mag_calibrated_sd=float(cal.a_mag.std()),
        ax_mean=float(cal.AX.mean()), ay_mean=float(cal.AY.mean()), az_mean=float(cal.AZ.mean()),
        ax_sd=float(cal.AX.std()), ay_sd=float(cal.AY.std()), az_sd=float(cal.AZ.std()),
        roll_mean=float(cal.Ro.mean()), roll_sd=float(cal.Ro.std()),
        pitch_mean=float(cal.Pi.mean()), pitch_sd=float(cal.Pi.std()),
        yaw_cal_range=[float(cal.Ya.min()), float(cal.Ya.max())],
        yaw_uncal_drift_dps=float(np.polyfit(unc.ti, np.unwrap(np.radians(unc.Ya)), 1)[0] * 180 / np.pi),
        temperature_mean=float(g1["T"].mean()), temperature_sd=float(g1["T"].std()),
        sound_mean=float(g1.SN.mean()), sound_sd=float(g1.SN.std()), sound_n=int(g1.SN.notna().sum()),
        rssi_mean=float(g1.rssi.mean()), rssi_sd=float(g1.rssi.std()),
        snr_mean=float(g1.snr.mean()), snr_sd=float(g1.snr.std()),
        gps=dict(n=int(g1.lat.notna().sum()), lat_mean=float(g1.lat.mean()), lon_mean=float(g1.lon.mean()),
                 lat_sd=float(g1.lat.std()), lon_sd=float(g1.lon.std()), galt_mean=float(g1.galt.mean())),
        rate_hz=float((len(g1) - 1) / (g1.ti.iloc[-1] - g1.ti.iloc[0])),
        tilt_deg=float(np.degrees(np.arccos(cal.AZ.mean() / cal.a_mag.mean()))),
    )
    # GPS scatter in metres around the mean
    if g1.lat.notna().sum() > 2:
        lat0, lon0 = g1.lat.mean(), g1.lon.mean()
        dn = (g1.lat.dropna() - lat0) * 111_320.0
        de = (g1.lon.dropna() - lon0) * 111_320.0 * np.cos(np.radians(lat0))
        r["gps"]["scatter_m_rms"] = float(np.sqrt((dn ** 2 + de ** 2).mean()))
    return r


def analyse_link(d: pd.DataFrame) -> dict:
    r = {}
    r["rssi_all"] = dict(mean=float(d.rssi.mean()), min=float(d.rssi.min()), max=float(d.rssi.max()), sd=float(d.rssi.std()))
    r["snr_all"] = dict(mean=float(d.snr.mean()), min=float(d.snr.min()), max=float(d.snr.max()), sd=float(d.snr.std()))
    r["margin_to_sensitivity_db"] = dict(
        worst=float(d.rssi.min() - LORA_SENSITIVITY_DBM), mean=float(d.rssi.mean() - LORA_SENSITIVITY_DBM),
        best=float(d.rssi.max() - LORA_SENSITIVITY_DBM))
    rr = stats.pearsonr(d.rssi, d.snr)
    r["rssi_snr"] = dict(r=float(rr.statistic), p=float(rr.pvalue))
    # packet size by shape
    r["bytes_by_shape"] = {}
    for nm, g in d.groupby("name"):
        if g.bytes.notna().any():
            gg = g[g.bytes.notna()]
            r["bytes_by_shape"][nm] = dict(
                rich_mean=float(gg[gg.rich].bytes.mean()) if gg.rich.any() else None,
                lean_mean=float(gg[~gg.rich].bytes.mean()) if (~gg.rich).any() else None,
                max=float(gg.bytes.max()), min=float(gg.bytes.min()))
    allb = d[d.bytes.notna()]
    r["bytes_overall"] = dict(min=float(allb.bytes.min()), max=float(allb.bytes.max()), mean=float(allb.bytes.mean()),
                              n=int(len(allb)))
    # rich/lean pattern in the max-rate sessions
    for nm in ("F1", "G1"):
        g = d[d.name == nm]
        pat = "".join("R" if x else "l" for x in g.rich)
        r[f"pattern_{nm}"] = pat
    return r


CORR_COLS = ["h_base", "Pr", "T", "a_mag", "Ro", "Pi", "SN", "rssi", "snr", "v"]


def analyse_correlations(d: pd.DataFrame) -> dict:
    """Pearson and Spearman between the measured channels, per flight."""
    res = {}
    for nm in ("F1", "F2"):
        g = d[d.name == nm].copy()
        g["v"] = local_rate(g.ti.to_numpy(), g.h_base.to_numpy())
        g["Ro"] = g.Ro.abs()
        g["Pi"] = g.Pi.abs()
        if nm == "F1":
            g = g[g.ti >= 679.0]        # after the canopy opened: the descent proper
        else:
            g = g[g.ti <= 118.4]        # to touchdown
        pairs = {}
        def pr(a, b):
            x = g[[a, b]].dropna()
            if len(x) < 5:
                return None
            p = stats.pearsonr(x[a], x[b]); s = stats.spearmanr(x[a], x[b])
            return dict(n=int(len(x)), pearson=float(p.statistic), p=float(p.pvalue), spearman=float(s.statistic), sp=float(s.pvalue))
        for a, b in [("h_base", "Pr"), ("h_base", "rssi"), ("rssi", "snr"), ("v", "a_mag"), ("v", "SN"),
                     ("a_mag", "SN"), ("Ro", "Pi"), ("h_base", "snr"), ("T", "h_base"), ("Ro", "a_mag"), ("Pi", "a_mag"),
                     ("v", "rssi")]:
            pairs[f"{a}~{b}"] = pr(a, b)
        res[nm] = pairs
        mat = g[CORR_COLS].corr(method="pearson")
        res[nm + "_matrix"] = {c: {k: (None if pd.isna(v) else float(v)) for k, v in mat[c].items()} for c in mat.columns}
    return res


# ------------------------------------------------------------------------------------------
# Command line
# ------------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", type=Path)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent)
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args(argv)
    raw = load_raw(a.xlsx)
    d = clean(raw)
    d, res = analyse(d, raw)
    a.out.mkdir(parents=True, exist_ok=True)
    cols = ["name", "P", "ti", "host_utc", "host_ist", "A", "h_base", "Pr", "T", "Ro", "Pi", "Ya", "AX", "AY", "AZ",
            "a_mag", "lat", "lon", "galt", "SN", "ST", "rssi", "snr", "bytes"]
    d[cols].to_csv(a.out / "flight_data_clean.csv", index=False)
    with open(a.out / "results.json", "w") as f:
        json.dump(res, f, indent=2, default=lambda o: o if not isinstance(o, (np.floating, np.integer)) else o.item())
    if not a.no_figures:
        import launch_figures  # noqa: PLC0415
        launch_figures.make_all(d, res, a.out / "figures")
    print(json.dumps({k: res[k] for k in ("rows_in_workbook", "distinct_packets", "sessions")}, indent=2))
    return d, res


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
