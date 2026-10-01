"""Figures for the launch-day analysis. Every figure is drawn from ``flight_data_clean.csv``
and ``results.json`` -- nothing is typed in by hand.

One visual system throughout: Inter for text, a small fixed palette, light horizontal grid,
no chart junk. Flight 1 is always blue and Flight 2 is always orange-red, so a reader never has
to look at a legend to know which is which.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyBboxPatch
from scipy import stats

FONT_DIR = Path(__file__).resolve().parents[2] / "documentation" / "project" / "report-2026" / "fonts"
for f in FONT_DIR.glob("*.ttf"):
    fm.fontManager.addfont(str(f))

# ---- palette -----------------------------------------------------------------------------
INK = "#0F172A"
MUTED = "#64748B"
GRID = "#E2E8F0"
F1C = "#1D4ED8"      # flight 1
F2C = "#E4572E"      # flight 2
TEAL = "#0F8B8D"
PURPLE = "#7B2CBF"
GOLD = "#F2A900"
GREEN = "#2E9E5B"
RED = "#D1495B"
NAVY = "#0B2545"
SKY = "#8FB8DE"
SEQ = LinearSegmentedColormap.from_list("cs", ["#EFF6FF", "#93C5FD", "#1D4ED8", "#0B2545"])
DIV = LinearSegmentedColormap.from_list("div", ["#E4572E", "#FDE7DD", "#FFFFFF", "#DBEAFE", "#1D4ED8"])

mpl.rcParams.update({
    "font.family": "Inter", "font.size": 8.5, "text.color": INK,
    "axes.labelcolor": INK, "axes.edgecolor": "#CBD5E1", "axes.linewidth": 0.8,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
    "legend.frameon": False, "legend.fontsize": 7.5,
    "figure.dpi": 100, "savefig.dpi": 220, "savefig.bbox": "tight", "savefig.pad_inches": 0.08,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "mathtext.fontset": "custom", "mathtext.rm": "Inter", "mathtext.it": "Inter:italic", "mathtext.bf": "Inter:bold",
})

G0 = 9.80665


def _save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name)
    plt.close(fig)


def _pkt_axis(ax, g, xcol="ti"):
    """Packet number along the top edge, as the rulebook's 'time / packet no.' asks."""
    sec = ax.secondary_xaxis("top", functions=(
        lambda t: np.interp(t, g[xcol], g.P), lambda p: np.interp(p, g.P, g[xcol])))
    sec.set_xlabel("packet number", color=MUTED, fontsize=7.5)
    sec.tick_params(colors=MUTED, labelsize=7)
    sec.spines["top"].set_color("#CBD5E1")
    return sec


def _band(ax, x0, x1, color, label=None, alpha=0.10, y=None, fs=7):
    ax.axvspan(x0, x1, color=color, alpha=alpha, lw=0)
    if label:
        ax.text((x0 + x1) / 2, y if y is not None else 0.97, label, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=fs, color=color, fontweight="bold")


def _tag(ax, x, y, text, dx=0, dy=0, color=INK, ha="left", fs=7.2, arrow=True):
    ax.annotate(text, xy=(x, y), xytext=(x + dx, y + dy), fontsize=fs, color=color, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.7, shrinkA=2, shrinkB=2) if arrow else None)


# ==========================================================================================
# 01  sessions
# ==========================================================================================

def fig_sessions(d, res, out):
    """When each power cycle began and what the ground station heard of it."""
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    fig.subplots_adjust(left=0.2, right=0.97)
    rows = [("S0", "Pad capture", MUTED), ("F1", "Flight 1", F1C), ("G1", "Flight 1 · after landing", TEAL), ("F2", "Flight 2", F2C)]
    base = pd.Timestamp("2026-09-30 17:45:00")

    def mins(ts):
        return (ts.tz_localize(None) - base).total_seconds() / 60.0
    for i, (nm, lab, c) in enumerate(rows[::-1]):
        g = d[d.name == nm]
        boot = g.host_ist.iloc[0] - pd.Timedelta(seconds=float(g.ti.iloc[0]))
        end = g.host_ist.iloc[-1]
        x0, x1 = mins(boot), mins(end)
        ax.barh(i, x1 - x0, left=x0, height=0.26, color=c, alpha=0.18, zorder=2)
        if nm != "G1":
            ax.barh(i, 5.0, left=x0, height=0.26, color="none", edgecolor=c, hatch="////", lw=0, alpha=0.55, zorder=3)
        xs = (g.host_ist - pd.Timedelta(seconds=0)).apply(mins)
        ax.barh(i, mins(g.host_ist.iloc[-1]) - mins(g.host_ist.iloc[0]) + 0.35, left=mins(g.host_ist.iloc[0]) - 0.1, height=0.5, color=c, zorder=4)
        ax.text(-0.015, i + 0.1, lab, ha="right", va="center", fontsize=8.8, fontweight="bold", color=c, transform=ax.get_yaxis_transform())
        ax.text(-0.015, i - 0.22, f"{len(g)} packets · P-{g.P.min():03d}…P-{g.P.max():03d}", ha="right", va="center", fontsize=6.9, color=MUTED, transform=ax.get_yaxis_transform())
        ax.text(x0, i + 0.3, f"power-on {boot.strftime('%H:%M:%S')}", fontsize=6.6, color=c, ha="left", va="bottom")
    ax.annotate("throw ≈ 18:25:51", xy=(mins(pd.Timestamp("2026-09-30 18:25:51")), 2), xytext=(mins(pd.Timestamp("2026-09-30 18:25:51")) - 12, 2.55),
                fontsize=7, color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=0.8), ha="right")
    ax.set_yticks([]); ax.set_ylim(-0.6, 3.8)
    ax.set_xlim(0, 65)
    ax.set_xticks(range(0, 66, 10))
    ax.set_xticklabels([(base + pd.Timedelta(minutes=m)).strftime("%H:%M") for m in range(0, 66, 10)])
    ax.set_xlabel("clock time at the ground station, IST (UTC + 5:30), 30 September 2026")
    ax.grid(axis="y", visible=False); ax.spines["left"].set_visible(False)
    ax.set_title("Four power cycles, two descents", loc="left", x=-0.2)
    ax.text(0.99, 0.97, "pale bar: vehicle powered  ·  solid: heard by the ground station\nhatched: first five minutes (uplink command window)",
            transform=ax.transAxes, ha="right", va="top", fontsize=6.6, color=MUTED)
    _save(fig, out, "01_session_timeline.png")


# ==========================================================================================
# 02 / 03  the three mandatory graphs
# ==========================================================================================

def _mandatory(d, res, out, nm, color, fname, title, events):
    g = d[d.name == nm].reset_index(drop=True)
    fig, axs = plt.subplots(3, 1, figsize=(7.2, 6.4), sharex=True, gridspec_kw=dict(hspace=0.16))
    t = g.ti.to_numpy()
    ax = axs[0]
    ax.plot(t, g.A, color=color, lw=1.8, marker="o", ms=3.6, label="altitude as transmitted (A-)")
    ax.plot(t, g.h_base, color=NAVY, lw=1.0, ls="--", marker=None, label="hypsometric height from the same pressure")
    ax.set_ylabel("altitude (m)")
    ax.legend(loc="upper right" if nm == "F1" else "upper right")
    ax.set_title(title)
    for ev in events:
        ev(ax)
    _pkt_axis(ax, g)
    ax = axs[1]
    ax.plot(t, g["T"], color=GOLD, lw=1.8, marker="o", ms=3.6)
    lo, hi = g["T"].min(), g["T"].max()
    ax.set_ylim(29.0, 33.5)
    ax.set_ylabel("temperature (°C)")
    ax.text(0.99, 0.12, (f"{lo:.1f} °C throughout" if lo == hi else f"{lo:.1f}–{hi:.1f} °C across the record"), transform=ax.transAxes, ha="right", fontsize=7.5, color=MUTED)
    ax = axs[2]
    ax.plot(t, g.Pr / 100.0, color=TEAL, lw=1.8, marker="o", ms=3.6)
    ax.set_ylabel("pressure (hPa)")
    ax.set_xlabel("mission time (s)")
    for a in axs:
        a.margins(x=0.02)
    _save(fig, out, fname)


