@@chapter 14 | Flight results and data analysis | Two descents, 102 distinct packets, analysed channel by channel — altitude, temperature, pressure, acceleration, orientation, descent rate, radio link, and how each relates to the others.@@

## 14.1 What the ground station recorded

On 30 September 2026 the organizers' ground station recorded the vehicle's packets and exported them as `Team-25.xlsx`: **180 rows from 10 exported files.** Before any number is quoted, the log has to be made into what it should have been.

@@tab t-clean | From the export to the analysis dataset@@

| Step | Result |
|---|---|
| Rows in the workbook | **180** — one per received LoRa packet, with host timestamp, packet text, RSSI and SNR |
| Parsed by the ground station's own `parse_packet()` | **180 / 180** — every row passes the strict parser; `CAN-Team-25` leads every packet |
| Repeated exports removed (key: packet number + mission clock) | 78 duplicate rows removed → **102 distinct packets** |
| Split at every restart of the mission clock | **4 power sessions** (the rows are not in time order; two exports had been concatenated) |
| Clock used for dynamics | The **vehicle's mission clock** (`Ti-`), never the host timestamp — the host log buffers: packets P-1622…P-1625 arrived 30 ms apart although they are 0.97 s apart on the vehicle's clock |

@@fig f-sessions | 01_session_timeline.png | The four power sessions in the log. Power-on times are reconstructed from the mission clock; the hatched part is the first five minutes (the command window). | 96%@@

@@tab t-sessions2 | The four sessions@@

| Session | Power-on (IST) | Mission clock | Packets | Content |
|---|---|---|---:|---|
| **S0** · pad capture | 17:51:01 | 293.3 – 294.0 s | 2 (P-420 … P-421) | Standing on the ground, 0 m |
| **F1** · Flight 1 | 18:14:34 | 672.9 – 685.9 s | 41 (P-1585 … P-1625) | Carried at height, release, descent |
| **G1** · after landing | 18:26:02 | 0 – 12.95 s | 41 (P-001 … P-041) | On the ground after Flight 1 |
| **F2** · Flight 2 | 18:44:07 | 102.9 – 119.0 s | 18 (P-148 … P-171) | A 29.6 m descent |

Two important conventions follow from the session structure. First, **each power cycle sets its own altitude zero**: the vehicle calibrates a ground baseline at power-up and again when the command window closes, so "0 m" means the pad *of that power cycle*. Second, packet numbers restart at `P-001` at every power cycle — as the rulebook requires — and the ground station's vehicle-restart logic handles it.

## 14.2 The telemetry stream itself

@@fig f-stream | 18_packet_stream.png | Top left: packet count against time (the 1 Hz rulebook floor dashed). Top right: gaps between packets in the max-rate pattern. Bottom left: packet size by shape. Bottom right: which packet slots are present in the shared log. | 100%@@

@@tab t-stream | Packet stream statistics@@

| Session | Received | Sent | Rate on the vehicle's clock | Median gap | Mean packet size |
|---|---:|---:|---:|---:|---:|
| Flight 1 | **41** | 41 | **3.09 Hz** | 0.297 s | 143 B |
| After landing | **41** | 41 | **3.09 Hz** | 0.297 s | 134 B |
| Flight 2 | 18 | 24 | **1.43 Hz** transmit cadence | 0.700 s | — |
| Pad capture | 2 | 2 | 1.43 Hz | 0.701 s | 142 B |

* **The designed cadence is visible to the millisecond.** In both max-rate sessions the gap to the next packet alternates 0.374 s (after the rich packet), 0.296 s and 0.297 s — the three slots of Section 11.4 — and the pattern `Rll Rll Rll …` (R = rich, l = lean) repeats without a single break across all 41 packets of each session.
* **Packet sizes follow the shapes:** lean packets 118–130 B, rich packets 136–188 B, all comfortably under the organizers' 200-byte ceiling.
* **Flight 1 and the after-landing session are complete: 41 of 41 packets each, no gaps.** Flight 2 was captured at the pad-phase cadence of 1.43 Hz (a 0.70 s gap, as in the pad capture); of its 24 packet numbers 18 are in the shared log.
* **A packet decoded at SNR −6.75 dB** (pad capture, RSSI −105 dBm) — within 1 dB of the SF7 demodulation limit (about −7.5 dB) — shows how much headroom the chosen spreading factor leaves in a weak link.

## 14.3 Flight 1

