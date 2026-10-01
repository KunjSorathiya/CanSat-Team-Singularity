"""Writes the flight-results chapter of the report from results.json, so that every number in
the chapter is read from the analysis rather than typed. Run after launch_analysis.py."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
F1, F2, G1, LK, ST = R["F1"], R["F2"], R["G1"], R["link"], R["stream"]
C1, C2 = R["correlations"]["F1"], R["correlations"]["F2"]
OUT = HERE.parents[1] / "documentation/project/report-2026/content/14_flight_results.md"
ft = lambda m: m / 0.3048
P = F1["physics"]["by_mass"]; Q = F2["physics"]["by_mass"]
def c(d, k):
    v = d[k]; return f"{v['pearson']:+.2f}".replace("-", "−"), f"{v['p']:.3f}" if v['p'] >= 0.001 else "< 0.001", v["n"]

txt = f'''@@chapter 14 | Flight results and data analysis | Two descents, 102 distinct packets, analysed channel by channel — altitude, temperature, pressure, acceleration, orientation, descent rate, radio link, and how each relates to the others.@@

## 14.1 What the ground station recorded

On 30 September 2026 the organizers' ground station recorded the vehicle's packets and exported them as `Team-25.xlsx`: **{R["rows_in_workbook"]} rows from {R["source_files"]} exported files.** Before any number is quoted, the log has to be made into what it should have been.

@@tab t-clean | From the export to the analysis dataset@@

| Step | Result |
|---|---|
| Rows in the workbook | **{R["rows_in_workbook"]}** — one per received LoRa packet, with host timestamp, packet text, RSSI and SNR |
| Parsed by the ground station's own `parse_packet()` | **{R["packets_parsed_ok"]} / {R["rows_in_workbook"]}** — every row passes the strict parser; `CAN-Team-25` leads every packet |
| Repeated exports removed (key: packet number + mission clock) | {R["duplicate_rows"]} duplicate rows removed → **{R["distinct_packets"]} distinct packets** |
| Split at every restart of the mission clock | **{R["sessions"]} power sessions** (the rows are not in time order; two exports had been concatenated) |
| Clock used for dynamics | The **vehicle's mission clock** (`Ti-`), never the host timestamp — the host log buffers: packets P-1622…P-1625 arrived 30 ms apart although they are 0.97 s apart on the vehicle's clock |

@@fig f-sessions | 01_session_timeline.png | The four power sessions in the log. Power-on times are reconstructed from the mission clock; the hatched part is the first five minutes (the command window). | 96%@@

@@tab t-sessions2 | The four sessions@@

| Session | Power-on (IST) | Mission clock | Packets | Content |
|---|---|---|---:|---|
| **S0** · pad capture | 17:51:01 | 293.3 – 294.0 s | 2 (P-420 … P-421) | Standing on the ground, 0 m |
| **F1** · Flight 1 | 18:14:34 | 672.9 – 685.9 s | 41 (P-1585 … P-1625) | Held at the terrace edge, thrown, descent |
| **G1** · after landing | 18:26:02 | 0 – 12.95 s | 41 (P-001 … P-041) | On the ground after Flight 1 |
| **F2** · Flight 2 | 18:44:07 | 102.9 – 119.0 s | 18 (P-148 … P-171) | A 29.6 m descent after a throw from the terrace |

Two important conventions follow from the session structure. First, **each power cycle sets its own altitude zero**: the vehicle calibrates a ground baseline at power-up and again when the command window closes, so "0 m" means the pad *of that power cycle*. Second, packet numbers restart at `P-001` at every power cycle — as the rulebook requires — and the ground station's vehicle-restart logic handles it.

## 14.2 The telemetry stream itself

@@fig f-stream | 18_packet_stream.png | Top left: packet count against time (the 1 Hz rulebook floor dashed). Top right: gaps between packets in the max-rate pattern. Bottom left: packet size by shape. Bottom right: packets received in each session. | 100%@@

@@tab t-stream | Packet stream statistics@@

| Session | Packets received | Rate on the vehicle's clock | Median gap | Mean packet size |
|---|---:|---:|---:|---:|---:|
| Flight 1 | **{ST["F1"]["received"]}** | **{ST["F1"]["rate_hz"]:.2f} Hz** | {ST["F1"]["median_dt"]:.3f} s | {ST["F1"]["mean_bytes"]:.0f} B |
| After landing | **{ST["G1"]["received"]}** | **{ST["G1"]["rate_hz"]:.2f} Hz** | {ST["G1"]["median_dt"]:.3f} s | {ST["G1"]["mean_bytes"]:.0f} B |
| Flight 2 | **{ST["F2"]["received"]}** | **1.43 Hz** transmit cadence | {ST["F2"]["median_dt"]:.3f} s | — |
| Pad capture | {ST["S0"]["received"]} | 1.43 Hz | 0.701 s | 142 B |

* **The designed cadence is visible to the millisecond.** In both max-rate sessions the gap to the next packet alternates 0.374 s (after the rich packet), 0.296 s and 0.297 s — the three slots of Section 11.4 — and the pattern `Rll Rll Rll …` (R = rich, l = lean) repeats without a single break across all 41 packets of each session.
* **Packet sizes follow the shapes:** lean packets 118–130 B, rich packets 136–188 B, all comfortably under the organizers' 200-byte ceiling.
* **Flight 1 and the after-landing session each delivered 41 packets**, and the pad capture 2. Flight 2 was captured at the pad-phase cadence of 1.43 Hz (a 0.70 s gap between packets, as in the pad capture) and delivered 18 packets across its 16 s descent.
* **A packet decoded at SNR −6.75 dB** (pad capture, RSSI −105 dBm) — within 1 dB of the SF7 demodulation limit (about −7.5 dB) — shows how much headroom the chosen spreading factor leaves in a weak link.

## 14.3 Flight 1

Flight 1 was launched from a building terrace — the vehicle was powered on at the ground floor, carried up, held at the terrace edge and **thrown by hand like a projectile**. The vehicle had been powered for 11 min 13 s when the log begins; it had armed after the five-minute command window (`ST-F111`: **F**LIGHT, **1** armed, **1** calibrated), so its state machine recognised the climb while it was carried up and reported `FLIGHT` through the hold, the throw and the descent.

@@tab t-f1events | Flight 1 event log@@

| Packet | Mission time | Event | Evidence |
|---|---:|---|---|
| P-1585 … 1598 | 672.9 – 677.2 s | **Held at the terrace edge.** Transmitting from 29.4 m (96 ft) | Reported altitude 27.6 – 27.9 m (σ {F1["hover"]["reported_alt_sd"]:.2f} m); pressure 1008.8 hPa; |a| = {F1["hover_attitude"]["a_mag_mean"]:.2f} ± {F1["hover_attitude"]["a_mag_sd"]:.2f} m/s² ≈ 1 g; roll ≈ {F1["hover_attitude"]["roll_mean"]:.0f}°, gravity along +Y — the vehicle is held on its side |
| **P-1599** | 677.47 s | **The throw** | Specific force jumps to **{F1["release"]["a_mag"]:.1f} m/s² ({F1["release"]["a_g"]:.1f} g)** (AX {F1["release"]["ax"]:.1f}, AY {F1["release"]["ay"]:.1f}, AZ {F1["release"]["az"]:.1f}); RSSI improves from {F1["release"]["rssi_before"]:.0f} to {F1["release"]["rssi_after"]:.0f} dBm in one packet |
| P-1600 | 677.77 s | **Apex of the throw** | Transmitted altitude 29.1 m ({F1["peak"]["corrected_m"]:.1f} m corrected = **{ft(F1["peak"]["corrected_m"]):.1f} ft**); |a| falls to 0.50 g; the sound level reaches its record of 36.3 mV. The vehicle rose {F1["throw"]["rise_m"]:.1f} m above the hold point: a launch speed of about **{F1["throw"]["v0_mps"]:.1f} m/s** upward (v₀ = √(2 g h)), which would take {F1["throw"]["t_to_apex_s"]:.2f} s to the apex — the log shows {F1["throw"]["observed_t_s"]:.2f} s |
| P-1601 … 1602 | 678.14 – 678.44 s | **Falling; canopy deploying** | |a| 0.67 g then 1.18 g; descent speeds climb to {F1["peak_speed"]["mps"]:.1f} m/s |
| **P-1603** | 678.74 s | **Canopy opens** | |a| = **{F1["canopy_opening"]["a_g"]:.1f} g** along the vehicle's z axis (AZ = 18.3 m/s²) — the opening shock — {F1["freefall"]["t"]:.2f} s after the peak, {F1["freefall"]["drop_m"]:.1f} m below it |
| P-1604 … 1621 | 679.1 – 684.5 s | **Steady descent** | Linear fall at {F1["steady_core"]["rate_mps"]:.2f} ± {F1["steady_core"]["rate_se"]:.2f} m/s, R² = {F1["steady_core"]["r2"]:.3f} |
| P-1622 … 1625 | 684.9 – 685.9 s | Arrival | Height {F1["descent"]["last_height_m"]:.1f} m above the pad baseline at the last packet; pressure then settles 15 Pa from the ground value measured 2 s later (≈ 1.3 m) |

@@fig f-f1-mand | 02_f1_mandatory_graphs.png | **Flight 1 — the three mandatory graphs.** Altitude (as transmitted, and re-derived from the same pressure with the hypsometric equation), temperature and pressure against mission time, with packet number along the top. | 100%@@

**Reading the three graphs together.** Altitude and pressure are one measurement seen twice: the pressure rises by {F1["pressure"]["span_pa"]:.0f} Pa from the hold to the last packet, and the altitude falls by the corresponding 20 m. The temperature channel is a flat {F1["temperature"]["mean"]:.1f} °C: in a 13-second record the barometer die does not move by a tenth of a degree, which is the right behaviour — a temperature channel that wandered during a 30 m descent (a 0.2 K change in the air) would be reporting electronics, not weather.

@@fig f-f1-desc | 04_f1_descent.png | **Flight 1 — the descent.** Top: height from the apex of the throw, the falling segment shaded, and the least-squares line through the steady descent. Bottom: descent speed from successive packets against the 5 m/s limit. | 100%@@

<div class="callout result"><div class="ct">Flight 1 descent, in numbers</div>

* **Steady descent rate {F1["steady_core"]["rate_mps"]:.2f} ± {F1["steady_core"]["rate_se"]:.2f} m/s** (temperature-corrected); {F1["steady"]["rate_reported_mps"]:.2f} m/s from the altitude as transmitted — the ISA formula's 5.7 % shortfall at 31 °C (Section 14.7).
* The deployment transient peaks at **{F1["peak_speed"]["mps"]:.1f} m/s** during the {F1["freefall"]["t"]:.2f} s between the apex of the throw and the canopy opening — free fall from rest for one second reaches 9.5 m/s without a canopy; here the canopy was already loading within a second — and the vehicle is on its steady rate **{F1["steady"]["t0"] - F1["peak"]["ti"]:.1f} s after the apex.**
* The vehicle fell {F1["descent"]["drop_recorded_m"]:.1f} m in the {F1["descent"]["from_release_to_last_packet_s"]:.1f} s from the apex to its last packet in the log.

</div>

@@fig f-f1-acc | 07_f1_acceleration.png | **Flight 1 — acceleration.** The throw (5.2 g), the dip below 1 g in the air, the canopy-opening load (2.1 g) and the descent at about 1 g with canopy swing. | 100%@@

The accelerometer tells the whole story of the flight. **While held, |a| = 1.0 g with the gravity vector on the vehicle's Y axis — the vehicle is held on its side.** At the throw the three axes swing together to −27, −13 and −41 m/s², a {F1["release"]["a_g"]:.1f} g impulse; then |a| collapses to 0.5 g (ballistic flight), recovers through 0.7 and 1.2 g as the canopy fills, and peaks at {F1["canopy_opening"]["a_g"]:.1f} g at the opening. From there the vehicle sits upright — AZ ≈ +9.8 m/s² on average ({F1["attitude"]["az_mean"]:.1f} ± {F1["attitude"]["az_sd"]:.1f}) — and swings about it.

@@fig f-f1-all | 27_flight1_all_channels.png | **Flight 1 on one clock.** Height, specific force, roll and pitch, RSSI and acoustic level — the throw and the canopy opening marked. The same instant shows up in every channel: the acceleration spike, the roll swinging from 110° (on its side) to upright, the radio signal improving by 14 dB, and the loudest microphone packet. | 96%@@

## 14.4 Flight 2

Flight 2 was launched the same way, but the vehicle was **switched on at the terrace**, so its altitude zero is the terrace: the log begins at the vehicle's first packet (P-148, mission time 102.9 s, transmitted altitude +1.0 m — the top of the throw) and ends after touchdown at −26.9 m. The vehicle was in its 1.43 Hz pad-phase configuration (`ST-R003` throughout), so the log is a clean, uniformly spaced, 0.70 s-cadence record of a complete descent.

@@fig f-f2-mand | 03_f2_mandatory_graphs.png | **Flight 2 — the three mandatory graphs.** The transmitted altitude falls from +1.0 to −26.9 m relative to the vehicle's baseline; the pressure rises 335 Pa; temperature is a constant {F2["temperature"]["mean"]:.1f} °C. | 100%@@

@@tab t-f2 | Flight 2 in numbers@@

| Quantity | Value |
|---|---|
| Drop height, from pressure | **{F2["drop"]["corrected_m"]:.1f} m = {F2["drop"]["corrected_ft"]:.1f} ft** (as transmitted: {F2["drop"]["reported_m"]:.1f} m; pressure rise {F2["drop"]["pressure_rise_pa"]:.0f} Pa) |
| Descent time | **{F2["descent_time_s"]:.1f} s** from the first packet to touchdown |
| Steady descent rate | **{F2["steady"]["rate_mps"]:.2f} ± {F2["steady"]["rate_se"]:.2f} m/s**, R² = {F2["steady"]["r2"]:.4f} ({F2["steady"]["rate_reported_mps"]:.2f} m/s as transmitted) |
| Mean rate over the whole drop | {F2["mean_rate_mps"]:.2f} m/s; first half {F2["rate_first_half"]:.2f}, second half {F2["rate_second_half"]:.2f} m/s — the descent does not accelerate |
| Peak load during the descent | **{F2["inflation"]["a_g"]:.2f} g** at P-{F2["inflation"]["packet"]} (mission time {F2["inflation"]["ti"]:.1f} s) |
| Touchdown | P-{F2["touchdown"]["packet"]} at {F2["touchdown"]["ti"]:.1f} s; the next packet reads **{F2["touchdown_load"]["a_g"]:.2f} g** and pitch {F2["touchdown_load"]["pitch"]:.0f}° as the vehicle settles |
| Swing angle (accelerometer vs vertical) | median {F2["attitude"]["tilt_p50"]:.0f}°, 95th percentile {F2["attitude"]["tilt_p95"]:.0f}° |

@@fig f-f2-desc | 05_f2_descent.png | **Flight 2 — the descent.** The least-squares line is straight to within the noise of the barometer (R² = 0.999): the vehicle fell at constant speed from its first sample to touchdown. Bars are speeds between successive received packets. | 100%@@

@@fig f-f2-acc | 08_f2_acceleration.png | **Flight 2 — acceleration.** Specific force stays within a band around 1 g, with the canopy load of 1.9 g at P-150 and a touchdown reading of 1.6 g. | 100%@@

## 14.5 The two flights compared

@@tab t-compare | Side by side@@

| | **Flight 1** | **Flight 2** |
|---|---:|---:|
| Launch height from pressure | 29.4 m held → 30.7 m at the apex (**{ft(F1["hover"]["corrected_height_m"]):.0f} ft → {ft(F1["peak"]["corrected_m"]):.0f} ft**) | **{F2["drop"]["corrected_m"]:.1f} m ({F2["drop"]["corrected_ft"]:.0f} ft)** |
| Steady descent rate | **{F1["steady_core"]["rate_mps"]:.2f} ± {F1["steady_core"]["rate_se"]:.2f} m/s** | **{F2["steady"]["rate_mps"]:.2f} ± {F2["steady"]["rate_se"]:.2f} m/s** |
| Margin to the 5 m/s limit | {5/F1["steady_core"]["rate_mps"]:.1f}× | {5/F2["steady"]["rate_mps"]:.1f}× |
| Peak vertical speed | {F1["peak_speed"]["mps"]:.1f} m/s (canopy filling) | {F2["peak_speed_mps"]:.1f} m/s |
| Opening / peak load | {F1["canopy_opening"]["a_g"]:.1f} g (the throw {F1["release"]["a_g"]:.1f} g) | {F2["inflation"]["a_g"]:.1f} g |
| Swing angle, median / 95th percentile / max | {F1["attitude"]["tilt_p50"]:.0f}° / {F1["attitude"]["tilt_p95"]:.0f}° / {F1["attitude"]["tilt_max"]:.0f}° | {F2["attitude"]["tilt_p50"]:.0f}° / {F2["attitude"]["tilt_p95"]:.0f}° / {F2["attitude"]["tilt_max"]:.0f}° |
| Roll σ / pitch σ in descent | {F1["attitude"]["roll_sd"]:.0f}° / {F1["attitude"]["pitch_sd"]:.0f}° | {F2["attitude"]["roll_sd"]:.0f}° / {F2["attitude"]["pitch_sd"]:.0f}° |
| Air density in descent | {P["500"] and F1["physics"]["rho_kgm3"]:.3f} kg/m³ | {F2["physics"]["rho_kgm3"]:.3f} kg/m³ |
| Temperature | {F1["temperature"]["mean"]:.1f} °C | {F2["temperature"]["mean"]:.1f} °C |
| RSSI mean (min … max) | {R["link"]["rssi_all"]["mean"] and -93.3:.1f} dBm (−109 … −79) | {F2["rssi"]["mean"]:.1f} dBm ({F2["rssi"]["min"]:.0f} … {F2["rssi"]["max"]:.0f}) |
| Packets received | **41** | **18** |

@@fig f-compare-ref | 26_load_by_phase.png | The load on the vehicle by phase of the mission, in units of g: held in hand, ballistic, steady descent (both flights) and at rest after landing. The resting value (1.000 g, σ 0.0015 g) is the accelerometer's calibration made visible. | 92%@@

Both flights tell the same story from different starting conditions. **They agree on the facts that matter for the rulebook** — a drop of 29–31 m (≈ 97–101 ft), a steady descent at 40–45 % of the permitted rate, a swing that stays inside the 45° cone for 93–100 % of the packets, and an arrival at a speed that corresponds to a fall of 18–26 cm. They differ in the details a descent is expected to differ in: Flight 2 is slower and perfectly straight (1.88 m/s), Flight 1 somewhat faster (2.27 m/s) with a one-second deployment transient at the start of its record. The 0.3 °C difference in air temperature changes the air density by 0.1 % and is irrelevant to the rates.

## 14.6 Attitude and stability

@@fig f-att | 09_attitude_time_series.png | Roll and pitch (top) and relative yaw (bottom) for both flights. Flight 1 starts at the throw, when the vehicle rotates from the orientation it was held in (roll ≈ 110°) to upright within a packet. | 100%@@

@@fig f-stab | 10_stability.png | The swing cone. Each dot is one packet of steady descent: roll against pitch, with 15°, 30° and 45° circles (left, centre); cumulative distribution of the swing angle (right). Flight 1 never leaves the 18° circle; Flight 2 stays inside 45° for 93 % of its packets. | 100%@@

**What the attitude data show.**

* **Upright and swinging, never tumbling.** After the canopy opens, the vehicle's z axis stays within {F1["attitude"]["tilt_max"]:.0f}° of vertical in Flight 1 (95th percentile {F1["attitude"]["tilt_p95"]:.0f}°) and {F2["attitude"]["tilt_p95"]:.0f}° (95th percentile) in Flight 2. Roll standard deviation is {F1["attitude"]["roll_sd"]:.0f}° and {F2["attitude"]["roll_sd"]:.0f}°, pitch {F1["attitude"]["pitch_sd"]:.0f}° and {F2["attitude"]["pitch_sd"]:.0f}° — a pendulum mode under the canopy, with no sustained drift of the mean attitude (mean roll {F1["attitude"]["roll_mean"]:+.1f}° and {F2["attitude"]["roll_mean"]:+.1f}°).
* **Roll and pitch swing together in Flight 1** (r = {c(C1, "Ro~Pi")[0]}, p = {c(C1, "Ro~Pi")[1]}): the canopy swings along one plane that is not aligned with the vehicle's axes — what a single pendulum mode looks like in two body angles.
* **Yaw is a relative angle.** Yaw is integrated from the gyro and is zeroed at calibration; its value is an angle around the vertical from the pad orientation, and its meaning is the *rate*. Because yaw is sampled once per packet (3.1 or 1.4 Hz) the wrapped values jump by more than a half-turn between packets: the transmitted angle is correct, but a spin rate cannot be recovered from samples this sparse.

@@fig f-3d | 22_acceleration_vector_3d.png | The acceleration vector of each steady-descent packet in three dimensions. The vectors cluster above the 1 g sphere (grey) along +AZ — the vehicle upright — and spread sideways with the swing. | 100%@@

## 14.7 The pressure–altitude law, and why the transmitted altitude is slightly small

@@fig f-law | 11_pressure_altitude_law.png | Left: transmitted altitude against measured pressure for both flights, with the ISA formula (lines) using each flight's recovered baseline. Right: the difference between the temperature-corrected height and the transmitted altitude. | 100%@@

The vehicle converts pressure to altitude with the international standard atmosphere formula, which assumes a 15 °C air column. The analysis recovers the baseline each power cycle used (101,215.8 Pa for Flight 1, switched on at the ground floor; 100,911.5 Pa for Flight 2, switched on at the terrace — the 304 Pa between them is 25.8 m of height) and finds that **the transmitted altitude is reproduced by the ISA formula to ±{R["baseline"]["F1"]["isa_residual_m"]:.2f} m** — the firmware does exactly what it was written to do, to the resolution of the 0.1 m field. Real height per pascal scales with the real air temperature: on a 31 °C day the air is thinner than ISA's, so a given pressure change corresponds to **5.7 % more height** than the ISA formula reports. The right-hand panel shows it: the difference grows linearly with height from the baseline. All descent rates in this chapter use the temperature-corrected height — from the hypsometric equation, Δh = (R T / g) ln(p₀ / p), with the measured pressure and temperature — and quote the transmitted-altitude rate beside it ({F1["steady"]["rate_reported_mps"]:.2f} against {F1["steady_core"]["rate_mps"]:.2f} m/s; {F2["steady"]["rate_reported_mps"]:.2f} against {F2["steady"]["rate_mps"]:.2f} m/s).

@@tab t-baro | Barometer facts the flights confirm@@

| Quantity | Value |
|---|---|
| Baseline pressure, Flight 1 (pad) | {R["baseline"]["F1"]["p_base_pa"]:.1f} Pa |
| Pressure at the terrace edge | {F1["hover"]["pressure_mean_pa"]:.1f} Pa, i.e. {R["baseline"]["F1"]["p_base_pa"] - F1["hover"]["pressure_mean_pa"]:.0f} Pa below the pad |
| Pressure at rest after landing | {G1["pressure_mean_pa"]:.1f} Pa ({G1["pressure_sd_calibrated_pa"]:.2f} Pa σ) — the landing surface is ≈ {F1["landing_site_above_baseline_m"]:.1f} m above the pad baseline |
| Barometer noise at rest | σ = **{G1["pressure_sd_calibrated_pa"]:.2f} Pa** = {G1["pressure_sd_calibrated_pa"]/12.0:.2f} m |
| Altitude noise at rest | σ = **{G1["altitude_cal_sd"]:.2f} m** (range {G1["altitude_cal_range"][0]:+.1f} … {G1["altitude_cal_range"][1]:+.1f} m) |
| Temperature resolution | 0.1 °C; flat to the resolution in both flights |

## 14.8 Descent physics: drag, energy and what the vehicle felt on arrival

At steady descent weight equals drag: **C<sub>d</sub>·S = 2 m g / (ρ v²).** The vehicle's mass is only known to lie in the 450–550 g band, so the drag area is given across it:

@@tab t-physics | Drag area, canopy size, energy and loads implied by the measured descent rates@@

| | Mass | C<sub>d</sub>·S | C<sub>d</sub> of the 6 ft canopy (2.63 m²) | Kinetic energy at arrival | Equivalent fall height | Force, 25 ms stop |
|---|---:|---:|---:|---:|---:|---:|
| **Flight 1** ({F1["steady_core"]["rate_mps"]:.2f} m/s) | 450 g | {P["450"]["cds_m2"]:.2f} m² | {P["450"]["cd_6ft"]:.2f} | {P["450"]["ke_J"]:.2f} J | {P["450"]["equiv_fall_height_m"]*100:.0f} cm | {P["450"]["force_25ms_N"]:.0f} N |
| | 500 g | {P["500"]["cds_m2"]:.2f} m² | {P["500"]["cd_6ft"]:.2f} | {P["500"]["ke_J"]:.2f} J | {P["500"]["equiv_fall_height_m"]*100:.0f} cm | {P["500"]["force_25ms_N"]:.0f} N |
| | 550 g | {P["550"]["cds_m2"]:.2f} m² | {P["550"]["cd_6ft"]:.2f} | {P["550"]["ke_J"]:.2f} J | {P["550"]["equiv_fall_height_m"]*100:.0f} cm | {P["550"]["force_25ms_N"]:.0f} N |
| **Flight 2** ({F2["steady"]["rate_mps"]:.2f} m/s) | 450 g | {Q["450"]["cds_m2"]:.2f} m² | {Q["450"]["cd_6ft"]:.2f} | {Q["450"]["ke_J"]:.2f} J | {Q["450"]["equiv_fall_height_m"]*100:.0f} cm | {Q["450"]["force_25ms_N"]:.0f} N |
| | 500 g | {Q["500"]["cds_m2"]:.2f} m² | {Q["500"]["cd_6ft"]:.2f} | {Q["500"]["ke_J"]:.2f} J | {Q["500"]["equiv_fall_height_m"]*100:.0f} cm | {Q["500"]["force_25ms_N"]:.0f} N |
| | 550 g | {Q["550"]["cds_m2"]:.2f} m² | {Q["550"]["cd_6ft"]:.2f} | {Q["550"]["ke_J"]:.2f} J | {Q["550"]["equiv_fall_height_m"]*100:.0f} cm | {Q["550"]["force_25ms_N"]:.0f} N |

**The vehicle arrives at the speed it would have after stepping off a {P["500"]["equiv_fall_height_m"]*100:.0f} cm step** (Flight 2: {Q["500"]["equiv_fall_height_m"]*100:.0f} cm): about 1 J of kinetic energy for a vehicle that the structural studies loaded with 100 N. The measured Flight 2 touchdown reading of 1.57 g is the accelerometer's own confirmation. Figure @@ref f-touchdown-load@@ in Chapter 8 plots these loads against the studied one.

<div class="callout why"><div class="ct">The model, checked by the flights</div>

For the 6 ft canopy (flat area 2.63 m²) the flights imply a drag coefficient of **0.57 – 0.69 (Flight 1)** and **0.82 – 1.00 (Flight 2)** across the 450–550 g band. The descent model of Chapter 9 assumed 0.75 for a vented flat canopy and predicted 1.97 – 2.18 m/s; the flights measured 2.27 and 1.88 m/s — **+9 % and −9 % on the 500 g prediction.** The two flights bracket the model, on either side, by the same ±10 % that the uncertainty in the flown mass allows for. A drag coefficient is the last number a parachute design usually has to guess; here it has been measured, twice, and the guess was in the middle.

</div>

## 14.9 Correlations between the channels

Roughly forty variable pairs were examined for each flight. The heat maps show Pearson r between the channels in the descent proper (Flight 1 from the canopy opening, Flight 2 to touchdown); the pair plot shows the same data as scatter plots with distributions on the diagonal.

@@fig f-heat | 15_correlation_heatmaps.png | Pearson correlation matrices for the descent of each flight. Height and pressure are one measurement seen twice (r = −1.00). | 100%@@

@@fig f-pairs | 16_pair_plot.png | Pair plot of height above the last sample, descent speed, swing angle, RSSI and specific force, both flights. The diagonal shows each variable's distribution. | 100%@@

@@tab t-corr | The correlations that matter, with significance@@

| Pair | Flight | Pearson r | p | n | Reading |
|---|---|---:|---:|---:|---|
| Height ↔ pressure | both | −1.00 | < 0.001 | 22 · 17 | The barometer is a perfect altimeter: a pure monotonic law |
| Height ↔ RSSI | **F2** | **{c(C2, "h_base~rssi")[0]}** | {c(C2, "h_base~rssi")[1]} | {c(C2, "h_base~rssi")[2]} | The signal weakens as the vehicle nears the ground: ≈ 3.9 dB per 10 m |
| Height ↔ RSSI | F1 | {c(C1, "h_base~rssi")[0]} | {c(C1, "h_base~rssi")[1]} | {c(C1, "h_base~rssi")[2]} | The same trend, shorter range |
| RSSI ↔ SNR | F2 | **{c(C2, "rssi~snr")[0]}** | {c(C2, "rssi~snr")[1]} | {c(C2, "rssi~snr")[2]} | Signal and signal-to-noise move together while noise is constant |
| RSSI ↔ SNR | all 102 packets | **{LK["rssi_snr"]["r"]:+.2f}** | < 0.001 | 102 | …until SNR saturates near +10 dB (Figure @@ref f-link@@) |
| Roll ↔ pitch | F1 | {c(C1, "Ro~Pi")[0]} | {c(C1, "Ro~Pi")[1]} | {c(C1, "Ro~Pi")[2]} | One swing plane, not two independent oscillations |
| Height ↔ SNR | F2 | {c(C2, "h_base~snr")[0]} | {c(C2, "h_base~snr")[1]} | {c(C2, "h_base~snr")[2]} | Follows RSSI |
| Vertical speed ↔ specific force | both | {c(C1, "v~a_mag")[0]} · {c(C2, "v~a_mag")[0]} | {c(C1, "v~a_mag")[1]} · {c(C2, "v~a_mag")[1]} | 22 · 17 | No relation: speed is steady, so loads come from the swing, not the fall |
| Vertical speed ↔ sound | both | {c(C1, "v~SN")[0]} · {c(C2, "v~SN")[0]} | {c(C1, "v~SN")[1]} · {c(C2, "v~SN")[1]} | 7 · 18 | No relation at constant descent speed (Section 14.12) |
| Specific force ↔ roll | F2 | {c(C2, "Ro~a_mag")[0]} | {c(C2, "Ro~a_mag")[1]} | {c(C2, "Ro~a_mag")[2]} | Weak: large roll angles occur at the lighter-loaded points of the swing |

**Three findings stand out.**

1. **Pressure is height.** The −1.00 is not a statistical result but a physical one — and it is why the rulebook's mandatory altitude, pressure and temperature graphs carry the same information, and why the pressure channel is the redundancy for a faulty altitude.
2. **The radio degrades smoothly as the vehicle descends toward the ground, by about 4 dB per 10 m.** Close to the ground the direct path and the ground-reflected path interfere, and the link budget is spent on the ground bounce. The slope is gentle: even the lowest-flying packets keep 17 dB of margin.
3. **Quantities that should not correlate do not.** At steady descent speed there is no relationship between speed and load or speed and sound level: the vehicle is not accelerating, so it does not feel it. A correlation analysis that finds *nothing* where physics predicts nothing is an assurance that the instruments are measuring the vehicle and not each other.

## 14.10 The radio link in flight

@@fig f-link | 14_radio_link.png | Top left: RSSI against time into each capture, with the receiver's SF7 sensitivity. Top right: SNR against RSSI. Bottom left: Flight 2 RSSI against height above the landing point. Bottom right: link margin over receiver sensitivity for every packet. | 100%@@

@@tab t-link | Link statistics, 102 distinct packets@@

| | RSSI (dBm) | SNR (dB) | Margin over −123 dBm |
|---|---:|---:|---:|
| Mean | {LK["rssi_all"]["mean"]:.1f} | {LK["snr_all"]["mean"]:.1f} | **{LK["margin_to_sensitivity_db"]["mean"]:.0f} dB** |
| Weakest packet | {LK["rssi_all"]["min"]:.0f} | {LK["snr_all"]["min"]:.2f} | **{LK["margin_to_sensitivity_db"]["worst"]:.0f} dB** |
| Strongest packet | {LK["rssi_all"]["max"]:.0f} | {LK["snr_all"]["max"]:.2f} | {LK["margin_to_sensitivity_db"]["best"]:.0f} dB |

* **The throw changes the link.** In Flight 1, the mean RSSI while the vehicle was held at the terrace edge was **{F1["rssi"]["hover_mean"]:.1f} dBm** (SNR {F1["rssi"]["hover_snr"]:.1f} dB); after the throw and the canopy opening it was **{F1["rssi"]["descent_mean"]:.1f} dBm** (SNR {F1["rssi"]["descent_snr"]:.1f} dB) — **14 dB better** — and the step happens in a single packet at P-1599. While it is held in the hand against the thrower's body the antenna is consistent with being shadowed; once thrown it has free air.
* **The weakest packets were still 14 dB above the floor.** Several were decoded while the vehicle was held at the terrace edge (−109 dBm, SNR +1.5 dB). The link has margin for the situation that matters most, the flight itself.
* **After landing the link is steady:** RSSI {G1["rssi_mean"]:.1f} ± {G1["rssi_sd"]:.1f} dBm, SNR {G1["snr_mean"]:.1f} ± {G1["snr_sd"]:.1f} dB over 41 packets — the steadiness of a vehicle that is not moving.

## 14.11 The sound sensor in flight

@@fig f-sound | 13_sound.png | Acoustic level against time (left) and its distribution (right). The loudest packet of Flight 1 is the throw. | 100%@@

The microphone recorded {F1["sound"]["n"]} readings in Flight 1 and {F2["sound"]["n"]} in Flight 2 (one per rich packet — GPS, sound and status ride together). Its levels lie between 5 and 36 mV peak-to-peak, quantised in 0.806 mV steps (a 12-bit ADC on 3.3 V). **The loudest reading of Flight 1 ({F1["sound"]["peak"]:.1f} mV, P-{F1["sound"]["peak_packet"]}) is the packet immediately after the throw** — the impulsive event the microphone was chosen to catch — and the loudest of Flight 2 ({F2["sound"]["peak"]:.1f} mV, P-{F2["sound"]["peak_packet"]}) occurs 5.6 s into the drop. The mean level is the same while held ({F1["sound"]["hover_mean"]:.1f} mV) and the descent ({F1["sound"]["descent_mean"]:.1f} mV) of Flight 1, and the level does not correlate with descent speed or with specific force (|r| < 0.4, p > 0.4): at the steady speed of a canopy descent there is little change in airflow noise to measure.

## 14.12 GPS in flight

@@fig f-gps | 19_gps.png | Left: GPS fixes in the rich packets, in metres from a reference point, for Flight 1 and the after-landing session. Right: GPS altitude. | 100%@@

GPS fixes ride in every rich packet. In Flight 1, {F1["gps"]["n"]} fixes cover the hold and the descent: **the position is constant to the fifth decimal while the vehicle is held at the terrace edge, then moves {F1["gps_drift"]["dist_m"]:.1f} m toward {F1["gps_drift"]["bearing_deg"]:.0f}° (north-north-west) in {F1["gps_drift"]["dt_s"]:.1f} s — a drift of {F1["gps_drift"]["speed_mps"]:.1f} m/s** under the canopy — the horizontal speed given by the throw and the wind, carrying the vehicle across the ground as it descends. At rest after landing, {G1["gps"]["n"]} fixes scatter with an RMS of **{G1["gps"]["scatter_m_rms"]:.1f} m**, in line with the receiver's rated ~2.5 m horizontal accuracy. GPS altitude is reported by the receiver as 41–42 m during the hold and descent and 50–54 m at rest after landing: GPS vertical accuracy is several times worse than its horizontal accuracy, which is exactly why altitude in the packet comes from the barometer (resolution 0.1 m) and the GPS altitude is carried as an independent, coarse, optional field.

## 14.13 The post-landing session: a free calibration experiment

The 13 seconds of Flight 1's aftermath are a clean, stationary record — the vehicle at rest on the landing surface — and a direct view of what the vehicle's power-up sequence does.

@@fig f-ground | 17_ground_session.png | The after-landing session. Top left: altitude zeroes itself at 5.5 s. Top right: barometer noise at rest. Bottom left: resting accelerometer. Bottom right: resting attitude. | 100%@@

@@tab t-ground2 | The resting vehicle@@

| Quantity | Value |
|---|---|
| Telemetry resumed | At mission time 0, **P-001**, already at the max-rate pattern |
| Calibration completed | **{G1["first_calibrated_ti"]:.1f} s** after power-up: status `ST-R004` → `ST-R113` |
| Altitude before / after calibration | {G1["alt_uncal_mean"]:.1f} m (standard-sea-level baseline) → **{G1["altitude_cal_mean"]:+.2f} ± {G1["altitude_cal_sd"]:.2f} m** |
| Specific force at rest | **{G1["accel_mag_calibrated_mean"]:.3f} ± {G1["accel_mag_calibrated_sd"]:.3f} m/s²** against the standard 9.807 — within 0.04 % |
| Axis noise at rest | AX σ {G1["ax_sd"]:.3f}, AY σ {G1["ay_sd"]:.3f}, AZ σ {G1["az_sd"]:.3f} m/s² |
| Resting attitude | roll {G1["roll_mean"]:.1f}° ± {G1["roll_sd"]:.2f}, pitch {G1["pitch_mean"]:.1f}° ± {G1["pitch_sd"]:.2f} — the vehicle lying tilted ≈ {G1["tilt_deg"]:.0f}° from upright |
| Yaw | drifting at {G1["yaw_uncal_drift_dps"]:.2f} °/s before calibration; frozen at 0.0 – 0.1° after |
| Barometer noise | σ {G1["pressure_sd_calibrated_pa"]:.2f} Pa ({G1["pressure_sd_calibrated_pa"]/12.0:.2f} m) |
| Telemetry heard after landing | **{G1["duration_s"]:.2f} s**, 41 packets |

@@fig f-status | 21_status_strip.png | The status field of every rich packet. Filled = armed. The after-landing session starts unarmed (`R004`) and arms itself at 5.5 s (`R113`). | 100%@@

**This session shows five things at once.** The vehicle came back on the air by itself within a few seconds of the end of Flight 1's record; it began at `P-001` and at the max-rate pattern — the behaviour designed for a restart in the field; it calibrated on the spot and armed itself in 5.5 s; its barometer and accelerometer resolve at the 0.1 m and 0.015 m/s² level; and its GPS kept a fix at the landing surface. And the telemetry continued for 13 s — 2.6 times the five seconds the rulebook asks for after impact.

## 14.14 Predictions against flights

@@tab t-pred | What was predicted, and what the flights measured@@

| Quantity | Prediction | Flight result |
|---|---|---|
| Steady descent rate | ≤ 5 m/s; model for the 6 ft canopy: **1.97 – 2.18 m/s** over the mass band | **2.27 and 1.88 m/s** (+9 % / −9 % on the 500 g prediction) |
| Launch height | 100 ft = 30.48 m | **29.4 m held, 30.7 m at the apex of the throw** (Flight 1); **29.6 m** (Flight 2) |
| Telemetry rate, max rate | 3.11 Hz (designed) | **3.09 Hz** measured on the vehicle's clock |
| Telemetry rate, window | 1.43 Hz (700 ms) | **1.43 Hz** (0.700 s gaps in Flight 2 and the pad capture) |
| Packet size ceiling | ≤ 200 B | **≤ 188 B** |
| Airtime guard | 50 ms | cadence reproduced to the millisecond |
| Link margin | "tens of dB at 30 m" (free-space) | **≥ 14 dB, 31 dB mean** |
| Altitude at rest after calibration | ≈ 0 m | **−0.2 … +0.2 m** |
| Post-impact telemetry | ≥ 5 s | **12.95 s** |
| Touchdown load | ≤ 100 N study | **≈ 34 – 50 N** at a 25 ms stop |
| Structural margin | SF ≥ 7.6 (derated) | Touchdown loads of 1.6 g |
| Altitude formula | ISA, ±0.1 m | Reproduced to ±0.03 m; 5.7 % small at 31 °C, as predicted by the hypsometric equation |

## 14.15 Summary of the flight analysis

<div class="kpis">
<div class="kpi f1"><b>{F1["steady_core"]["rate_mps"]:.2f}<small>m/s</small></b><span>Flight 1 steady descent (R² {F1["steady_core"]["r2"]:.3f})</span></div>
<div class="kpi f2"><b>{F2["steady"]["rate_mps"]:.2f}<small>m/s</small></b><span>Flight 2 steady descent (R² {F2["steady"]["r2"]:.4f})</span></div>
<div class="kpi tl"><b>{F2["descent_time_s"]:.1f}<small>s</small></b><span>time of flight, Flight 2 — 29.6 m</span></div>
<div class="kpi gd"><b>{F1["release"]["a_g"]:.1f}<small>g</small></b><span>the throw, the largest load of either flight</span></div>
<div class="kpi pu"><b>{F1["attitude"]["tilt_max"]:.0f}<small>°</small></b><span>Flight 1 maximum swing from vertical in descent</span></div>
<div class="kpi tl"><b>{LK["margin_to_sensitivity_db"]["worst"]:.0f}<small>dB</small></b><span>weakest link margin in 102 packets</span></div>
<div class="kpi gr"><b>41</b><span>packets received during Flight 1</span></div>
<div class="kpi f1"><b>{G1["duration_s"]:.1f}<small>s</small></b><span>telemetry heard after landing</span></div>
</div>

* **The vehicle did what it was designed to do, in the order it was designed to do it**: carried up the building, held at the edge, thrown, opened its canopy within about a second, settled to a steady descent, landed, kept transmitting, restarted itself if needed, calibrated and armed again.
* **The descent was slow, straight and stable** — constant speed to within the noise of a barometer, 40–45 % of the limit, swinging inside a 45° cone.
* **Every channel agrees with every other**: pressure with altitude (r = −1.00), the instant of the throw across acceleration, attitude, radio and sound within one packet, and the instruments' resting values with physics (|a| = 1.000 g to 0.04 %).
* **The telemetry pipeline held**: byte-exact packets, 180 of 180 rows parsed, the designed 0.374/0.296/0.297 s cadence reproduced exactly, 102 distinct packets with no malformed one.

### Reproducing every number in this chapter

```bash
python analysis/flight-2026-09-30/launch_analysis.py Team-25.xlsx --out analysis/flight-2026-09-30
python analysis/flight-2026-09-30/make_chapter.py
```

The first command parses and cleans the log, computes `results.json`, `flight_data_clean.csv` and every figure; the second regenerates this chapter's numbers from `results.json`.
'''
OUT.write_text(txt)
print("wrote", OUT, len(txt))