def fig_f1_mandatory(d, res, out):
    r = res["F1"]

    def ev(ax):
        ax.axvspan(r["hover"]["t0"], 677.3, color=SKY, alpha=0.18, lw=0)
        ax.text(675.0, 0.06, "held at the terrace edge", transform=ax.get_xaxis_transform(), ha="center", fontsize=7.2, color=MUTED)
        ax.axvline(r["release"]["ti"], color=RED, lw=0.9, ls=":")
        ax.text(r["release"]["ti"] - 0.1, 0.55, "throw", rotation=90, transform=ax.get_xaxis_transform(), ha="right", va="center", fontsize=7.2, color=RED)
        ax.axvline(r["canopy_opening"]["ti"], color=GREEN, lw=0.9, ls=":")
        ax.text(r["canopy_opening"]["ti"] + 0.1, 0.55, "canopy opens", rotation=90, transform=ax.get_xaxis_transform(), ha="left", va="center", fontsize=7.2, color=GREEN)
        ax.text(683.4, 0.40, "steady descent", transform=ax.get_xaxis_transform(), ha="center", fontsize=7.2, color=F1C)
    _mandatory(d, res, out, "F1", F1C, "02_f1_mandatory_graphs.png", "Flight 1 · altitude, temperature and pressure against mission time", [ev])


def fig_f2_mandatory(d, res, out):
    r = res["F2"]

    def ev(ax):
        ax.axvline(r["touchdown"]["ti"], color=GREEN, lw=0.9, ls=":")
        ax.text(r["touchdown"]["ti"] - 0.15, 0.55, "touchdown", rotation=90, transform=ax.get_xaxis_transform(), ha="right", va="center", fontsize=7.2, color=GREEN)
        ax.text(110.5, 0.30, "steady descent under canopy", transform=ax.get_xaxis_transform(), ha="center", fontsize=7.2, color=F2C)
    _mandatory(d, res, out, "F2", F2C, "03_f2_mandatory_graphs.png", "Flight 2 · altitude, temperature and pressure against mission time", [ev])


# ==========================================================================================
# 04 / 05  descent analysis
# ==========================================================================================

def _descent(d, res, out, nm, color, fname, title, t_rel, steady_window, notes):
    g = d[d.name == nm].reset_index(drop=True)
    r = res[nm]
    t = g.ti.to_numpy() - t_rel
    h = g.h_base.to_numpy()
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[1.25, 1], hspace=0.13))
    ax = axs[0]
    ax.plot(t, h, color=color, lw=1.8, marker="o", ms=3.8, zorder=3, label="height (hypsometric, from pressure)")
    s0, s1 = steady_window
    m = (g.ti >= s0) & (g.ti <= s1)
    fit = np.polyfit(g.ti[m], g.h_base[m], 1)
    tt = np.array([s0, s1])
    ax.plot(tt - t_rel, np.polyval(fit, tt), color=NAVY, lw=1.6, ls="--", zorder=4,
            label=f"least-squares fit  ·  {-fit[0]:.2f} m/s")
    ax.set_ylabel("height above baseline (m)")
    ax.legend(loc="upper right" if nm == "F2" else "upper right")
    ax.set_title(title)
    for fn in notes:
        fn(ax, t_rel)
    ax = axs[1]
    from launch_analysis import local_rate
    v = -local_rate(g.ti.to_numpy(), h)
    ax.axhspan(0, 5.0, color=GREEN, alpha=0.06, lw=0)
    ax.axhline(5.0, color=RED, lw=1.0, ls="--")
    ax.text(t.max(), 5.12, "5 m/s rulebook limit", ha="right", va="bottom", fontsize=7.5, color=RED)
    ax.bar(t, v, width=0.22 if nm == "F1" else 0.5, color=color, alpha=0.85, zorder=3)
    ax.axhline(-fit[0], color=NAVY, lw=1.0, ls=":")
    ax.text(t.min() + 0.05, -fit[0] + 0.15, f"steady rate {-fit[0]:.2f} m/s", fontsize=7.5, color=NAVY, va="bottom")
    ax.set_ylabel("descent speed (m/s)")
    ax.set_xlabel("time since the apex of the throw (s)" if nm == "F1" else "time since first packet of the record (s)")
    ax.set_ylim(min(0, v[np.isfinite(v)].min() - 0.3), max(8, np.nanmax(v) + 0.8))
    _save(fig, out, fname)


def fig_f1_descent(d, res, out):
    r = res["F1"]
    t_rel = r["peak"]["ti"]

    def n1(ax, t0):
        ax.axvline(0, color=RED, lw=0.9, ls=":")
        ax.text(0.04, 0.04, "apex of the throw · 30.7 m", transform=ax.get_xaxis_transform(), color=RED, fontsize=7.2, ha="left")
        ax.axvline(r["canopy_opening"]["ti"] - t0, color=GREEN, lw=0.9, ls=":")
        ax.text(r["canopy_opening"]["ti"] - t0 + 0.05, 0.93, "canopy opens", transform=ax.get_xaxis_transform(), color=GREEN, fontsize=7.2, ha="left", va="top")
        ax.axvspan(0, r["canopy_opening"]["ti"] - t0, color=GOLD, alpha=0.15, lw=0)
        ax.text((r["canopy_opening"]["ti"] - t0) / 2, 0.2, "falling,\ncanopy\nloading", transform=ax.get_xaxis_transform(), color="#9A6B00", fontsize=7, ha="center")
    # use samples from the peak on
    d1 = d.copy()
    _descent(d1[(d1.name != "F1") | (d1.ti >= 677.3)], res, out, "F1", F1C, "04_f1_descent.png",
             "Flight 1 · height and descent speed from the apex of the throw", t_rel, (679.111, 684.92), [n1])


def fig_f2_descent(d, res, out):
    r = res["F2"]

    def n2(ax, t0):
        ax.axvline(r["touchdown"]["ti"] - t0, color=GREEN, lw=0.9, ls=":")
        ax.text(r["touchdown"]["ti"] - t0 - 0.2, 0.5, "touchdown", transform=ax.get_xaxis_transform(), color=GREEN, fontsize=7.2, ha="right", rotation=90, va="center")
    _descent(d, res, out, "F2", F2C, "05_f2_descent.png", "Flight 2 · height and descent speed",
             res["F2"]["start"]["ti"], (r["steady"]["t0"], r["steady"]["t1"]), [n2])


# ==========================================================================================
# 06  comparison
# ==========================================================================================