Flight 1 is the drone flight. The vehicle had been powered for 11 min 13 s when the log begins; it had armed after the five-minute command window (`ST-F111`: **F**LIGHT, **1** armed, **1** calibrated), so its state machine recognised the lift during the climb and reported `FLIGHT` through the carry, the release and the descent.

@@tab t-f1events | Flight 1 event log@@

| Packet | Mission time | Event | Evidence |
|---|---:|---|---|
| P-1585 … 1598 | 672.9 – 677.2 s | **Carried at height.** Transmitting from 29.4 m (96 ft) | Reported altitude 27.6 – 27.9 m (σ 0.09 m); pressure 1008.8 hPa; |a| = 10.20 ± 0.59 m/s² ≈ 1 g; roll ≈ 109°, gravity along +Y — the vehicle is carried on its side |
| **P-1599** | 677.47 s | **Release** | Specific force jumps to **50.8 m/s² (5.2 g)** (AX -27.5, AY -13.4, AZ -40.5); RSSI improves from -103 to -88 dBm in one packet |
| P-1600 | 677.77 s | **Peak** | Transmitted altitude 29.1 m (30.7 m corrected = **100.8 ft**); |a| falls to 0.50 g; the sound level reaches its record of 36.3 mV |
| P-1601 … 1602 | 678.14 – 678.44 s | **Free fall** | |a| 0.67 g then 1.18 g; descent speeds climb to 7.0 m/s |
| **P-1603** | 678.74 s | **Canopy opens** | |a| = **2.1 g** along the vehicle's z axis (AZ = 18.3 m/s²) — the opening shock — 0.97 s after the peak, 5.2 m below it |
| P-1604 … 1621 | 679.1 – 684.5 s | **Steady descent** | Linear fall at 2.27 ± 0.05 m/s, R² = 0.991 |
| P-1622 … 1625 | 684.9 – 685.9 s | Arrival | Height 9.7 m above the pad baseline at the last packet; pressure then settles 15 Pa from the ground value measured 2 s later (≈ 1.3 m) |

@@fig f-f1-mand | 02_f1_mandatory_graphs.png | **Flight 1 — the three mandatory graphs.** Altitude (as transmitted, and re-derived from the same pressure with the hypsometric equation), temperature and pressure against mission time, with packet number along the top. | 100%@@

**Reading the three graphs together.** Altitude and pressure are one measurement seen twice: the pressure rises by 239 Pa from the carry to the last packet, and the altitude falls by the corresponding 20 m. The temperature channel is a flat 31.4 °C: in a 13-second record the barometer die does not move by a tenth of a degree, which is the right behaviour — a temperature channel that wandered during a 30 m descent (a 0.2 K change in the air) would be reporting electronics, not weather.

@@fig f-f1-desc | 04_f1_descent.png | **Flight 1 — the descent.** Top: height from the release peak, the free-fall segment shaded, and the least-squares line through the steady descent. Bottom: descent speed from successive packets against the 5 m/s limit. | 100%@@

<div class="callout result"><div class="ct">Flight 1 descent, in numbers</div>

* **Steady descent rate 2.27 ± 0.05 m/s** (temperature-corrected); 2.16 m/s from the altitude as transmitted — the ISA formula's 5.7 % shortfall at 31 °C (Section 14.7).
* The deployment transient peaks at **7.0 m/s** during the 0.97 s between the release peak and the canopy opening — free fall from rest for one second reaches 9.5 m/s without a canopy; here the canopy was already loading within a second — and the vehicle is on its steady rate **1.3 s after the peak.**
* The vehicle fell 21.1 m in the 8.1 s from the peak to its last packet in the log.

</div>

@@fig f-f1-acc | 07_f1_acceleration.png | **Flight 1 — acceleration.** The release jolt (5.2 g), the free-fall dip below 1 g, the canopy-opening load (2.1 g) and the descent at about 1 g with canopy swing. | 100%@@

The accelerometer tells the whole story of the flight. **While carried, |a| = 1.0 g with the gravity vector on the vehicle's Y axis — the vehicle hangs on its side.** At the release the three axes swing together to −27, −13 and −41 m/s², a 5.2 g impulse; then |a| collapses to 0.5 g (free fall), recovers through 0.7 and 1.2 g as the canopy fills, and peaks at 2.1 g at the opening. From there the vehicle sits upright — AZ ≈ +9.8 m/s² on average (10.5 ± 3.2) — and swings about it.

