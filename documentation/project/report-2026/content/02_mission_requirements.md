@@chapter 2 | Mission and requirements | The rulebook turned into thirty-odd testable requirements — each with a design response and the evidence that it holds.@@

## 2.1 The mission

The CanSat is powered on at ground level and begins transmitting at once. It is lifted to **100 ft (30.48 m) — in the competition by a drone, which releases it** — and launched. It deploys a parachute, descends at **no more than 5 m/s**, transmits throughout, keeps transmitting for **at least five seconds after impact**, and is then recovered.

Flight is **fully autonomous.** There is no launch command, no arming button and no manual trigger anywhere in the firmware: the vehicle powers on, calibrates itself, arms itself, detects its own launch and its own landing, and keeps talking through every failure it can survive. The reason is simple — an operator cannot be inside a loop that closes in under fifteen seconds, whether the launch is a drone release or a throw, and a design with a human trigger has a human-sized failure mode.

@@fig f-profile | c01_mission_profile.png | The mission profile. The descent segment is drawn to the Flight 1 measurement (held at 29.4 m, thrown, canopy opening, steady descent). | 94%@@

## 2.2 The rulebook's hard numbers

@@tab t-numbers | The quantities the rulebook fixes, with the requirement that carries each@@

| Quantity | Value | Requirement | The design's figure |
|---|---|---|---|
| Body envelope | 21 cm (+ 7 cm egg chamber) × 12 cm | GEN-004 | **118.5 × 115.0 × 110.0 mm** — 91.5 mm of height unused |
| Mass | 500 g ± 10 % (450–550 g) | GEN-005 | In the band; 280 g bare structure + avionics, trimmed to the band |
| Launch altitude | 100 ft / 30.48 m (drone release; equivalent to an eight-storey building) | MIS-001 | Flights launched by hand from a terrace at **29.4 m and 29.6 m** (96–97 ft) |
| Descent rate | ≤ 5 m/s | REC-005 | **2.27 and 1.88 m/s** steady, measured |
| Telemetry rate | ≥ 1 packet per second | TEL-005 | **1.43 Hz** pre-arm, **3.09 Hz** armed |
| Post-impact telemetry | ≥ 5 s | REC-008 | **12.95 s** heard after Flight 1's landing |
| Radio | 433 MHz LoRa; sync `0xF3` test / `0xA5` launch | TEL-023/024 | `0xA5` on both ends, always |
| Packet | `CAN-Team-XX; P-XXX; Ti-…; A-…; …` | TEL-009 … 020 | Byte-exact; 180 / 180 logged rows parse |

### Three rulebook ambiguities, each resolved before it could matter

The original guidelines contradicted themselves on dimensions and launch altitude. Neither was guessed at locally; both were escalated to the organizers, and the 2026 revision settled both:

| Was ambiguous | Resolution |
|---|---|
| Dimensions | **21 cm (+ 7 cm for the egg chamber) × 12 cm**, now stated identically in two places |
| Launch altitude | **100 ft, released from a drone** ("equivalent to an 8-story building"), now stated identically in two places |
| "12 cm across" — a width or a diameter? | For a prismatic body the two differ by 33 %. The organizers confirmed on 9 September 2026 that **a 12 cm sided box is acceptable**, so the section limit is a 120 mm square |

<div class="callout why"><div class="ct">Why a box rather than a cylinder</div>

A 120 mm circular bore would cap a flat 100 × 100 mm board's corner-to-corner diagonal (141 mm) well outside the circle, forcing the electronics to stand on edge. A sided box lets the board lie flat, which is the layout with the shortest wires, the best access for assembly and the most predictable centre of mass. The written confirmation from the organizers settled the question before the CAD was committed.

</div>

## 2.3 Requirement-to-evidence matrix

Thirty requirements were extracted from the rulebook; each has a design response, a verification method and a recorded status in `documentation/requirements/requirements.md`. The matrix below is its summary. **Evidence** names the measurement or test; flight evidence refers to Chapter 14.

@@tab t-matrix | Requirement-to-evidence matrix@@