def fig_compare(d, res, out):
    f1 = d[(d.name == "F1") & (d.ti >= 677.3)]
    f2 = d[d.name == "F2"]
    fig = plt.figure(figsize=(7.2, 3.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.65, 1], wspace=0.28)
    ax = fig.add_subplot(gs[0])
    t1 = f1.ti - f1.ti.iloc[0]
    ax.plot(t1, f1.h_base - f1.h_base.iloc[-1], color=F1C, lw=1.9, marker="o", ms=3.4, label="Flight 1 (to last packet)")
    t2 = f2.ti - f2.ti.iloc[0]
    ax.plot(t2, f2.h_base - f2.h_base.iloc[-1], color=F2C, lw=1.9, marker="o", ms=3.4, label="Flight 2")
    # a 5 m/s reference descent from the same height
    h0 = 30.0
    tt = np.linspace(0, h0 / 5.0, 20)
    ax.plot(tt, h0 - 5.0 * tt, color=RED, lw=1.0, ls="--", label="a descent at the 5 m/s limit")
    ax.set_xlabel("time since the first sample shown (s)")
    ax.set_ylabel("height above the last sample (m)")
    ax.set_title("Descent profiles")
    ax.legend(loc="upper right")
    ax = fig.add_subplot(gs[1])
    vals = [res["F1"]["steady_core"]["rate_mps"], res["F2"]["steady"]["rate_mps"]]
    errs = [res["F1"]["steady_core"]["rate_se"], res["F2"]["steady"]["rate_se"]]
    ax.bar([0, 1], vals, color=[F1C, F2C], width=0.55, yerr=errs, error_kw=dict(ecolor=INK, lw=1, capsize=3), zorder=3)
    ax.axhline(5.0, color=RED, lw=1.1, ls="--")
    ax.text(1.45, 5.1, "5 m/s", color=RED, ha="right", va="bottom", fontsize=7.5)
    for i, v in enumerate(vals):
        ax.text(i, v / 2, f"{v:.2f}\nm/s", ha="center", va="center", color="white", fontweight="bold", fontsize=8.5)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Flight 1", "Flight 2"])
    ax.set_ylim(0, 5.8)
    ax.set_ylabel("steady descent rate (m/s)")
    ax.set_title("Steady rate")
    ax.grid(axis="x", visible=False)
    _save(fig, out, "06_flight_comparison.png")


# ==========================================================================================
# 07 / 08  acceleration
# ==========================================================================================

def _accel(d, res, out, nm, color, fname, title, marks):
    g = d[d.name == nm]
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 5.2), sharex=True, gridspec_kw=dict(height_ratios=[1.2, 1], hspace=0.12))
    ax = axs[0]
    ax.plot(g.ti, g.AX, color=RED, lw=1.2, marker="o", ms=2.6, label="AX")
    ax.plot(g.ti, g.AY, color=GREEN, lw=1.2, marker="o", ms=2.6, label="AY")
    ax.plot(g.ti, g.AZ, color=F1C, lw=1.2, marker="o", ms=2.6, label="AZ")
    ax.axhline(0, color="#94A3B8", lw=0.8)
    ax.set_ylabel("acceleration (m/s²)")
    ax.legend(ncol=3, loc="lower left")
    ax.set_title(title)
    ax = axs[1]
    ax.fill_between(g.ti, 0, g.a_mag / G0, color=color, alpha=0.18, lw=0)
    ax.plot(g.ti, g.a_mag / G0, color=color, lw=1.6, marker="o", ms=3)
    ax.axhline(1.0, color=MUTED, lw=0.9, ls="--")
    ax.text(g.ti.min(), 1.04, "1 g", color=MUTED, fontsize=7.2, va="bottom")
    ax.set_ylabel("specific force |a| (g)")
    ax.set_xlabel("mission time (s)")
    for fn in marks:
        fn(axs)
    _save(fig, out, fname)


def fig_f1_accel(d, res, out):
    r = res["F1"]

    def mk(axs):
        ax = axs[1]
        ax.annotate(f"the throw\n{r['release']['a_g']:.1f} g", xy=(r["release"]["ti"], r["release"]["a_g"]),
                    xytext=(r["release"]["ti"] - 2.6, r["release"]["a_g"] - 0.8), fontsize=7.5, color=RED,
                    arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
        ax.annotate(f"canopy opening\n{r['canopy_opening']['a_g']:.1f} g", xy=(r["canopy_opening"]["ti"], r["canopy_opening"]["a_g"]),
                    xytext=(r["canopy_opening"]["ti"] + 1.1, r["canopy_opening"]["a_g"] + 1.6), fontsize=7.5, color=GREEN,
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9))
        ax.text(675.0, 1.55, "held in hand: ≈ 1 g,\nvehicle on its side", ha="center", fontsize=7.2, color=MUTED)
        ax.text(683.0, 3.0, "descent: ≈ 1 g\nwith canopy swing", ha="center", fontsize=7.2, color=F1C)
        axs[0].axvspan(677.9, 678.8, color=GOLD, alpha=0.18, lw=0)
        axs[0].text(678.35, 0.04, "falling", transform=axs[0].get_xaxis_transform(), ha="center", fontsize=7, color="#9A6B00")
    _accel(d, res, out, "F1", F1C, "07_f1_acceleration.png", "Flight 1 · accelerometer, three axes and magnitude", [mk])


def fig_f2_accel(d, res, out):
    r = res["F2"]

    def mk(axs):
        ax = axs[1]
        ax.annotate(f"canopy load\n{r['inflation']['a_g']:.1f} g", xy=(r["inflation"]["ti"], r["inflation"]["a_g"]),
                    xytext=(r["inflation"]["ti"] + 2.0, r["inflation"]["a_g"] + 0.15), fontsize=7.5, color=GREEN,
                    arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9))
        ax.annotate(f"touchdown\n{r['touchdown_load']['a_g']:.1f} g", xy=(119.0, r["touchdown_load"]["a_g"]),
                    xytext=(114.3, 2.1), fontsize=7.5, color=F2C, arrowprops=dict(arrowstyle="->", color=F2C, lw=0.9))
    _accel(d, res, out, "F2", F2C, "08_f2_acceleration.png", "Flight 2 · accelerometer, three axes and magnitude", [mk])


# ==========================================================================================
# 09 / 10  attitude
# ==========================================================================================

def fig_attitude(d, res, out):
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 4.8), sharey="row", gridspec_kw=dict(hspace=0.6, wspace=0.08))
    for j, (nm, c) in enumerate([("F1", F1C), ("F2", F2C)]):
        g = d[d.name == nm]
        if nm == "F1":
            g = g[g.ti >= 677.3]
        ax = axs[0, j]
        ax.plot(g.ti, g.Ro, color=c, lw=1.5, marker="o", ms=3, label="roll")
        ax.plot(g.ti, g.Pi, color=NAVY, lw=1.5, marker="s", ms=3, label="pitch", alpha=0.85)
        ax.axhline(0, color="#94A3B8", lw=0.8)
        ax.axhspan(-45, 45, color=GREEN, alpha=0.05, lw=0)
        ax.set_title(("Flight 1" if nm == "F1" else "Flight 2") + " · roll and pitch")
        ax.set_xlabel("mission time (s)")
        if j == 0:
            ax.set_ylabel("angle (°)")
            ax.legend(loc="lower left", ncol=2)
        ax = axs[1, j]
        ya = np.degrees(np.unwrap(np.radians(g.Ya)))
        ax.plot(g.ti, g.Ya, color=PURPLE, lw=0, marker="o", ms=3.4)
        ax.set_ylim(-190, 190); ax.set_yticks([-180, -90, 0, 90, 180])
        ax.set_title("relative yaw (gyro-integrated, wrapped)")
        ax.set_xlabel("mission time (s)")
        if j == 0:
            ax.set_ylabel("yaw (°)")
    _save(fig, out, "09_attitude_time_series.png")