@@fig f-f1-all | 27_flight1_all_channels.png | **Flight 1 on one clock.** Height, specific force, roll and pitch, RSSI and acoustic level — release and canopy opening marked. The same instant shows up in every channel: the acceleration spike, the roll swinging from 110° (on its side) to upright, the radio signal improving by 14 dB, and the loudest microphone packet. | 96%@@

## 14.4 Flight 2

Flight 2 begins at the vehicle's first packet in the log (P-148, mission time 102.9 s, transmitted altitude +1.0 m) and ends at touchdown. The vehicle was in its 1.43 Hz pad-phase configuration (`ST-R003` throughout), so the log is a clean, uniformly spaced, 0.70 s-cadence record of a complete descent.

@@fig f-f2-mand | 03_f2_mandatory_graphs.png | **Flight 2 — the three mandatory graphs.** The transmitted altitude falls from +1.0 to −26.9 m relative to the vehicle's baseline; the pressure rises 335 Pa; temperature is a constant 31.1 °C. | 100%@@

@@tab t-f2 | Flight 2 in numbers@@

| Quantity | Value |
|---|---|
| Drop height, from pressure | **29.6 m = 97.0 ft** (as transmitted: 27.9 m; pressure rise 335 Pa) |
| Descent time | **15.4 s** from the first packet to touchdown |
| Steady descent rate | **1.88 ± 0.02 m/s**, R² = 0.9988 (1.78 m/s as transmitted) |
| Mean rate over the whole drop | 1.92 m/s; first half 1.79, second half 1.96 m/s — the descent does not accelerate |
| Peak load during the descent | **1.93 g** at P-150 (mission time 104.3 s) |
| Touchdown | P-170 at 118.3 s; the next packet reads **1.57 g** and pitch 50° as the vehicle settles |
| Swing angle (accelerometer vs vertical) | median 13°, 95th percentile 31° |

@@fig f-f2-desc | 05_f2_descent.png | **Flight 2 — the descent.** The least-squares line is straight to within the noise of the barometer (R² = 0.999): the vehicle fell at constant speed from its first sample to touchdown. Bars are speeds from successive packets; the gaps are packet numbers absent from the shared log. | 100%@@

@@fig f-f2-acc | 08_f2_acceleration.png | **Flight 2 — acceleration.** Specific force stays within a band around 1 g, with the canopy load of 1.9 g at P-150 and a touchdown reading of 1.6 g. | 100%@@

## 14.5 The two flights compared

@@tab t-compare | Side by side@@

| | **Flight 1** | **Flight 2** |
|---|---:|---:|
| Drop height from pressure | 29.4 m carried → 30.7 m peak (**96 ft → 101 ft**) | **29.6 m (97 ft)** |
| Steady descent rate | **2.27 ± 0.05 m/s** | **1.88 ± 0.02 m/s** |
| Margin to the 5 m/s limit | 2.2× | 2.7× |
| Peak vertical speed | 7.0 m/s (canopy filling) | 3.1 m/s |
| Opening / peak load | 2.1 g (release jolt 5.2 g) | 1.9 g |
| Swing angle, median / 95th percentile / max | 8° / 18° / 18° | 13° / 31° / 46° |
| Roll σ / pitch σ in descent | 19° / 12° | 26° / 20° |
| Air density in descent | 1.155 kg/m³ | 1.157 kg/m³ |
| Temperature | 31.4 °C | 31.1 °C |
| RSSI mean (min … max) | -93.3 dBm (−109 … −79) | -96.6 dBm (-106 … -87) |
| Packets received | **41 of 41** | 18 of 24 |

@@fig f-compare-ref | 26_load_by_phase.png | The load on the vehicle by phase of the mission, in units of g: carried, free fall, steady descent (both flights) and at rest after landing. The resting value (1.000 g, σ 0.0015 g) is the accelerometer's calibration made visible. | 92%@@

Both flights tell the same story from different starting conditions. **They agree on the facts that matter for the rulebook** — a drop of 29–31 m (≈ 97–101 ft), a steady descent at 38–45 % of the permitted rate, a swing that stays inside the 45° cone for 93–100 % of the packets, and an arrival at a speed that corresponds to a fall of 18–26 cm. They differ in the details a descent is expected to differ in: Flight 2 is slower and perfectly straight (1.88 m/s), Flight 1 somewhat faster (2.27 m/s) with a one-second deployment transient at the start of its record. The 0.3 °C difference in air temperature changes the air density by 0.1 % and is irrelevant to the rates.