| Requirement | Design response | Evidence |
|---|---|---|
| **GEN-002/003** Self-built, no kits | Every module bought individually and identified on arrival; board hand-soldered; structure printed; canopy sewn | Receiving-inspection record; photographs of every part |
| **GEN-004** Envelope | `Cansat_D1`: 118.5 × 115.0 × 110.0 mm, read from the STEP file by a script that fails the build on any disagreement | `tools/cad_dimensions.py` |
| **GEN-005** Mass band | Mass budget from weighed parts (110.6 g board, 40.7 g battery); bare vehicle 280 g, trimmed into 450–550 g | Scale readings 9 and 12 Sep |
| **MIS-003** Altitude ≈ 0 on the pad | Pad calibration averages 80 barometer samples into a ground baseline | Resting altitude −0.2 … +0.2 m (G1 session); −0.5 … +0.1 m over 62 bench packets |
| **MIS-004** Telemetry reflects the lift | Altitude in every packet, from the same compensated reading the flight core uses | Flight 1: 27.6–27.9 m reported while held at the terrace edge |
| **MIS-005** Parachute deployment | 6 ft (1.83 m) canopy, external / semi-exposed so it opens as soon as the vehicle is launched | Flight 1: 7 m/s transient → 2.3 m/s in about 1 s, 2.1 g opening load |
| **PAY-002** Egg chamber | Cushioned chamber designed into the frame within the +7 cm allowance | CAD; 128.7 g printed structure including the chamber |
| **PWR-001/002** Switch and LED | Switch in the battery lead; power LED on the regulated 3.3 V rail, not a GPIO | Fitted in the structure's switch cut-out |
| **PWR-004** Auto-transmit on power-up | No arming step anywhere between power and the first packet | Telemetry runs from mission time 0 (post-landing session: P-001 at `Ti-00:00:00:000`) |
| **TEL-001…004** Continuous telemetry | Scheduler independent of mission state; `FAULT` does not stop transmission | Flight 1: 41 packets received; after landing 41 |
| **TEL-005** ≥ 1 Hz | 700 ms period (1.43 Hz); 3-slot pattern (3.11 Hz) after the command window | Measured 1.43 Hz and 3.09 Hz in the flights |
| **TEL-006/010** Team identity | Identity is configuration; the placeholder `CAN-Team-XX` is refused at start-up | 180 / 180 rows carry `CAN-Team-25` |
| **TEL-007/008** `P-001` start, sequential | Counter starts at 1; suppression does not consume a number | G1 session starts at P-001 |
| **TEL-009…020** Field order and precision | Byte-exact formatter; C++, Python and JavaScript parsers held to one fixture file | 180 / 180 rows parse under the strict parser |
| **TEL-021** No corrupted mandatory fields | Per-field validity flags; an incomplete set yields no packet | Test suite; no invalid packet in the log |
| **TEL-023/024** Sync words | `0xA5` for launch; both Picos fly it always | Organizers' station received the flights |
| **SEN-001…010** Mandatory sensing | BMP280 (pressure, temperature, altitude), MPU-6500 (3-axis accelerometer, 3-axis gyro), Mahony attitude filter | All channels present and consistent in every flight packet |
| **SEN-011** Additional sensors | NEO-6M GPS (position, altitude), LM393 microphone (acoustic level) | `GP-` and `SN-` fields in the rich packets |
| **REC-005** ≤ 5 m/s | Model minimum 80 cm (5 m/s at 550 g, 35 °C); **6 ft canopy flown** (model: 1.9–2.2 m/s) | **2.27 and 1.88 m/s** steady |
| **REC-006** Stable descent | 6 ft canopy; attitude filter reports roll/pitch/yaw each packet | Swing ≤ 18° (F1) and ≤ 46° (F2); upright throughout both descents |
| **REC-007** Structure intact | Open-frame PETG; structural safety factors 7.6–40.9 | Touchdown load 1.6 g measured |
| **REC-008** ≥ 5 s post-impact | `LANDED` holds a 5 s window; telemetry never stops | 12.95 s of packets heard after Flight 1 landing |

## 2.4 What the rulebook says about packet format, and how the vehicle matches it

The rulebook gives one packet format and one rule above all others — *mandatory fields first, optional fields only if bandwidth allows.* The vehicle's packet is that format, byte for byte, with three optional groups appended in priority order: GPS, then sound, then a status field.

@@fig f-packet-note | d08_telemetry_build.png | The path from a snapshot to a packet. Nothing is built if any mandatory field is invalid, and the packet number is consumed only when a packet is actually produced. | 60%@@

Section 11 specifies the packet in full; the flight chapter reproduces real packets from both flights.