def fig_stability(d, res, out):
    from launch_analysis import tilt_deg
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.9), gridspec_kw=dict(width_ratios=[1, 1, 1.15], wspace=0.35))
    sets = []
    for nm, c in (("F1", F1C), ("F2", F2C)):
        g = d[d.name == nm]
        if nm == "F1":
            g = g[(g.ti >= 679.0) & (g.ti <= 684.95)]
        else:
            g = g[g.ti <= 118.0]
        sets.append((nm, c, g))
    for ax, (nm, c, g) in zip(axs[:2], sets):
        for rad, lab in ((15, "15°"), (30, "30°"), (45, "45°")):
            ax.add_patch(Circle((0, 0), rad, fill=False, ec="#CBD5E1", lw=0.9, ls="-" if rad == 45 else "--"))
            ax.text(rad * 0.71, rad * 0.71 + 1.0, lab, fontsize=6.5, color=MUTED)
        ax.scatter(g.Ro, g.Pi, c=c, s=26, alpha=0.9, lw=0, zorder=3)
        ax.axhline(0, color="#CBD5E1", lw=0.7); ax.axvline(0, color="#CBD5E1", lw=0.7)
        ax.set_xlim(-55, 55); ax.set_ylim(-55, 55); ax.set_aspect("equal")
        ax.set_xlabel("roll (°)"); ax.set_ylabel("pitch (°)" if nm == "F1" else "")
        ax.set_title("Flight " + nm[1], loc="left")
        ax.grid(False)
    ax = axs[2]
    for nm, c, g in sets:
        x = np.sort(tilt_deg(g))
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", color=c, lw=2, label=f"Flight {nm[1]}")
    ax.axvline(45, color=GREEN, lw=1, ls="--")
    ax.text(44, 0.55, "45°", ha="right", color=GREEN, fontsize=7.2)
    ax.set_xlabel("swing angle from vertical (°)")
    ax.set_ylabel("cumulative share of packets")
    ax.set_title("Swing angle", loc="left")
    ax.legend(loc="upper left")
    ax.set_xlim(0, 50)
    _save(fig, out, "10_stability.png")


# ==========================================================================================
# 11  pressure-altitude law
# ==========================================================================================

def fig_pressure_law(d, res, out):
    from launch_analysis import isa_altitude
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2), gridspec_kw=dict(wspace=0.3))
    ax = axs[0]
    for nm, c in (("F1", F1C), ("F2", F2C)):
        g = d[d.name == nm]
        ax.scatter(g.Pr / 100, g.A, color=c, s=20, alpha=0.9, lw=0, label=f"Flight {nm[1]} (as transmitted)", zorder=3)
        pb = res["baseline"][nm]["p_base_pa"]
        p = np.linspace(g.Pr.min(), g.Pr.max(), 50)
        ax.plot(p / 100, isa_altitude(p) - isa_altitude(pb), color=c, lw=1.1, alpha=0.8)
    ax.set_xlabel("pressure (hPa)")
    ax.set_ylabel("altitude, as transmitted (m)")
    ax.set_title("Pressure to altitude")
    ax.legend(loc="upper right")
    ax.text(0.03, 0.05, "lines: ISA formula the firmware\nuses, with each flight's baseline", transform=ax.transAxes, fontsize=6.8, color=MUTED)
    ax = axs[1]
    for nm, c in (("F1", F1C), ("F2", F2C)):
        g = d[d.name == nm]
        ax.scatter(g.A, g.h_base - g.A, color=c, s=20, alpha=0.9, lw=0, zorder=3)
    ax.axhline(0, color=MUTED, lw=0.9)
    ax.set_xlabel("altitude as transmitted (m)")
    ax.set_ylabel("hypsometric − transmitted (m)")
    ax.set_title("Temperature correction")
    k = np.mean([(d[d.name == n].h_base / d[d.name == n].A.replace(0, np.nan)).median() for n in ("F1",)])
    ax.text(0.04, 0.92, f"31 °C air is thinner than ISA's 15 °C:\nheight per pascal is ≈ {100*(1.0568-1):.1f} % larger", transform=ax.transAxes, fontsize=7, color=MUTED, va="top")
    _save(fig, out, "11_pressure_altitude_law.png")


# ==========================================================================================
# 13  sound
# ==========================================================================================

def fig_sound(d, res, out):
    from launch_analysis import local_rate
    fig = plt.figure(figsize=(7.4, 3.3))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1], wspace=0.28)
    ax = fig.add_subplot(gs[0])
    f1 = d[(d.name == "F1") & d.SN.notna()]
    f2 = d[(d.name == "F2") & d.SN.notna()]
    ax.plot(f1.ti - 677.768, f1.SN, color=F1C, lw=1.6, marker="o", ms=4, label="Flight 1 (t = 0 at the apex of the throw)")
    ax.plot(f2.ti - f2.ti.iloc[0], f2.SN, color=F2C, lw=1.6, marker="o", ms=4, label="Flight 2 (t = 0 at first packet)")
    ax.axvline(0, color=RED, lw=0.8, ls=":")
    ax.annotate("throw", xy=(0, 36.3), xytext=(0.8, 40), fontsize=7.2, color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=0.7))
    ax.set_xlabel("time (s)"); ax.set_ylabel("microphone level (mV peak-to-peak)")
    ax.set_ylim(0, 44)
    ax.set_title("Acoustic level")
    ax.legend(loc="upper right", fontsize=6.8)
    ax = fig.add_subplot(gs[1])
    allv = np.concatenate([f1.SN.to_numpy(), f2.SN.to_numpy()])
    lsb = 3300.0 / 4096.0
    ax.hist(allv, bins=np.arange(0, 40, lsb * 2.5), color=TEAL, alpha=0.85, edgecolor="white")
    ax.set_xlabel("level (mV p-p)"); ax.set_ylabel("rich packets")
    ax.set_title("Distribution")
    ax.text(0.97, 0.9, f"ADC step {lsb:.3f} mV\n(12 bit, 3.3 V)", transform=ax.transAxes, ha="right", va="top", fontsize=7, color=MUTED)
    _save(fig, out, "13_sound.png")


# ==========================================================================================
# 14  link
# ==========================================================================================