## 14.6 Attitude and stability

@@fig f-att | 09_attitude_time_series.png | Roll and pitch (top) and relative yaw (bottom) for both flights. Flight 1 starts at the release, when the vehicle rotates from its carried orientation (roll ≈ 110°) to upright within a packet. | 100%@@

@@fig f-stab | 10_stability.png | The swing cone. Each dot is one packet of steady descent: roll against pitch, with 15°, 30° and 45° circles (left, centre); cumulative distribution of the swing angle (right). Flight 1 never leaves the 18° circle; Flight 2 stays inside 45° for 93 % of its packets. | 100%@@

**What the attitude data show.**

* **Upright and swinging, never tumbling.** After the canopy opens, the vehicle's z axis stays within 18° of vertical in Flight 1 (95th percentile 18°) and 31° (95th percentile) in Flight 2. Roll standard deviation is 19° and 26°, pitch 12° and 20° — a pendulum mode under the canopy, with no sustained drift of the mean attitude (mean roll +1.2° and +3.6°).
* **Roll and pitch swing together in Flight 1** (r = +0.60, p = 0.003): the canopy swings along one plane that is not aligned with the vehicle's axes — what a single pendulum mode looks like in two body angles.
* **Yaw is a relative angle.** Yaw is integrated from the gyro and is zeroed at calibration; its value is an angle around the vertical from the pad orientation, and its meaning is the *rate*. Because yaw is sampled once per packet (3.1 or 1.4 Hz) the wrapped values jump by more than a half-turn between packets: the transmitted angle is correct, but a spin rate cannot be recovered from samples this sparse.

@@fig f-3d | 22_acceleration_vector_3d.png | The acceleration vector of each steady-descent packet in three dimensions. The vectors cluster above the 1 g sphere (grey) along +AZ — the vehicle upright — and spread sideways with the swing. | 100%@@

## 14.7 The pressure–altitude law, and why the transmitted altitude is slightly small

@@fig f-law | 11_pressure_altitude_law.png | Left: transmitted altitude against measured pressure for both flights, with the ISA formula (lines) using each flight's recovered baseline. Right: the difference between the temperature-corrected height and the transmitted altitude. | 100%@@

The vehicle converts pressure to altitude with the international standard atmosphere formula, which assumes a 15 °C air column. The analysis recovers the baseline each power cycle used (101,215.8 Pa for Flight 1; 100,911.5 Pa for Flight 2) and finds that **the transmitted altitude is reproduced by the ISA formula to ±0.03 m** — the firmware does exactly what it was written to do, to the resolution of the 0.1 m field. Real height per pascal scales with the real air temperature: on a 31 °C day the air is thinner than ISA's, so a given pressure change corresponds to **5.7 % more height** than the ISA formula reports. The right-hand panel shows it: the difference grows linearly with height from the baseline. All descent rates in this chapter use the temperature-corrected height — from the hypsometric equation, Δh = (R T / g) ln(p₀ / p), with the measured pressure and temperature — and quote the transmitted-altitude rate beside it (2.16 against 2.27 m/s; 1.78 against 1.88 m/s).

@@tab t-baro | Barometer facts the flights confirm@@

| Quantity | Value |
|---|---|
| Baseline pressure, Flight 1 (pad) | 101215.8 Pa |
| Pressure at the carry height | 100882.9 Pa, i.e. 333 Pa below the pad |
| Pressure at rest after landing | 101121.6 Pa (1.15 Pa σ) — the landing surface is ≈ 8.3 m above the pad baseline |
| Barometer noise at rest | σ = **1.15 Pa** = 0.10 m |
| Altitude noise at rest | σ = **0.11 m** (range -0.2 … +0.2 m) |
| Temperature resolution | 0.1 °C; flat to the resolution in both flights |

## 14.8 Descent physics: drag, energy and what the vehicle felt on arrival

At steady descent weight equals drag: **C<sub>d</sub>·S = 2 m g / (ρ v²).** The vehicle's mass is only known to lie in the 450–550 g band, so the drag area is given across it:

@@tab t-physics | Drag area, canopy size, energy and loads implied by the measured descent rates@@

