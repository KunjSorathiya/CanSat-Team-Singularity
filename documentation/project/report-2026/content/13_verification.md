@@chapter 13 | Verification and bring-up | 6,131 automated checks on the host, 94 recorded bench measurements — and the prediction written down before each one.@@

## 13.1 The host test suite

```bash
bash tools/build_host.sh
```

compiles and runs every C++ suite, the Python suites and the Node suite, then checks the documentation against the source. **All of it runs without hardware.**

@@fig f-tests | c06_test_suites.png | Automated checks by suite (log scale). | 92%@@

@@tab t-suites | Test suites and what each covers@@

| Suite | Coverage | Result |
|---|---|---|
| `flight_tests` | 143 suites: packet format, parser, shared fixtures, state machine, orientation and angle wrapping, GPS validation, sensor math, timing, calibration, faults, scheduler, block log and torn-header recovery, controller behaviour, link profile, LoRa airtime | **4674 / 4674** |
| `sd_card_tests` | microSD init, SDHC vs SDSC addressing, block round trip, bus release, timeouts, write-error paths | **613 / 613** |
| `sx1278_tests` | LoRa register sequence, TX timeout, RX and CRC handling, RSSI conversion | **168 / 168** |
| `fat_volume_tests` | FAT32 log lookup: MBR and superfloppy, contiguity, missing file, a card that stops answering | **30 / 30** |
| `flight_smoke_test` | Boot, first three packets, GPS parse | Passed |
| `ground_station_tests` | Framing, CRC detection, resync, known-answer vector | Passed |
| Python — ground station | Parser, validator, transport, health, logging robustness, bridge status, vehicle-restart recovery, cross-language end-to-end trace of real vehicle output | **143 / 143** |
| Python — tooling | LoRa airtime model pinned to published SX127x reference vectors | **49 / 49** |
| Python — simulations | Descent model against closed-form limits, ISA density, mass-tolerance argument | **40 / 40** |
| Python — post-flight analysis | Recovers a synthetic flight's known descent rate, drag coefficient, spin, drift and lost packet; the notebook executed cell by cell | **37 / 37** |
| Node — web console | Framing, parser, validator, link health, bridge status | **71 / 71** |
| Documented claims | Numbers in the documentation checked against the source that defines them | **306 / 306** |
| Pico syntax | 11 translation units against SDK stubs | All OK |

**Total: 6,131 automated checks.**

### What the tests prove

* The emitted packet matches the rulebook format **byte for byte**.
* The BMP280 compensation reproduces the **datasheet's own reference vector**.
* A boost before arming **cannot** trigger a launch.
* A hovering drone **cannot** be read as a landing.
* Invalid mandatory data suppresses a packet **without consuming its number**.
* `crc16_ccitt("123456789") == 0x29B1` — the standard known-answer vector.
* The vehicle and the bridge are proven to configure **the same radio modem**.
* Three independent parsers in three languages agree on **one fixture file**.

The same tests found **nine real defects in code that already built and passed** during the second review pass — a telemetry rate the radio could not have delivered, three parsers that disagreed, sensors that could not feed their own loop, an attitude filter wrong at the ±180° seam, a packet budget below the real packet, and two SPI drivers that had never executed.

## 13.2 Bring-up measurements

Every prediction was written down *before* the measurement was taken, and both are recorded side by side in `documentation/testing/bring-up-record.md` — 94 rows, of which 34 were taken at bring-up.

@@tab t-bringup | Predicted against measured@@

| Quantity | Predicted | **Measured** |
|---|---|---|
| Radio version register | `0x12` | **`0x12`** |
| Airtime, 206-byte packet, SF7/125 kHz | 328 ms | **333.7 ms** — +1.8 %, reproduced to 0.1 ms across four sessions |
| Gyro bias, per axis | within ±25 °/s | **X −3.30, Y +0.86, Z −0.06 °/s** |
| Barometer output rate | 83 Hz | **83.0 Hz** |
| GPS NMEA output | Clean sentences | **All six, 162 B/s, 0 checksum errors** |
| SD single block write | — | **2.678 ms mean, 4.9 ms typical worst, 29.8 ms occasional** |
| SD sustained rate | — | **~300 writes/s**, 3,672 in ten seconds |
| Rail under 45 transmits | Holds | **3.28 – 3.29 V** |
| Rail at 100 % write duty | Holds | **3.28 – 3.30 V** |
| Sensor read cost | Under 33 ms | **0.833 ms worst** |
| Altitude at rest after calibration | ≈ 0.0 m | **−0.5 m to +0.1 m** across 62 packets |
| First link | — | **66 packets, `P-001`–`P-066`, no gaps, no duplicates, 0 % loss, −44 dBm** |
| `MAX_RATE` at the station | ~3.13 Hz | **3.11 Hz**, 1 packet in 544 lost, RSSI −21 dBm, SNR 10.0 dB |

The airtime model survived contact with hardware to within 1.8 %. Chapter 14 adds a second column — what the flights measured — for the quantities that only flight can test.

## 13.3 The measurement that characterises the vehicle

**A 36.8-minute stationary log of 2,209 records** was taken as a characterisation of the attitude estimator. The first fifteen minutes were nearly perfect: **±0.8° total in yaw at 0.002 °/s.** The 36.8-minute log gives the vehicle's relative-yaw drift budget, and the pad calibration re-zeroes it at every power-up and again when the command window closes — so the yaw reported in flight is always fresh relative to the pad. Flight 1's post-landing session confirms the effect: yaw frozen to ±0.1° over 7.4 s after the calibration completed.

## 13.4 The documentation checker

`tools/check_doc_claims.py` has caught real errors repeatedly, including two during the writing of this report. A documentation set that cannot be checked drifts from the code within days; this one fails the build instead. It checks 306 claims, including the numbers in this report's source documents.