def fig_link(d, res, out):
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.4), gridspec_kw=dict(hspace=0.42, wspace=0.28))
    ax = axs[0, 0]
    for nm, c, t0 in (("F1", F1C, 672.929), ("F2", F2C, 102.901), ("G1", TEAL, 0.0)):
        g = d[d.name == nm]
        ax.plot(g.ti - t0, g.rssi, color=c, lw=1.3, marker="o", ms=2.8, label={"F1": "Flight 1", "F2": "Flight 2", "G1": "after landing"}[nm])
    ax.axhline(-123, color=RED, lw=1, ls="--")
    ax.text(16.2, -121.5, "SX127x SF7 sensitivity ≈ −123 dBm", ha="right", va="bottom", fontsize=7, color=RED)
    ax.set_ylim(-126, -74)
    ax.set_xlabel("time into each capture (s)"); ax.set_ylabel("RSSI (dBm)")
    ax.set_title("Received signal strength"); ax.legend(loc="upper right", ncol=3, fontsize=6.6)
    ax = axs[0, 1]
    for nm, c in (("F1", F1C), ("F2", F2C), ("G1", TEAL)):
        g = d[d.name == nm]
        ax.scatter(g.rssi, g.snr, color=c, s=22, alpha=0.85, lw=0)
    x = d.rssi.to_numpy(); y = d.snr.to_numpy()
    k = np.polyfit(x, y, 1)
    xx = np.linspace(x.min(), x.max(), 20)
    ax.plot(xx, np.polyval(k, xx), color=NAVY, lw=1.2, ls="--")
    rr = res["link"]["rssi_snr"]["r"]
    ax.text(0.04, 0.93, f"r = {rr:.2f}  (n = {len(d)})", transform=ax.transAxes, fontsize=7.8, va="top", color=NAVY, fontweight="bold")
    ax.set_xlabel("RSSI (dBm)"); ax.set_ylabel("SNR (dB)")
    ax.set_title("RSSI against SNR")
    ax = axs[1, 0]
    g2 = d[d.name == "F2"]
    ax.scatter(g2.h_base - g2.h_base.min(), g2.rssi, color=F2C, s=28, alpha=0.9, lw=0, zorder=3)
    xx = (g2.h_base - g2.h_base.min()).to_numpy(); yy = g2.rssi.to_numpy()
    k = np.polyfit(xx, yy, 1)
    ax.plot([0, 30], np.polyval(k, [0, 30]), color=NAVY, lw=1.2, ls="--")
    c2 = res["correlations"]["F2"]["h_base~rssi"]
    ax.text(0.04, 0.07, f"r = {c2['pearson']:.2f},  slope {k[0]*10:.1f} dB per 10 m", transform=ax.transAxes, fontsize=7.6, color=NAVY, fontweight="bold")
    ax.set_xlabel("height above landing point (m)"); ax.set_ylabel("RSSI (dBm)")
    ax.set_title("Flight 2 · signal against height")
    ax = axs[1, 1]
    margin = d.rssi - (-123.0)
    ax.hist(margin, bins=np.arange(10, 48, 3), color=TEAL, alpha=0.85, edgecolor="white")
    ax.axvline(margin.min(), color=RED, lw=1, ls="--")
    ax.text(margin.min() + 0.5, ax.get_ylim()[1] * 0.92, f"weakest packet\n+{margin.min():.0f} dB", fontsize=7.2, color=RED, va="top")
    ax.set_xlabel("link margin over receiver sensitivity (dB)"); ax.set_ylabel("packets")
    ax.set_title("Link margin")
    _save(fig, out, "14_radio_link.png")


# ==========================================================================================
# 15  correlation heatmaps
# ==========================================================================================

LABELS = {"h_base": "height", "Pr": "pressure", "T": "temperature", "a_mag": "|a|", "Ro": "|roll|", "Pi": "|pitch|",
          "SN": "sound", "rssi": "RSSI", "snr": "SNR", "v": "vert. speed (+up)"}


def fig_corr(d, res, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.9), gridspec_kw=dict(wspace=0.12))
    cols = ["h_base", "Pr", "a_mag", "Ro", "Pi", "SN", "rssi", "snr", "v"]
    for ax, nm in zip(axs, ("F1", "F2")):
        m = res["correlations"][nm + "_matrix"]
        M = np.array([[np.nan if m[c][r] is None else m[c][r] for c in cols] for r in cols])
        im = ax.imshow(M, cmap=DIV, vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols))); ax.set_yticks(range(len(cols)))
        ax.set_xticklabels([LABELS[c] for c in cols], rotation=45, ha="right", fontsize=7)
        ax.set_yticklabels([LABELS[c] for c in cols] if nm == "F1" else [], fontsize=7)
        for i in range(len(cols)):
            for j in range(len(cols)):
                if not np.isnan(M[i, j]):
                    ax.text(j, i, f"{M[i,j]:.2f}".replace("-0.", "−.").replace("0.", "."), ha="center", va="center", fontsize=6.2,
                            color="white" if abs(M[i, j]) > 0.65 else INK)
        ax.set_title("Flight " + nm[1] + " · descent", loc="left")
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
    cb = fig.colorbar(im, ax=axs, shrink=0.75, pad=0.02, aspect=26)
    cb.set_label("Pearson r", fontsize=7.5); cb.outline.set_visible(False)
    _save(fig, out, "15_correlation_heatmaps.png")


def fig_pairs(d, res, out):
    from launch_analysis import local_rate
    parts = []
    g = d[(d.name == "F1") & (d.ti >= 679.0)].copy(); g["flight"] = "Flight 1"; parts.append(g)
    g = d[(d.name == "F2") & (d.ti <= 118.4)].copy(); g["flight"] = "Flight 2"; parts.append(g)
    X = pd.concat(parts)
    X["speed"] = np.nan
    for nm in ("F1", "F2"):
        sub = d[d.name == nm]
        v = -local_rate(sub.ti.to_numpy(), sub.h_base.to_numpy())
        X.loc[X.index.intersection(sub.index), "speed"] = pd.Series(v, index=sub.index)
    X["height"] = X.h_base - X.groupby("flight").h_base.transform("min")
    X["tilt"] = np.degrees(np.arccos(np.clip(X.AZ / X.a_mag, -1, 1)))
    cols = [("height", "height (m)"), ("speed", "speed (m/s)"), ("tilt", "swing (°)"), ("rssi", "RSSI (dBm)"), ("a_mag", "|a| (m/s²)")]
    n = len(cols)
    fig, axs = plt.subplots(n, n, figsize=(7.4, 7.0), gridspec_kw=dict(hspace=0.12, wspace=0.12))
    for i, (ci, li) in enumerate(cols):
        for j, (cj, lj) in enumerate(cols):
            ax = axs[i, j]
            ax.grid(False)
            for fl, c in (("Flight 1", F1C), ("Flight 2", F2C)):
                s = X[X.flight == fl]
                if i == j:
                    v = s[ci].dropna()
                    ax.hist(v, bins=7, color=c, alpha=0.55, edgecolor="white")
                else:
                    ax.scatter(s[cj], s[ci], color=c, s=11, alpha=0.8, lw=0)
            if i != j:
                s = X[[ci, cj]].dropna()
                r = stats.pearsonr(s[cj], s[ci]).statistic
                ax.text(0.96, 0.95, f"r={r:+.2f}".replace("-", "−"), transform=ax.transAxes, ha="right", va="top", fontsize=6.4, color=MUTED)
            if i == n - 1:
                ax.set_xlabel(lj, fontsize=7.2)
            else:
                ax.set_xticklabels([])
            if j == 0:
                ax.set_ylabel(li, fontsize=7.2)
            else:
                ax.set_yticklabels([])
            ax.tick_params(labelsize=6)
    fig.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=F1C, label="Flight 1"),
                        plt.Line2D([], [], marker="o", ls="", color=F2C, label="Flight 2")], loc="upper right", ncol=2, bbox_to_anchor=(0.9, 0.93))
    _save(fig, out, "16_pair_plot.png")


# ==========================================================================================
# 17  the stationary session as a noise measurement
# ==========================================================================================