| | Mass | C<sub>d</sub>·S | Equivalent flat diameter (C<sub>d</sub> 0.75 · 1.40) | Kinetic energy at arrival | Equivalent fall height | Force, 25 ms stop |
|---|---:|---:|---:|---:|---:|---:|
| **Flight 1** (2.27 m/s) | 450 g | 1.49 m² | 159 · 116 cm | 1.16 J | 26 cm | 41 N |
| | 500 g | 1.65 m² | 168 · 123 cm | 1.28 J | 26 cm | 45 N |
| | 550 g | 1.82 m² | 176 · 129 cm | 1.41 J | 26 cm | 50 N |
| **Flight 2** (1.88 m/s) | 450 g | 2.16 m² | 191 · 140 cm | 0.79 J | 18 cm | 34 N |
| | 500 g | 2.40 m² | 202 · 148 cm | 0.88 J | 18 cm | 38 N |
| | 550 g | 2.64 m² | 212 · 155 cm | 0.97 J | 18 cm | 41 N |

**The vehicle arrives at the speed it would have after stepping off a 26 cm step** (Flight 2: 18 cm): about 1 J of kinetic energy for a vehicle that the structural studies loaded with 100 N. The measured Flight 2 touchdown reading of 1.57 g is the accelerometer's own confirmation. Figure @@ref f-touchdown-load@@ in Chapter 8 plots these loads against the studied one.

<div class="callout why"><div class="ct">What the drag area says about the margin</div>

The inferred drag areas — 1.5 to 2.6 m² across the band and the two flights — are 4 to 7 times the 0.38 m² of an 80 cm vented flat canopy, the sizing floor of Chapter 9. Drag area is the drag coefficient times the *inflated* area of the whole descending assembly, so it reflects the canopy actually fitted, how fully it inflates, and the vehicle's true mass within the band; the flights measure that combination directly. The practical meaning is simple: **the descent system has a large reserve against the 5 m/s limit** — the sizing that was done for the heaviest vehicle on the hottest day holds with room to spare.

</div>

## 14.9 Correlations between the channels

Roughly forty variable pairs were examined for each flight. The heat maps show Pearson r between the channels in the descent proper (Flight 1 from the canopy opening, Flight 2 to touchdown); the pair plot shows the same data as scatter plots with distributions on the diagonal.

@@fig f-heat | 15_correlation_heatmaps.png | Pearson correlation matrices for the descent of each flight. Height and pressure are one measurement seen twice (r = −1.00). | 100%@@

@@fig f-pairs | 16_pair_plot.png | Pair plot of height above the last sample, descent speed, swing angle, RSSI and specific force, both flights. The diagonal shows each variable's distribution. | 100%@@

@@tab t-corr | The correlations that matter, with significance@@

| Pair | Flight | Pearson r | p | n | Reading |
|---|---|---:|---:|---:|---|
| Height ↔ pressure | both | −1.00 | < 0.001 | 22 · 17 | The barometer is a perfect altimeter: a pure monotonic law |
| Height ↔ RSSI | **F2** | **+0.70** | 0.002 | 17 | The signal weakens as the vehicle nears the ground: ≈ 3.9 dB per 10 m |
| Height ↔ RSSI | F1 | +0.50 | 0.019 | 22 | The same trend, shorter range |
| RSSI ↔ SNR | F2 | **+0.89** | < 0.001 | 17 | Signal and signal-to-noise move together while noise is constant |
| RSSI ↔ SNR | all 102 packets | **+0.77** | < 0.001 | 102 | …until SNR saturates near +10 dB (Figure @@ref f-link@@) |
| Roll ↔ pitch | F1 | +0.60 | 0.003 | 22 | One swing plane, not two independent oscillations |
| Height ↔ SNR | F2 | +0.58 | 0.015 | 17 | Follows RSSI |
| Vertical speed ↔ specific force | both | −0.37 · +0.06 | 0.090 · 0.820 | 22 · 17 | No relation: speed is steady, so loads come from the swing, not the fall |
| Vertical speed ↔ sound | both | −0.36 · +0.13 | 0.432 · 0.624 | 7 · 18 | No relation at constant descent speed (Section 14.12) |
| Specific force ↔ roll | F2 | −0.45 | 0.067 | 17 | Weak: large roll angles occur at the lighter-loaded points of the swing |

**Three findings stand out.**

