@@chapter 4 | System architecture | Layers, data path, rates, and the seven rules the code is built around — and why each exists.@@

## 4.1 The layer model

The system is layered, and each layer depends only on the one beneath it. **The flight core never includes a Pico SDK header.** Hardware reaches it only through six abstract interfaces — `Imu`, `Barometer`, `Gps`, `Radio`, `SdLogger`, `BoardIo`. Tests substitute mocks; the vehicle substitutes `flight::pico::*`.

@@fig f-layers | d02_layers.png | Each layer depends only on the layer beneath it. The flight core (bold) is hardware-free. | 88%@@

<div class="callout why"><div class="ct">Why this rule</div>

A flight computer has a hardware-dependent part (pins, buses, timing) and a logic part (what a launch looks like, when to transmit). If the two are mixed, the logic can only be tested with the hardware attached — which means late, slowly, and never exhaustively. Separated by six small interfaces, the logic runs on a laptop at full speed: **5,485 C++ assertions exercise the entire mission logic with no board present**, including failure cases (a sensor that stops, a radio that refuses to transmit, a card that fills up) that would be dangerous or impossible to produce on demand with hardware. The software was therefore complete and tested before any component had been unpacked, and the hardware work could concentrate on what only hardware can reveal.

</div>

## 4.2 The end-to-end data path

```text
sensors -> controller -> plausibility gate -> bias correction -> orientation
        -> AGL and vertical rate
        -> TelemetryBuilder   (nothing is built if any mandatory field is invalid)
        -> packet string -> SX1278 -> 433 MHz LoRa -> SX1278 -> bridge Pico
        -> CRC-framed USB serial
        -> transport -> CRC check -> parse -> validate -> health -> log
        -> dashboard, web console, CSV export
```

A packet becomes a telemetry point only if it survives every stage, **and each stage's rejection is counted separately** — so a transport fault is never mistaken for a sensor fault.

## 4.3 Rates: each stage runs at what its physics allows

The radio is the slowest stage by two orders of magnitude and nothing else is tied to it.

@@tab t-rates | The rate split@@

| Stage | Rate | Bounded by | Why this value |
|---|---:|---|---|
| Main loop tick | 500 Hz (2 ms) | Scheduling jitter and the GPS UART FIFO | At 9600 baud the RP2040's 32-byte FIFO fills in 33 ms; a 2 ms tick drains it long before, and jitter stays under 6 % of the sensor period |
| Sensor acquisition, attitude, vertical rate | **30 Hz** (33 ms) | Barometer conversion time | The BMP280 delivers ~83 Hz; sampling at 30 Hz stays inside 2.4× margin so every sample is a fresh conversion |
| Mission state machine | 30 Hz | Fed each acquisition | A 33 ms decision latency against a 300 ms launch confirmation |
| Battery sample, health refresh | 1 Hz | Nothing meaningful changes faster | |
| SD flush | 0.5 Hz | Write latency | Appends happen per packet; the flush is the sync |
| **RF telemetry** | **1.43 Hz → 3.11 Hz** | **LoRa airtime** | Chapter 11 |

30 Hz of **RF** telemetry is physically impossible with this radio and packet — the best case in the airtime table (SF7 at 250 kHz) reaches 5 Hz at 100 % channel occupancy. 30 Hz of **acquisition and state estimation** is possible, and that is what the loop does. Decoupling the two rates rather than faking one is the architecture's central timing decision.

## 4.4 The seven design rules

These are the invariants the code is built around. Breaking one is a design change, not a refactor.

| # | Rule | Reason |
|---|---|---|
| 1 | **Telemetry never stops.** No peripheral failure and no state, `FAULT` included, suppresses telemetry that can still be produced correctly | The telemetry link is the one thing every other judgement about the flight depends on |
| 2 | **Wrong data is worse than no data.** Mandatory fields that cannot be trusted suppress the packet rather than send a plausible wrong value | A silent wrong value cannot be filtered downstream; a gap can |
| 3 | **Sequential numbering is over transmitted packets.** Suppression does not consume a number | A gap at the receiver then means radio loss and nothing else |
| 4 | **The flight core knows no hardware** | Testability — Section 4.1 |
| 5 | **Nothing in the flight loop blocks or allocates.** Fixed-size buffers, bounded loops | A blocking call or a heap failure in a 2 ms loop is a mission failure; bounded code has bounded worst cases |
| 6 | **Every constant says where it came from** — rulebook, datasheet, textbook or engineering choice | A number with no source cannot be reviewed, and a tuned value with no record is lost |
| 7 | **Predictions stay labelled as predictions** until a measurement replaces them | It keeps the model honest — the analysis in Chapter 14 can only compare predictions to flights because the predictions were recorded first |

## 4.5 How a claim becomes trustworthy

@@fig f-verif | d14_verification_flow.png | A requirement is traced from the rulebook to flight. The documentation checker ties the numbers in the prose to the source that defines them. | 100%@@

`tools/check_doc_claims.py` reads numbers out of the documentation and checks them against the source that defines them — pin assignments, telemetry rates, watchdog periods, packet sizes, test counts, rulebook constants, the generated netlist, the descent model's own output, the mass-budget arithmetic, and every relative link and heading anchor across 53 documents. It runs in the same build as the firmware tests, so **a document that drifts from the code fails the build.**

## 4.6 The software at a glance

@@tab t-modules | The flight computer's modules@@

| Module | Responsibility |
|---|---|
| `controller.cpp` | The flight loop orchestrator — the one place mission behaviour is composed |
| `state_machine.cpp` | `INIT → SELF_TEST → READY → FLIGHT → LANDED → RECOVERY`, plus `FAULT` |
| `scheduler.cpp` | `PeriodicTask` — fixed-period, non-allocating, stall-tolerant timers |
| `orientation.cpp` | Mahony complementary filter on a unit quaternion: gyro propagates, accelerometer corrects roll and pitch |
| `sensor_math.cpp` | Accelerometer/gyro scaling, Bosch BMP280 compensation, barometric altitude |
| `startup_calibration.cpp` | Pad calibration: gyro bias, a rotation-invariant accelerometer scale, barometric reference |
| `telemetry_builder.cpp` | Snapshot → record → packet string → SD CSV row |
| `fault_manager.cpp` | Fixed-size fault store indexed by enum; never grows |
| `raw_block_log.cpp` | Append-only 512-byte-block log, no filesystem |
| `gps_parser.cpp` | Streaming NMEA-0183 (GGA and RMC) with checksum validation |
| `sx1278.cpp` (shared) | Register-level LoRa driver, driven through a callback struct so it runs on the vehicle, the bridge, or a fake register bank |
| `telemetry.cpp` (shared) | Rulebook formatter and strict parser |