def fig_ground(d, res, out):
    g = d[d.name == "G1"]
    r = res["G1"]
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.2), gridspec_kw=dict(hspace=0.5, wspace=0.28))
    ax = axs[0, 0]
    ax.plot(g.ti, g.A, color=F1C, lw=1.6, marker="o", ms=3)
    ax.axvspan(0, r["first_calibrated_ti"] - 0.15, color=GOLD, alpha=0.18, lw=0)
    ax.text(2.7, 8.5, "power-on baseline\n(standard sea level)", ha="center", fontsize=7, color="#9A6B00")
    ax.text(9.4, 3.0, "calibrated: ground = 0 m", ha="center", fontsize=7, color=F1C)
    ax.set_xlabel("mission time (s)"); ax.set_ylabel("altitude (m)")
    ax.set_title("Altitude zeroes itself")
    ax = axs[0, 1]
    cal = g[g.A.abs() < 3]
    ax.hist(cal.Pr - cal.Pr.mean(), bins=np.arange(-3.4, 3.6, 0.6), color=TEAL, alpha=0.85, edgecolor="white", density=True)
    xs = np.linspace(-4, 4, 100)
    ax.plot(xs, stats.norm.pdf(xs, 0, cal.Pr.std()), color=NAVY, lw=1.6)
    ax.set_xlabel("pressure − mean (Pa)"); ax.set_ylabel("density")
    ax.set_title("Barometer noise")
    ax.text(0.97, 0.92, f"σ = {cal.Pr.std():.2f} Pa\n≈ {cal.Pr.std()/12.0:.2f} m", transform=ax.transAxes, ha="right", va="top", fontsize=7.6, color=NAVY, fontweight="bold")
    ax = axs[1, 0]
    ax.plot(g.ti, g.AX, color=RED, lw=1.3, label="AX"); ax.plot(g.ti, g.AY, color=GREEN, lw=1.3, label="AY"); ax.plot(g.ti, g.AZ, color=F1C, lw=1.3, label="AZ")
    ax.plot(g.ti, g.a_mag, color=INK, lw=1.4, ls="--", label="|a|")
    ax.axhline(G0, color=MUTED, lw=0.8, ls=":")
    ax.set_xlabel("mission time (s)"); ax.set_ylabel("m/s²")
    ax.set_title("Resting accelerometer"); ax.legend(ncol=4, loc="center", fontsize=6.6, bbox_to_anchor=(0.5, 0.30))
    ax.set_ylim(-3, 14)
    ax.text(0.5, 0.80, f"|a| = {r['accel_mag_calibrated_mean']:.3f} ± {r['accel_mag_calibrated_sd']:.3f} m/s²", transform=ax.transAxes, ha="center", fontsize=7.4, color=INK)
    ax = axs[1, 1]
    ax.plot(g.ti, g.Ro, color=F1C, lw=1.5, label="roll"); ax.plot(g.ti, g.Pi, color=NAVY, lw=1.5, label="pitch")
    ax.plot(g.ti, g.Ya, color=PURPLE, lw=1.5, label="yaw")
    ax.set_xlabel("mission time (s)"); ax.set_ylabel("angle (°)")
    ax.set_title("Resting attitude"); ax.legend(loc="center right", fontsize=6.6)
    ax.set_ylim(-4, 42)
    ax.text(0.5, 0.97, f"roll {r['roll_mean']:.1f}° ± {r['roll_sd']:.2f}   pitch {r['pitch_mean']:.1f}° ± {r['pitch_sd']:.2f}", transform=ax.transAxes, ha="center", va="top", fontsize=7, color=INK)
    _save(fig, out, "17_ground_session.png")


# ==========================================================================================
# 18  packet stream
# ==========================================================================================

def fig_packets(d, res, out):
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.2), gridspec_kw=dict(hspace=0.5, wspace=0.28))
    ax = axs[0, 0]
    for nm, c, lab in (("F1", F1C, "Flight 1  ·  3.09 Hz"), ("G1", TEAL, "after landing  ·  3.09 Hz"), ("F2", F2C, "Flight 2  ·  1.43 Hz")):
        g = d[d.name == nm]
        ax.plot(g.ti - g.ti.iloc[0], g.P - g.P.iloc[0] + 1, color=c, lw=(4.5 if nm == "F1" else 2), alpha=(0.5 if nm == "F1" else 1), label=lab)
    ax.plot([0, 13], [1, 1 + 13 * 1.0], color=RED, lw=1, ls="--", label="1 Hz rulebook floor")
    ax.set_xlabel("time into capture (s)"); ax.set_ylabel("packets since start of capture")
    ax.set_title("Packet count against time"); ax.legend(loc="upper left", fontsize=6.6)
    ax.set_xlim(0, 17)
    ax = axs[0, 1]
    gaps = []
    for nm in ("F1", "G1"):
        g = d[d.name == nm]
        gaps += list(np.diff(g.ti))
    ax.hist(gaps, bins=np.arange(0.26, 0.42, 0.01), color=F1C, alpha=0.85, edgecolor="white")
    ax.set_xlabel("gap to the next packet (s)"); ax.set_ylabel("packets")
    ax.set_title("Max-rate cadence")
    ax.text(0.97, 0.9, "three slots per 0.97 s:\n0.374 · 0.296 · 0.296 s", transform=ax.transAxes, ha="right", va="top", fontsize=7.2, color=MUTED)
    ax = axs[1, 0]
    g = d[(d.name == "F1") & d.bytes.notna()]
    cols = [GOLD if r else SKY for r in g.rich]
    ax.bar(np.arange(len(g)), g.bytes, color=cols, width=0.8, zorder=3)
    ax.axhline(200, color=RED, lw=1, ls="--")
    ax.text(len(g) - 1, 203, "200 B receiver ceiling", ha="right", va="bottom", fontsize=7, color=RED)
    ax.set_ylim(0, 225)
    ax.set_xlabel("packet index in Flight 1"); ax.set_ylabel("bytes on the air")
    ax.set_title("Packet size, rich · lean · lean")
    ax.grid(axis="x", visible=False)
    ax = axs[1, 1]
    names = [("F1", "Flight 1", F1C), ("G1", "After\nlanding", TEAL), ("F2", "Flight 2", F2C), ("S0", "Pad\ncapture", MUTED)]
    cnt = [int((d.name == n).sum()) for n, _, _ in names]
    ax.bar([x[1] for x in names], cnt, color=[x[2] for x in names], width=0.6, zorder=3)
    for i, v in enumerate(cnt):
        ax.text(i, v + 0.8, str(v), ha="center", fontsize=8, fontweight="bold")
    ax.set_ylim(0, 50); ax.set_ylabel("packets received")
    ax.set_title("Packets received per session"); ax.grid(axis="x", visible=False)
    _save(fig, out, "18_packet_stream.png")


# ==========================================================================================
# 19  GPS
# ==========================================================================================