1. **Pressure is height.** The −1.00 is not a statistical result but a physical one — and it is why the rulebook's mandatory altitude, pressure and temperature graphs carry the same information, and why the pressure channel is the redundancy for a faulty altitude.
2. **The radio degrades smoothly as the vehicle descends toward the ground, by about 4 dB per 10 m.** Close to the ground the direct path and the ground-reflected path interfere, and the link budget is spent on the ground bounce. The slope is gentle: even the lowest-flying packets keep 17 dB of margin.
3. **Quantities that should not correlate do not.** At steady descent speed there is no relationship between speed and load or speed and sound level: the vehicle is not accelerating, so it does not feel it. A correlation analysis that finds *nothing* where physics predicts nothing is an assurance that the instruments are measuring the vehicle and not each other.

## 14.10 The radio link in flight

@@fig f-link | 14_radio_link.png | Top left: RSSI against time into each capture, with the receiver's SF7 sensitivity. Top right: SNR against RSSI. Bottom left: Flight 2 RSSI against height above the landing point. Bottom right: link margin over receiver sensitivity for every packet. | 100%@@

@@tab t-link | Link statistics, 102 distinct packets@@

| | RSSI (dBm) | SNR (dB) | Margin over −123 dBm |
|---|---:|---:|---:|
| Mean | -92.1 | 8.3 | **31 dB** |
| Weakest packet | -109 | -6.75 | **14 dB** |
| Strongest packet | -79 | 10.75 | 44 dB |

* **Release changes the link.** In Flight 1, the mean RSSI while the vehicle was carried at height was **-102.5 dBm** (SNR 6.1 dB); after the release and canopy opening it was **-87.6 dBm** (SNR 9.6 dB) — **14 dB better** — and the step happens in a single packet at P-1599. While carried, the antenna is consistent with being shadowed by its carrier; once released it has free air.
* **The weakest packets were still 14 dB above the floor.** Several were decoded while carried at 28 m beside the drone (−109 dBm, SNR +1.5 dB). The link has margin for the situation that matters most, the flight itself.
* **After landing the link is steady:** RSSI -88.3 ± 0.8 dBm, SNR 9.7 ± 0.4 dB over 41 packets — the steadiness of a vehicle that is not moving.

## 14.11 The sound sensor in flight

@@fig f-sound | 13_sound.png | Acoustic level against time (left) and its distribution (right). The loudest packet of Flight 1 is the release. | 100%@@

The microphone recorded 14 readings in Flight 1 and 18 in Flight 2 (one per rich packet — GPS, sound and status ride together). Its levels lie between 5 and 36 mV peak-to-peak, quantised in 0.806 mV steps (a 12-bit ADC on 3.3 V). **The loudest reading of Flight 1 (36.3 mV, P-1600) is the packet immediately after the release jolt** — the impulsive event the microphone was chosen to catch — and the loudest of Flight 2 (36.3 mV, P-156) occurs 5.6 s into the drop. The mean level is the same in the carry (14.8 mV) and the descent (17.1 mV) of Flight 1, and the level does not correlate with descent speed or with specific force (|r| < 0.4, p > 0.4): at the steady speed of a canopy descent there is little change in airflow noise to measure.

## 14.12 GPS in flight

@@fig f-gps | 19_gps.png | Left: GPS fixes in the rich packets, in metres from a reference point, for Flight 1 and the after-landing session. Right: GPS altitude. | 100%@@

GPS fixes ride in every rich packet. In Flight 1, 12 fixes cover the carry and the descent: **the position is constant to the fifth decimal while the vehicle hangs under the drone, then moves 9.4 m toward 341° (north-north-west) in 4.8 s — a drift of 1.9 m/s** under the canopy, the wind carrying the vehicle across the ground as it descends. At rest after landing, 8 fixes scatter with an RMS of **2.3 m**, in line with the receiver's rated ~2.5 m horizontal accuracy. GPS altitude is reported by the receiver as 41–42 m during the carry and descent and 50–54 m at rest after landing: GPS vertical accuracy is several times worse than its horizontal accuracy, which is exactly why altitude in the packet comes from the barometer (resolution 0.1 m) and the GPS altitude is carried as an independent, coarse, optional field.

## 14.13 The post-landing session: a free calibration experiment

The 13 seconds of Flight 1's aftermath are a clean, stationary record — the vehicle at rest on the landing surface — and a direct view of what the vehicle's power-up sequence does.

