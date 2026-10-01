@@chapter 16 | Design decision register | Every major decision in one place: what was chosen, what it was chosen over, why, and the evidence.@@

## 16.1 How to read the register

A decision is recorded when it fixes something that would be expensive to change later, and each carries its reason and its evidence. The register is organised by subsystem.

## 16.2 System and software

@@tab t-dec-sw | System and software decisions@@

| # | Decision | Alternatives | Why | Evidence |
|---|---|---|---|---|
| 1 | One non-blocking 2 ms loop | RTOS tasks; interrupt-driven | Bounded worst case, trivially analysable, no preemption hazards, and a single scheduler that is fully host-testable | Scheduler tests; no blocking call exists in the loop |
| 2 | Flight core with no hardware dependency, six abstract interfaces | Direct SDK calls throughout | Mission logic testable on a laptop against mocks, including failure cases that cannot be produced safely on hardware | 5,485 C++ assertions; compile-checked Pico layer |
| 3 | Autonomous launch/landing detection; no manual trigger | Arming button; ground command | A human cannot be inside a loop that closes in seconds, whether it is a drone release or a throw; no operator-sized failure mode | Flight 1 reported `FLIGHT` for the carry and the descent |
| 4 | Telemetry never stops, in any state | Silence on `FAULT` | Telemetry is what every other judgement depends on | State-machine and fault tests |
| 5 | Packet suppressed when a mandatory field is invalid; number not consumed | Send last-good value; send with a flag | Wrong data is worse than no data; sequential numbers make gaps mean radio loss | Controller tests |
| 6 | 30 Hz acquisition, 3 Hz telemetry | Acquire at the radio rate | The radio is limited by airtime, the sensors are not: decoupling avoids aliasing the vertical-rate estimate | Sensor-rate analysis; barometer 83 Hz measured |
| 7 | Vertical rate = EWMA 0.7/0.3, updated only on a fresh conversion | Raw difference; Kalman filter | Smooths 0.1 m barometer noise without lag that would delay landing detection; no state beyond one float | State-machine and sensor-timing tests |
| 8 | Launch: armed AND (boost OR 15 m climb), 300 ms | Altitude only; accelerometer only | A drone lift or a carry up a building has no boost; a throw has a boost but no 15 m climb of its own; either must work | Launch-guard tests; Flight 1 (climb met in the carry, 5.2 g at the throw) |
| 9 | Landing: descent gate, then rest 3 s | At-rest alone | A hover is at rest too (D-4) | Hover reproduction test; Flight 1 |
| 10 | 5 s post-impact window, enforced at build time | Fixed by convention | A value below the rulebook's 5 s will not compile | `validate_config()` |
| 11 | Pad calibration: 80 samples, σ < 2 °/s, \|a\| within 1.5 m/s² of 1 g; best-effort after 20 s | Fixed offsets; blocking calibration | Bias is measured where the vehicle sits; a failed window never blocks the mission | Post-landing session: calibrated in 5.5 s |
| 12 | Mahony quaternion filter | Euler integration; complementary on angles | A tumbling vehicle passes through the ±90° singularity | 20 s tumble test at 100 °/s |
| 13 | Plausibility gate drops the previous value too | Skip the bad sample only | The vehicle must not coast on data from a sensor that is actively wrong | Gate tests |
| 14 | Faults classified (warning / degraded / critical) in a fixed array | Exceptions; dynamic log | No allocation, constant cost, and only total sensing loss is critical | 20 fault codes tested |
| 15 | 2 s hardware watchdog; restart skips the command window | Software watchdog only | A hung loop reboots in hardware, and a mid-flight reset must arm at once | Post-landing restart in the flight log |
| 16 | Raw 512-byte block log, alternating headers | FAT file | No filesystem to corrupt; torn header write recoverable | Torn-header test |
| 17 | Drivers written in-house from datasheets | Arduino / vendor libraries | Fully understood, testable, no hidden blocking | BMP280 datasheet vector reproduced |
| 18 | Five-minute command window, closes by itself | No uplink; permanent uplink | Pad-time control without a flight-time attack surface | Command-window tests |

## 16.3 Radio and protocol

@@tab t-dec-rf | Radio and protocol decisions@@