def fig_gps(d, res, out):
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.5), gridspec_kw=dict(wspace=0.32, width_ratios=[1.05, 1]))
    lat0, lon0 = 21.16, 72.7880
    f1 = d[(d.name == "F1") & d.lat.notna()]
    g1 = d[(d.name == "G1") & d.lat.notna()]

    def enu(g):
        return (g.lon - lon0) * 111_320 * np.cos(np.radians(lat0)), (g.lat - lat0) * 111_320
    ax = axs[0]
    for g, c, lab in ((f1, F1C, "Flight 1"), (g1, TEAL, "after landing")):
        e, n = enu(g)
        ax.plot(e, n, color=c, lw=1.2, alpha=0.5)
        ax.scatter(e, n, color=c, s=30, zorder=3, label=lab, lw=0)
    e, n = enu(f1)
    ax.annotate("", xy=(e.iloc[-1], n.iloc[-1]), xytext=(e.iloc[6], n.iloc[6]), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.4))
    ax.text(3.0, 8.0, "drift under canopy\n9 m in 4.8 s", fontsize=7, color=NAVY, va="center", ha="center")
    ax.set_xlim(-26, 26); ax.set_ylim(-11, 11)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("east of 21.1600° N, 72.7880° E  (m)"); ax.set_ylabel("north (m)")
    ax.set_title("Ground track"); ax.legend(loc="lower left", fontsize=6.8)
    ax = axs[1]
    for g, c, lab in ((f1, F1C, "Flight 1"), (g1, TEAL, "after landing")):
        ax.plot(g.ti - g.ti.iloc[0], g.galt, color=c, lw=1.6, marker="o", ms=3.5, label=lab)
    ax.set_xlabel("time into capture (s)"); ax.set_ylabel("GPS altitude (m above MSL)")
    ax.set_title("GPS altitude")
    ax.set_ylim(35, 60)
    ax.legend(loc="center right", fontsize=6.8)
    _save(fig, out, "19_gps.png")


# ==========================================================================================
# 20  physics
# ==========================================================================================

def fig_physics(d, res, out):
    fig, axs = plt.subplots(1, 3, figsize=(7.6, 2.95), gridspec_kw=dict(wspace=0.42))
    S = res["F1"]["physics"]["canopy_area_m2"]
    ax = axs[0]
    m = np.linspace(0.40, 0.60, 30)
    for nm, c in (("F1", F1C), ("F2", F2C)):
        r = res[nm]["physics"]
        v = r["rate_mps"]; rho = r["rho_kgm3"]
        ax.plot(m * 1000, 2 * m * G0 / (rho * v ** 2), color=c, lw=2, label=f"Flight {nm[1]}  ({v:.2f} m/s)")
    ax.axhline(0.75 * S, color=MUTED, lw=1, ls="--"); ax.text(402, 0.75 * S + 0.04, "model: Cd 0.75 × 6 ft canopy", fontsize=6.4, color=MUTED)
    ax.axvspan(450, 550, color=GOLD, alpha=0.14, lw=0)
    ax.set_xlabel("vehicle mass (g)"); ax.set_ylabel("drag area  Cd·S  (m²)")
    ax.set_title("Drag area"); ax.legend(loc="upper left", fontsize=6.6)
    ax = axs[1]
    for nm, c in (("F1", F1C), ("F2", F2C)):
        r = res[nm]["physics"]
        ax.plot(m * 1000, 2 * m * G0 / (r["rho_kgm3"] * r["rate_mps"] ** 2) / S, color=c, lw=2, label=f"Flight {nm[1]}")
    ax.axhspan(0.75, 0.85, color=GREEN, alpha=0.18, lw=0); ax.text(402, 0.865, "vented / flat circular\n0.75 – 0.85", fontsize=6.2, color="#15803d", va="bottom")
    ax.axvspan(450, 550, color=GOLD, alpha=0.14, lw=0)
    ax.set_xlabel("vehicle mass (g)"); ax.set_ylabel("canopy drag coefficient Cd")
    ax.set_title("Cd of the 6 ft canopy"); ax.legend(loc="lower right", fontsize=6.6)
    ax.set_ylim(0.45, 1.15)
    ax = axs[2]
    tst = np.linspace(5, 60, 100)
    for nm, c in (("F1", F1C), ("F2", F2C)):
        r = res[nm]["physics"]["by_mass"]["500"]
        ax.plot(tst, r["momentum_Ns"] / (tst / 1000), color=c, lw=2, label=f"Flight {nm[1]}")
    ax.axhline(100, color=RED, lw=1, ls="--")
    ax.text(58, 104, "100 N study load", ha="right", va="bottom", fontsize=6.8, color=RED)
    ax.set_xlabel("stopping time at touchdown (ms)"); ax.set_ylabel("mean force (N)")
    ax.set_ylim(0, 140)
    ax.set_title("Touchdown load (500 g)"); ax.legend(loc="upper right", fontsize=6.6)
    _save(fig, out, "20_descent_physics.png")


# ==========================================================================================
# 21  status strip
# ==========================================================================================

def fig_status(d, res, out):
    fig, axs = plt.subplots(3, 1, figsize=(7.4, 3.0), gridspec_kw=dict(hspace=0.9))
    for ax, (nm, lab) in zip(axs, (("F1", "Flight 1"), ("G1", "After landing"), ("F2", "Flight 2"))):
        g = d[(d.name == nm) & d.ST.notna()]
        t0 = g.ti.min()
        names = {"F": "FLIGHT", "R": "READY"}
        colors = {"F": F1C, "R": MUTED}
        for _, r in g.iterrows():
            st = r.ST
            c = colors.get(st[0], MUTED)
            armed = st[1] == "1"; cal = st[2] == "1"
            ax.add_patch(FancyBboxPatch((r.ti - t0 - 0.27, 0.1), 0.54, 0.8, boxstyle="round,pad=0,rounding_size=0.1", fc=c if armed else "white", ec=c, lw=1.2))
            ax.text(r.ti - t0, 0.5, st, ha="center", va="center", fontsize=5.0, color="white" if armed else c, fontweight="bold")
        ax.set_xlim(-0.8, 14 if nm != "F2" else 17); ax.set_ylim(0, 1)
        ax.set_yticks([]); ax.grid(False)
        ax.set_ylabel(lab, rotation=0, ha="right", va="center", fontsize=8, fontweight="bold", color=F1C if nm == "F1" else (TEAL if nm == "G1" else F2C))
        ax.spines["left"].set_visible(False)
        if ax is axs[-1]:
            ax.set_xlabel("time into capture (s)")
        else:
            ax.set_xticklabels([])
    axs[0].set_title("Status field ST- on each rich packet   (filled = armed)")
    _save(fig, out, "21_status_strip.png")


# ==========================================================================================
# 22  3-D acceleration vector
# ==========================================================================================

def fig_accel3d(d, res, out):
    fig = plt.figure(figsize=(7.4, 3.6))
    for k, (nm, c) in enumerate((("F1", F1C), ("F2", F2C))):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        g = d[d.name == nm]
        g = g[(g.ti >= 679.0)] if nm == "F1" else g[g.ti <= 118.0]
        ax.scatter(g.AX, g.AY, g.AZ, c=g.ti - g.ti.min(), cmap="viridis", s=22, depthshade=False)
        ax.plot(g.AX, g.AY, g.AZ, color=c, lw=0.7, alpha=0.5)
        u, v = np.mgrid[0:2 * np.pi:36j, 0:np.pi:18j]
        ax.plot_wireframe(G0 * np.cos(u) * np.sin(v), G0 * np.sin(u) * np.sin(v), G0 * np.cos(v), color="#CBD5E1", lw=0.35, alpha=0.7)
        ax.set_xlabel("AX", fontsize=7, labelpad=-5); ax.set_ylabel("AY", fontsize=7, labelpad=-5); ax.set_zlabel("AZ", fontsize=7, labelpad=-5)
        ax.tick_params(labelsize=6, pad=-3)
        ax.view_init(elev=18, azim=-55)
        ax.set_title("Flight " + nm[1], loc="left", fontsize=9)
        ax.set_xlim(-14, 14); ax.set_ylim(-14, 14); ax.set_zlim(-14, 20)
        ax.set_box_aspect((1, 1, 1.2))
        for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
            pane.pane.set_facecolor((1, 1, 1, 0)); pane.pane.set_edgecolor("#E2E8F0")
    fig.text(0.5, 0.0, "one dot per packet in steady descent; the grey sphere is 1 g (9.81 m/s²); colour is time", ha="center", fontsize=7, color=MUTED)
    _save(fig, out, "22_acceleration_vector_3d.png")


