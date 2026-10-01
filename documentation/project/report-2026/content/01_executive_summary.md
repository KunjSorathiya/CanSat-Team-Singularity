@@chapter 1 | Executive summary | One page of answers: what the CanSat is, what it did on 30 September, and the five ideas that shaped it.@@

## 1.1 The vehicle in one page

<p class="lead">The CanSat is a can-sized satellite built around a Raspberry Pi Pico. A drone lifts it to 100&nbsp;ft (30.48&nbsp;m) and releases it; it deploys a parachute, descends well under the 5&nbsp;m/s limit, and streams rulebook-format telemetry over 433&nbsp;MHz LoRa from the moment it is switched on until well after it lands. Everything it senses is also written to an onboard microSD card.</p>

<div class="kpis">
<div class="kpi f1"><b>29.4<small>m</small></b><span>release height above the pad, Flight 1 — 96 ft (corrected height; the pressure peak at release is 100.8 ft)</span></div>
<div class="kpi f2"><b>29.6<small>m</small></b><span>drop height, Flight 2 — 97 ft</span></div>
<div class="kpi f1"><b>2.27<small>m/s</small></b><span>steady descent rate, Flight 1 (± 0.05) — 2.2× inside the 5&nbsp;m/s limit</span></div>
<div class="kpi f2"><b>1.88<small>m/s</small></b><span>steady descent rate, Flight 2 (± 0.02) — 2.7× inside the limit</span></div>
<div class="kpi tl"><b>3.09<small>Hz</small></b><span>telemetry rate in the armed flight configuration; 1.43&nbsp;Hz in the pre-arm configuration; rulebook floor 1&nbsp;Hz</span></div>
<div class="kpi tl"><b>41/41</b><span>packets heard by the organizers' station across Flight 1 and 41/41 after landing</span></div>
<div class="kpi gd"><b>≥ 14<small>dB</small></b><span>weakest link margin over receiver sensitivity (RSSI −109 … −79&nbsp;dBm)</span></div>
<div class="kpi pu"><b>12.95<small>s</small></b><span>of telemetry heard after landing — 2.6× the 5&nbsp;s requirement</span></div>
</div>

The system has four parts that were designed together:

1. **A flight computer** — one RP2040, running a single non-blocking loop that reads an MPU-6500 IMU, a BMP280 barometer, a NEO-6M GPS and a microphone, calibrates itself on the pad, detects its own launch and landing, and transmits a rulebook packet every 0.97&nbsp;s (three packets) or 0.70&nbsp;s.
2. **A radio link** — an SX1278 (RA-02) LoRa module at 433&nbsp;MHz, SF7 / 125&nbsp;kHz, with the official launch sync word, shared by the vehicle and by the team's own ground bridge.
3. **A structure and recovery system** — a 3D-printed PETG frame with an egg chamber, a sewn canopy sized by a closed-form descent model, a manual switch and a power LED.
4. **A ground station and an analysis pipeline** — a bridge Pico, a CRC-framed USB link, a parsing/validating Python pipeline, a single-file web console, and the post-flight analysis that produced Chapter 14.

@@fig f-arch | d01_architecture.png | The whole system: the vehicle, the radio link, and the team's ground station beside the organizers' official stations. | 60%@@

## 1.2 What flew on 30 September 2026

Two descents were recorded by the organizers' ground station, plus two shorter captures. All four are analysed in Chapter 14.

@@tab t-sessions | The four captures in the organizers' log@@

| Capture | Packets | What it shows |
|---|---:|---|
| **Flight 1** — 18:25 IST | 41 (P-1585 … P-1625) | The vehicle in `FLIGHT` state, carried at 29 m, released, free fall, canopy opening, steady descent to within a few metres of the ground. **41 of 41 packets received** |
| **Flight 1, after landing** | 41 (P-001 … P-041) | 13 s on the ground after landing: the flight computer re-initialised itself, resumed telemetry at the max rate within about 2 s, re-calibrated in 5.5 s and re-armed |
| **Flight 2** — 18:46 IST | 18 received of 24 sent (P-148 … P-171) | A 29.6 m descent, 15.4 s long, from the first packet to touchdown |
| **Pad capture** — 17:55 IST | 2 (P-420, P-421) | Two packets from a vehicle standing on the ground at 0 m |

@@fig f-compare | 06_flight_comparison.png | The two descents on one axis, with the 5 m/s limit drawn as a reference line, and the steady rates. | 92%@@

<div class="callout result"><div class="ct">The headline</div>

**Both flights descended at roughly 38–45 % of the permitted rate.** Flight 1 settled at 2.27&nbsp;m/s within 1.2 s of release and held it to the end of the record; Flight 2 held 1.88&nbsp;m/s from its first sample to touchdown. The slower descent buys a longer, gentler flight — 15.4&nbsp;s for the 29.6&nbsp;m of Flight 2 — and a landing equivalent to a fall of only 18–26&nbsp;cm.

</div>

@@fig f-margins | 23_requirement_margins.png | Each measured quantity as a multiple of the requirement it answers. 1.0 is the requirement. | 88%@@

## 1.3 Five ideas that shaped the design

**1. Telemetry never stops.** No peripheral failure, no mission state — not even `FAULT` — can silence the radio. The loop never blocks on hardware, every recovery path is bounded, and a 2&nbsp;s hardware watchdog restarts the flight computer if anything hangs. The flight data shows this working: after landing, the vehicle restarted itself and was transmitting again within about two seconds.

**2. Wrong data is worse than no data.** A mandatory field that cannot be trusted suppresses the packet instead of sending a plausible-looking wrong value — and a suppressed packet does not consume a packet number, so a gap at the ground station always means radio loss and never a sensor decision.

**3. The flight core knows no hardware.** All mission logic compiles on a laptop against six abstract interfaces. That is why 5,485 C++ assertions could exercise the entire flight before a single component had been unpacked, and why the logic met real hardware only after thousands of assertions had already exercised it.

**4. Every number says where it came from.** Rulebook, datasheet, textbook, or measurement — named in a comment at the definition. A documentation checker fails the build when a number in the prose disagrees with the source that defines it.

**5. Predictions are written down before measurements.** The bring-up record lists 94 predicted values; each was entered before the instrument was touched. Chapter 14 closes the same loop for the flight: the descent model, the link budget, the airtime and the structural load cases are each compared with what the flights measured.

## 1.4 Where each result is found

| Question | Where |
|---|---|
| What does the mission require, and how is each requirement met? | Chapter 2 |
| What does the vehicle do, minute by minute? | Chapter 3 |
| Why these components? | Chapters 5 and 16 |
| How is the structure strong enough? | Chapter 8 |
| Why does the parachute work the way it does? | Chapter 9 |
| How does the software decide that it has launched or landed? | Chapters 3 and 10 |
| What exactly goes over the air? | Chapter 11 |
| What did the flights show? | **Chapter 14** |