| # | Decision | Alternatives | Why | Evidence |
|---|---|---|---|---|
| 19 | SX1278 LoRa, 433 MHz | nRF24L01 (2.4 GHz) | Same silicon as the organizers' station; better penetration and margin | Organizers' station recorded both flights |
| 20 | SF7 / 125 kHz / CR 4/5 | SF9 and higher | Only SF7 meets 1 Hz with duty margin (SF9 = 1,250 ms) | Airtime 333.7 ms measured; 1.43 / 3.09 Hz |
| 21 | +17 dBm | +20 dBm | Rail stress and current (87 vs 120 mA) for a link that does not need it | Rail 3.28 V under TX; ≥ 14 dB margin |
| 22 | Sync word 0xA5 always | 0xF3 for testing | One word for test and launch: what the team hears is what the judges hear | 10 Sep range test |
| 23 | Text packet in rulebook format | Binary | Human-readable; the rulebook defines it | 180/180 rows parse |
| 24 | Rich + lean packet shapes, 200 B ceiling | Always rich | The organizers' receiver discards > 200 B | Packets ≤ 188 B |
| 25 | GPS printed at 5 decimals, whole metres | 6 decimals | Matches receiver resolution; saves 4 B | Packet size test |
| 26 | 700 ms window cadence; 374 + 296 + 296 ms max-rate pattern | 1000 ms; uniform 322 ms | Window needs gaps to listen; pattern puts GPS and sound on the air each cycle | Cadence reproduced exactly in flight |
| 27 | Slots sized from measured airtime + 50 ms guard | Modelled airtime | The model reads 1.8 % low | Four sessions to 0.1 ms |
| 28 | CRC-16 on the USB link | None | Separates transport corruption from malformed packets | Known-answer vector |
| 29 | One shared link profile and one shared fixture file | Separate copies | Silent total failure if they disagree | Cross-language tests |

## 16.4 Hardware, structure and recovery

@@tab t-dec-hw | Hardware, structure and recovery decisions@@

| # | Decision | Alternatives | Why | Evidence |
|---|---|---|---|---|
| 30 | RP2040 Pico (×2) | ESP32, AVR, STM32 | RAM, watchdog, ADC, SDK, cost; no stray 2.4 GHz radio | Flight |
| 31 | MPU-6500 six-axis IMU | Nine-axis part | Rulebook reference is the six-axis class; roll and pitch are gravity-referenced and absolute | Rest \|a\| = 1.000 g |
| 32 | ±16 g, ±2000 °/s, 20 Hz filter | ±8 g; wider filter | 3× headroom over measured peak 5.2 g; no aliasing at 30 Hz | Flight loads |
| 33 | BMP280 on I²C | Analogue pressure sensor | The rulebook's named sensor; one chip for P, T, altitude | σ 1.15 Pa = 0.10 m |
| 34 | Altitude relative to a ground baseline | Absolute ISA altitude | Rulebook asks 0 m on the pad whatever the weather | Rest ±0.2 m; F1/F2 baselines |
| 35 | NEO-6M GPS with quality gate | Raw fixes | A reported fix is not a holdable fix (D-6) | Rest scatter 2.3 m RMS |
| 36 | Microphone (LM393 module) as the additional sensor | Humidity, air quality, UV | Flight-proven descent instrument; cheap; impulsive events | The throw is the loudest packet |
| 37 | microSD raw log | Flash on the Pico | Removable, large, survives a vehicle fault | 100/100 writes; 300/s |
| 38 | No external regulator | AMS1117 | Dropout at full cell; Pico rail measured 3.28 V | Rail measurements |
| 39 | Power LED on the 3.3 V rail | On a GPIO; on the battery | Lights immediately; goes dark if the system is dead | Design review |
| 40 | Local capacitors: 470 µF + 100 nF (card), 10 µF + 100 nF (radio) | None; one shared | The card's write spike and the radio's PA key-up each get their own reservoir | Card 100/100 after the fix |
| 41 | Universal board, short soldered runs, no sockets | Custom PCB; breadboard | Frozen pin map, short supply paths, same-day changes, no loose sockets | Soldered board passes gates 3–7 |
| 42 | Sided-box frame 118.5 × 115 × 110 mm | Cylinder | Board fits flat; organizers confirmed a 12 cm sided box | CAD read from STEP |
| 43 | Open frame with arched faces | Closed shell | Load path, ambient pressure for the barometer, access | Safety factor ≥ 7.6 derated |
| 44 | White PETG, printed on its base | PLA, ABS | Tough, prints without an enclosure, deforms before it breaks; orientation fixed in advance | Structural studies |
| 45 | Model minimum 80 cm for 550 g at 35 °C (vented); **6 ft canopy flown** | Fly the minimum | The floor guarantees the cap only at the edge of the model; 5.2× its area adds margin against Cd and mass uncertainty and a harder hand-thrown start, and gives a ~1 J arrival | Model 1.9–2.2 m/s; flights 2.27 and 1.88 m/s |
| 46 | Canopy external / semi-exposed | Packed inside | Deploys as soon as the vehicle is launched | Opened about 1 s after the apex of the throw |
| 47 | Egg chamber inside the +7 cm allowance | Separate pod | Meets the envelope; part of one printed model | 128.7 g including the chamber |

## 16.5 Decisions about how the work was done

| # | Decision | Why |
|---|---|---|
| 48 | Every constant names its source | A number with no source cannot be reviewed |
| 49 | Predictions written before measurement | Keeps the model honest |
| 50 | Documentation fails the build when it disagrees with the code | Stale documentation is believed; a failing build is noticed |
| 51 | Photograph and identify every part on arrival; read registers to settle identity | A listing is not a datasheet; a register read is not an opinion |
| 52 | Post-flight analysis written and tested against a synthetic flight before the launch | The four-hour analysis window is for interpreting data, not for writing code |