# ==========================================================================================
# 23  margins radar
# ==========================================================================================

def fig_radar(d, res, out):
    """Achieved against required, as a multiple of the requirement. 1.0 is the requirement."""
    r1, r2 = res["F1"], res["F2"]
    items = [
        ("Descent rate\n(headroom: 5 m/s ÷ measured)", 5.0 / r1["steady_core"]["rate_mps"], 5.0 / r2["steady"]["rate_mps"]),
        ("Telemetry rate\n(vehicle cadence ÷ 1 Hz)", 1.0 / res["stream"]["F1"]["median_dt"] * (res["stream"]["F1"]["rate_hz"] * res["stream"]["F1"]["median_dt"]), 1.0 / res["stream"]["F2"]["median_dt"]),
        ("Telemetry after landing\n(seconds heard ÷ 5 s)", res["G1"]["duration_s"] / 5.0, None),
        ("Touchdown load\n(100 N study ÷ 25 ms load)", 100.0 / r1["physics"]["by_mass"]["500"]["force_25ms_N"], 100.0 / r2["physics"]["by_mass"]["500"]["force_25ms_N"]),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    y = np.arange(len(items))[::-1]
    for k, (lab, a, b) in enumerate(items):
        ax.barh(y[k] + 0.17, a, height=0.3, color=F1C, zorder=3)
        ax.text(a + 0.05, y[k] + 0.17, f"{a:.1f}×", va="center", fontsize=7.6, color=F1C, fontweight="bold")
        if b is not None:
            ax.barh(y[k] - 0.17, b, height=0.3, color=F2C, zorder=3)
            ax.text(b + 0.05, y[k] - 0.17, f"{b:.1f}×", va="center", fontsize=7.6, color=F2C, fontweight="bold")
        else:
            ax.text(0.05, y[k] - 0.17, "post-landing packets are in the F1 capture", va="center", fontsize=6.6, color=MUTED)
    ax.axvline(1.0, color=RED, lw=1.2, ls="--")
    ax.text(1.03, -0.62, "requirement = 1.0×", color=RED, fontsize=7.2, va="center")
    ax.set_yticks(y); ax.set_yticklabels([i[0] for i in items], fontsize=7.4)
    ax.set_xlim(0, 3.8); ax.set_ylim(-0.85, len(items) - 0.4)
    ax.set_xlabel("multiple of the requirement")
    ax.grid(axis="y", visible=False)
    ax.set_title("Margin against the flight requirements")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=F1C), plt.Rectangle((0, 0), 1, 1, color=F2C)], labels=["Flight 1", "Flight 2"], loc="lower right")
    _save(fig, out, "23_requirement_margins.png")


# ==========================================================================================
# 26  load distributions
# ==========================================================================================

def fig_load_dist(d, res, out):
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    groups = []
    f1 = d[d.name == "F1"]
    groups.append(("Held in hand\n(F1)", f1[f1.ti < 677.3].a_mag / G0, SKY))
    groups.append(("Ballistic\n(F1)", f1[(f1.ti >= 677.7) & (f1.ti < 678.5)].a_mag / G0, GOLD))
    groups.append(("Steady\ndescent (F1)", f1[(f1.ti >= 679.0) & (f1.ti <= 684.95)].a_mag / G0, F1C))
    f2 = d[d.name == "F2"]
    groups.append(("Steady\ndescent (F2)", f2[f2.ti <= 118.0].a_mag / G0, F2C))
    g1 = d[(d.name == "G1") & (d.A.abs() < 3)]
    groups.append(("At rest\n(after landing)", g1.a_mag / G0, TEAL))
    for i, (lab, v, c) in enumerate(groups):
        bp = ax.boxplot(v, positions=[i], widths=0.5, patch_artist=True, showfliers=False,
                        boxprops=dict(facecolor=c, alpha=0.35, edgecolor=c), medianprops=dict(color=INK, lw=1.4),
                        whiskerprops=dict(color=c), capprops=dict(color=c))
        ax.scatter(np.full(len(v), i) + np.random.default_rng(i).normal(0, 0.06, len(v)), v, color=c, s=14, alpha=0.9, lw=0, zorder=3)
    ax.axhline(1, color=MUTED, lw=0.9, ls="--")
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([g[0] for g in groups], fontsize=7.4)
    ax.set_ylabel("specific force |a| (g)")
    ax.set_title("Load by phase of the mission")
    ax.grid(axis="x", visible=False)
    _save(fig, out, "26_load_by_phase.png")


# ==========================================================================================
# 27  height vs time with every channel ("flight deck")
# ==========================================================================================

def fig_deck(d, res, out):
    g = d[(d.name == "F1")].reset_index(drop=True)
    fig, axs = plt.subplots(5, 1, figsize=(7.4, 7.4), sharex=True, gridspec_kw=dict(hspace=0.12, height_ratios=[1.3, 1, 1, 1, 0.8]))
    t = g.ti
    axs[0].plot(t, g.h_base, color=F1C, lw=1.9, marker="o", ms=3); axs[0].set_ylabel("height (m)")
    axs[0].set_title("Flight 1 · every channel on one clock")
    axs[1].plot(t, g.a_mag / G0, color=PURPLE, lw=1.6, marker="o", ms=2.6); axs[1].set_ylabel("|a| (g)")
    axs[2].plot(t, g.Ro, color=F1C, lw=1.4, label="roll"); axs[2].plot(t, g.Pi, color=NAVY, lw=1.4, label="pitch"); axs[2].set_ylabel("angle (°)"); axs[2].legend(ncol=2, loc="lower right", fontsize=6.6)
    axs[3].plot(t, g.rssi, color=TEAL, lw=1.6, marker="o", ms=2.6); axs[3].set_ylabel("RSSI (dBm)")
    s = g[g.SN.notna()]
    axs[4].bar(s.ti, s.SN, width=0.18, color=GOLD, zorder=3); axs[4].set_ylabel("sound (mV)")
    axs[4].set_xlabel("mission time (s)")
    for ax in axs:
        ax.axvline(677.472, color=RED, lw=0.9, ls=":")
        ax.axvline(678.735, color=GREEN, lw=0.9, ls=":")
    axs[0].text(677.42, 0.55, "throw", rotation=90, transform=axs[0].get_xaxis_transform(), ha="right", va="center", fontsize=7, color=RED)
    axs[0].text(678.8, 0.55, "canopy", rotation=90, transform=axs[0].get_xaxis_transform(), ha="left", va="center", fontsize=7, color=GREEN)
    _save(fig, out, "27_flight1_all_channels.png")


# ==========================================================================================
def make_all(d, res, out: Path):
    for fn in (fig_sessions, fig_f1_mandatory, fig_f2_mandatory, fig_f1_descent, fig_f2_descent, fig_compare,
               fig_f1_accel, fig_f2_accel, fig_attitude, fig_stability, fig_pressure_law, fig_sound, fig_link,
               fig_corr, fig_pairs, fig_ground, fig_packets, fig_gps, fig_physics, fig_status, fig_accel3d,
               fig_radar, fig_load_dist, fig_deck):
        print("  ", fn.__name__)
        fn(d, res, out)