@@fig f-ground | 17_ground_session.png | The after-landing session. Top left: altitude zeroes itself at 5.5 s. Top right: barometer noise at rest. Bottom left: resting accelerometer. Bottom right: resting attitude. | 100%@@

@@tab t-ground2 | The resting vehicle@@

| Quantity | Value |
|---|---|
| Telemetry resumed | At mission time 0, **P-001**, already at the max-rate pattern |
| Calibration completed | **5.5 s** after power-up: status `ST-R004` → `ST-R113` |
| Altitude before / after calibration | 17.0 m (standard-sea-level baseline) → **-0.02 ± 0.11 m** |
| Specific force at rest | **9.811 ± 0.015 m/s²** against the standard 9.807 — within 0.04 % |
| Axis noise at rest | AX σ 0.009, AY σ 0.008, AZ σ 0.015 m/s² |
| Resting attitude | roll 30.7° ± 0.05, pitch 6.6° ± 0.05 — the vehicle lying tilted ≈ 31° from upright |
| Yaw | drifting at 0.63 °/s before calibration; frozen at 0.0 – 0.1° after |
| Barometer noise | σ 1.15 Pa (0.10 m) |
| Telemetry heard after landing | **12.95 s**, 41 packets |

@@fig f-status | 21_status_strip.png | The status field of every rich packet. Filled = armed. The after-landing session starts unarmed (`R004`) and arms itself at 5.5 s (`R113`). | 100%@@

**This session shows five things at once.** The vehicle came back on the air by itself within a few seconds of the end of Flight 1's record; it began at `P-001` and at the max-rate pattern — the behaviour designed for a restart in the field; it calibrated on the spot and armed itself in 5.5 s; its barometer and accelerometer resolve at the 0.1 m and 0.015 m/s² level; and its GPS kept a fix at the landing surface. And the telemetry continued for 13 s — 2.6 times the five seconds the rulebook asks for after impact.

## 14.14 Predictions against flights

@@tab t-pred | What was predicted, and what the flights measured@@

| Quantity | Prediction | Flight result |
|---|---|---|
| Steady descent rate | ≤ 5 m/s (model: 4.4 – 5.0 m/s for the 80 cm design floor over the mass band) | **2.27 and 1.88 m/s** |
| Release height | 100 ft = 30.48 m | **29.4 m carried, 30.7 m at the peak** (Flight 1); **29.6 m** drop (Flight 2) |
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
<div class="kpi f1"><b>2.27<small>m/s</small></b><span>Flight 1 steady descent (R² 0.991)</span></div>
<div class="kpi f2"><b>1.88<small>m/s</small></b><span>Flight 2 steady descent (R² 0.9988)</span></div>
<div class="kpi tl"><b>15.4<small>s</small></b><span>time of flight, Flight 2 — 29.6 m</span></div>
<div class="kpi gd"><b>5.2<small>g</small></b><span>release jolt, the largest load of either flight</span></div>
<div class="kpi pu"><b>18<small>°</small></b><span>Flight 1 maximum swing from vertical in descent</span></div>
<div class="kpi tl"><b>14<small>dB</small></b><span>weakest link margin in 102 packets</span></div>
<div class="kpi gr"><b>41/41</b><span>packets heard during Flight 1</span></div>
<div class="kpi f1"><b>13.0<small>s</small></b><span>telemetry heard after landing</span></div>
</div>

* **The vehicle did what it was designed to do, in the order it was designed to do it**: carried at height, released, opened its canopy within one second, settled to a steady descent, landed, kept transmitting, restarted itself if needed, calibrated and armed again.
* **The descent was slow, straight and stable** — constant speed to within the noise of a barometer, 38–45 % of the limit, swinging inside a 45° cone.
* **Every channel agrees with every other**: pressure with altitude (r = −1.00), release instant across acceleration, attitude, radio and sound within one packet, and the instruments' resting values with physics (|a| = 1.000 g to 0.04 %).
* **The telemetry pipeline held**: byte-exact packets, 180 of 180 rows parsed, the designed 0.374/0.296/0.297 s cadence reproduced exactly, 102 distinct packets with no malformed one.

### Reproducing every number in this chapter

```bash
python analysis/flight-2026-09-30/launch_analysis.py Team-25.xlsx --out analysis/flight-2026-09-30
python analysis/flight-2026-09-30/make_chapter.py
```

The first command parses and cleans the log, computes `results.json`, `flight_data_clean.csv` and every figure; the second regenerates this chapter's numbers from `results.json`.
