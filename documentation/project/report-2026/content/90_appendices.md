@@chapter A | Appendices | Flight constants, the repository map, the complete flight dataset, references and a glossary.@@

## A.1 Flight configuration constants

From `firmware/flight-computer/src/pico/main.cpp` and `config.hpp`. Every value is validated at start-up by `validate_config()`, which refuses to run a configuration that cannot meet the rulebook.

@@tab t-constants | Flight configuration constants@@

| Constant | Value | Note |
|---|---:|---|
| `team_id` | `CAN-Team-25` | The formatter refuses the rulebook's `CAN-Team-XX` placeholder |
| `loop_tick_ms` | 2 ms | Bounded twice: scheduling jitter, and draining the GPS UART before its FIFO fills |
| `sensor_period_ms` | 33 ms | 30 Hz attitude and altitude-rate update |
| `telemetry_period_ms` | 700 ms | **1.43 Hz.** Hard ceiling 950 ms, enforced three ways |
| `sd_flush_period_ms` | 2000 ms | Appends happen per packet; this is the sync |
| Watchdog | 2000 ms | A hung loop restarts; telemetry resumes automatically |
| `calib_samples` | 80 | ~2.7 s at 30 Hz |
| `calib_timeout_ms` | 20 000 ms | Then resolve best-effort |
| `arming_delay_ms` | 3000 ms | **and** calibration must have settled |
| `launch_confirm_ms` | 300 ms | Launch condition must hold this long |
| `launch_altitude_gain_m` | 15 m | Or acceleration above 30 m/s² |
| `min_flight_ms` | 3000 ms | Landing detection suppressed until this into flight |
| `landing_descent_rate_mps` | −2 m/s | The descent gate |
| `landing_descent_confirm_ms` | 1000 ms | Held this long before the gate opens |
| `landing_confirm_ms` | 3000 ms | At-rest condition must hold this long |
| `post_impact_transmission_ms` | 5000 ms | ≥ the rulebook's 5 s; a shorter value will not build |
| `sensor_stale_after_ms` | 2000 ms | Time-based, not attempt-based |
| `sd_max_failures` | 10 | Consecutive write failures before logging disables itself |
| `radio_recovery_backoff_ms` | 1000 ms | Bounded re-init, never a blocking retry loop |
| `battery_divider_ratio` | 2.0 | 33 kΩ / 33 kΩ into GP26 |
| `battery_low_voltage` | 3.5 V | Raises a warning |
| `command_window_ms` | 300 000 ms | Five minutes from power-on, pre-arm only |
| `auto_max_rate` | true | Max rate when the window closes, and after a watchdog reset |

## A.2 Repository map

**Repository:** [github.com/KunjSorathiya/CanSat-Team-Singularity](https://github.com/KunjSorathiya/CanSat-Team-Singularity)

```text
firmware/
  common/              shared telemetry format + SX1278 driver     (cansat::)
  flight-computer/     flight core + Pico HAL + tests              (flight::)
  ground-station/      bridge firmware + USB CRC framing           (ground::)
ground-station/
  software/            Python receive pipeline + tests
  web/                 single-file browser telemetry console
avionics/              per-subsystem summaries against what was measured
electrical/
  schematics/          machine-readable netlist, generated from the firmware
mechanical/            envelope, mass budget, canopy spec, CAD (STEP, F3D), stress studies
simulations/           descent model + tests
analysis/
  flight-2026-09-30/   launch-day analysis: parser, cleaning, statistics, figures, dataset
tools/                 host build, Pico syntax check, LoRa link-budget calculator,
                       netlist and drawing generators, documentation-claim checker,
                       SD-card and flight-log utilities, report figures, SDK stubs
test-data/             shared fixtures the C++, Python and JavaScript parsers all read
documentation/
  requirements/        rulebook, requirement checklist
  mission/             concept of operations
  design/              architecture, protocol, wiring, electrical, link budget
  hardware/            BOM, inspection, assembly, compatibility, GPIO map, datasheets, photos
  project/             timeline, this report and its build (report-2026/)
  testing/             test plan and the bring-up measurement record
  operations/          runbook and launch-day procedure
```

Supporting materials the rulebook asks to be attached or referenced: **schematics and netlist** (`electrical/schematics/`), **wiring diagrams and board layout** (`documentation/hardware/diagrams/`), **CAD** (`mechanical/CAD/Cansat_D1.step`, `.f3d`), **structural studies** (`mechanical/simulation/`), **firmware and ground software** (`firmware/`, `ground-station/`), **the raw flight log and its analysis** (`analysis/flight-2026-09-30/`).

## A.3 The complete flight dataset

All 102 distinct packets from the organizers' export, in vehicle order within each session. **S0** pad capture · **F1** Flight 1 · **G1** after landing · **F2** Flight 2. `A` is the altitude as transmitted; `h` is the temperature-corrected height above that power cycle's baseline; `Pr` in Pa; `T` in °C; angles in degrees; acceleration in m/s²; `SN` in mV p-p; `ST` the status field; RSSI in dBm and SNR in dB are the receiving station's measurements. GPS coordinates are in `flight_data_clean.csv`.

<div class="datatab">

| Ses | P | Ti (s) | A | h | Pr | T | Ro | Pi | Ya | AX | AY | AZ | SN | ST | RSSI | SNR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| S0 | 420 | 293.300 | -0.7 | -0.7 | 101200.16 | 31.5 | -52.6 | -27.1 | 123.1 | 4.40 | -7.00 | 5.42 | 14.5 | R003 | -105 | -6.50 |
| S0 | 421 | 294.001 | -0.7 | -0.7 | 101200.16 | 31.5 | -51.2 | -24.6 | 121.7 | 4.21 | -6.97 | 5.59 | 4.8 | R003 | -105 | -6.75 |
| F1 | 1585 | 672.929 | 27.6 | 29.2 | 100884.95 | 31.4 | 62.2 | 16.0 | 153.1 | -2.66 | 10.51 | 4.48 | 10.5 | F111 | -94 | 9.00 |
| F1 | 1586 | 673.305 | 27.7 | 29.2 | 100884.28 | 31.4 | 88.5 | 20.3 | 175.4 | -3.82 | 10.03 | 1.37 |  |  | -95 | 9.00 |
| F1 | 1587 | 673.601 | 27.7 | 29.2 | 100884.28 | 31.4 | 92.9 | 9.4 | 166.2 | -1.31 | 9.51 | 0.11 |  |  | -96 | 9.25 |
| F1 | 1588 | 673.898 | 27.7 | 29.3 | 100883.60 | 31.4 | 101.9 | 4.1 | 150.0 | -1.91 | 10.53 | -0.84 | 24.2 | F111 | -101 | 7.50 |
| F1 | 1589 | 674.272 | 27.8 | 29.4 | 100882.25 | 31.4 | 115.0 | -0.0 | 121.8 | -0.63 | 8.26 | -5.14 |  |  | -109 | 1.50 |
| F1 | 1590 | 674.569 | 27.9 | 29.5 | 100881.57 | 31.4 | 120.4 | -1.4 | 102.7 | 0.07 | 8.34 | -5.43 |  |  | -105 | 4.25 |
| F1 | 1591 | 674.865 | 27.8 | 29.4 | 100882.43 | 31.4 | 116.8 | -6.3 | 92.6 | 1.78 | 8.85 | -4.51 | 16.1 | F111 | -107 | 3.75 |
| F1 | 1592 | 675.239 | 27.8 | 29.4 | 100882.92 | 31.4 | 117.3 | -7.8 | 89.8 | 1.34 | 8.67 | -4.50 |  |  | -106 | 4.50 |
| F1 | 1593 | 675.536 | 27.8 | 29.4 | 100882.92 | 31.4 | 115.1 | -9.3 | 87.6 | 1.68 | 9.10 | -3.76 |  |  | -104 | 6.00 |
| F1 | 1594 | 675.832 | 27.8 | 29.4 | 100883.11 | 31.4 | 118.2 | -9.3 | 85.3 | 1.32 | 8.57 | -4.79 | 12.9 | F111 | -104 | 6.25 |
| F1 | 1595 | 676.208 | 27.9 | 29.5 | 100881.57 | 31.4 | 118.4 | -11.5 | 83.9 | 2.05 | 8.34 | -4.62 |  |  | -104 | 6.00 |
| F1 | 1596 | 676.505 | 27.9 | 29.5 | 100881.76 | 31.4 | 115.7 | -11.8 | 84.2 | 2.21 | 8.86 | -3.79 |  |  | -104 | 6.00 |
| F1 | 1597 | 676.801 | 27.9 | 29.5 | 100881.76 | 31.4 | 117.3 | -9.9 | 82.4 | 1.54 | 8.86 | -4.27 | 10.5 | F111 | -103 | 6.50 |
| F1 | 1598 | 677.176 | 27.7 | 29.3 | 100883.29 | 31.4 | 124.1 | -3.8 | 79.0 | -0.18 | 8.37 | -6.78 |  |  | -103 | 6.50 |
| F1 | 1599 | 677.472 | 28.6 | 30.3 | 100872.48 | 31.4 | 104.6 | -16.8 | 111.5 | -27.48 | -13.36 | -40.54 |  |  | -88 | 9.50 |
| F1 | 1600 | 677.768 | 29.1 | 30.7 | 100867.57 | 31.4 | 110.6 | 28.5 | 135.3 | 0.54 | 1.79 | 4.56 | 36.3 | F111 | -90 | 9.00 |
| F1 | 1601 | 678.142 | 28.0 | 29.6 | 100880.22 | 31.4 | 10.6 | 9.9 | 42.7 | 0.21 | 1.11 | 6.47 |  |  | -96 | 8.50 |
| F1 | 1602 | 678.439 | 26.7 | 28.3 | 100895.39 | 31.4 | 10.3 | 7.7 | -24.4 | -0.58 | 0.82 | 11.53 |  |  | -84 | 10.00 |
| F1 | 1603 | 678.735 | 24.1 | 25.5 | 100926.96 | 31.4 | 7.4 | -1.6 | 149.6 | 8.41 | -3.45 | 18.27 | 16.1 | F111 | -94 | 9.25 |
| F1 | 1604 | 679.111 | 22.9 | 24.2 | 100940.97 | 31.4 | 5.7 | -10.5 | -101.0 | 2.46 | 0.04 | 7.56 |  |  | -86 | 9.50 |
| F1 | 1605 | 679.409 | 22.4 | 23.7 | 100947.54 | 31.4 | -23.7 | 9.3 | -170.0 | 2.56 | 1.16 | 18.05 |  |  | -81 | 9.50 |
| F1 | 1606 | 679.706 | 21.8 | 23.0 | 100954.79 | 31.4 | -33.9 | 10.9 | -175.3 | 1.28 | 0.43 | 9.79 | 10.5 | F111 | -79 | 9.75 |
| F1 | 1607 | 680.081 | 21.4 | 22.7 | 100958.84 | 31.4 | 5.1 | 8.6 | -130.7 | 0.72 | 0.40 | 9.35 |  |  | -87 | 9.50 |
| F1 | 1608 | 680.379 | 20.8 | 22.0 | 100966.46 | 31.4 | -18.8 | -13.7 | -37.2 | 2.33 | -0.32 | 14.60 |  |  | -93 | 9.25 |
| F1 | 1609 | 680.675 | 20.2 | 21.4 | 100973.21 | 31.4 | 39.4 | 14.9 | 141.0 | 2.07 | 0.69 | 8.30 | 19.3 | F111 | -89 | 9.75 |
| F1 | 1610 | 681.050 | 19.8 | 20.9 | 100978.44 | 31.4 | -0.7 | -6.0 | -152.2 | 0.60 | 0.57 | 7.86 |  |  | -83 | 9.50 |
| F1 | 1611 | 681.347 | 19.0 | 20.1 | 100987.74 | 31.4 | -25.6 | 8.9 | 131.9 | -0.95 | -0.60 | 8.25 |  |  | -86 | 9.50 |
| F1 | 1612 | 681.643 | 18.3 | 19.3 | 100996.68 | 31.4 | 16.2 | -15.8 | 73.8 | -1.17 | 0.49 | 6.55 | 24.2 | F111 | -86 | 9.50 |
| F1 | 1613 | 682.017 | 17.7 | 18.7 | 101003.43 | 31.4 | 10.6 | -0.8 | 130.8 | -0.15 | 1.09 | 11.12 |  |  | -87 | 9.75 |
| F1 | 1614 | 682.314 | 17.0 | 18.0 | 101011.39 | 31.4 | 34.7 | 4.5 | 137.8 | -0.45 | 2.32 | 12.60 |  |  | -96 | 9.25 |
| F1 | 1615 | 682.610 | 16.3 | 17.2 | 101020.32 | 31.4 | -10.0 | 24.5 | 36.3 | 0.82 | -0.05 | 8.43 | 12.1 | F111 | -87 | 9.75 |
| F1 | 1616 | 682.984 | 15.6 | 16.5 | 101028.28 | 31.4 | 3.6 | -20.7 | -10.2 | 0.86 | 0.13 | 11.28 |  |  | -90 | 10.00 |
| F1 | 1617 | 683.281 | 14.7 | 15.5 | 101039.77 | 31.4 | -21.7 | -12.5 | 95.5 | 2.35 | -0.33 | 12.53 |  |  | -88 | 9.25 |
| F1 | 1618 | 683.578 | 13.8 | 14.6 | 101050.58 | 31.4 | 5.5 | 15.5 | -137.4 | 0.38 | 1.68 | 5.43 | 26.6 | F111 | -89 | 9.25 |
| F1 | 1619 | 683.953 | 13.1 | 13.9 | 101058.69 | 31.4 | 6.6 | -2.1 | -160.3 | 0.02 | 0.79 | 10.46 |  |  | -92 | 9.75 |
| F1 | 1620 | 684.249 | 12.2 | 12.9 | 101068.98 | 31.4 | 11.0 | 3.1 | 128.2 | -0.37 | -0.39 | 10.36 |  |  | -90 | 10.00 |
| F1 | 1621 | 684.545 | 11.4 | 12.0 | 101079.11 | 31.4 | 10.8 | 1.1 | 125.6 | -0.03 | 0.42 | 10.39 | 9.7 | F113 | -93 | 9.75 |
| F1 | 1622 | 684.920 | 10.4 | 11.0 | 101091.27 | 31.4 | 7.3 | 12.9 | 167.6 | -0.88 | -0.18 | 16.18 |  |  | -83 | 9.75 |
| F1 | 1623 | 685.216 | 9.8 | 10.3 | 101098.55 | 31.4 | -7.3 | -17.9 | 177.6 | 1.18 | -0.29 | 1.70 |  |  | -90 | 9.75 |
| F1 | 1624 | 685.514 | 9.7 | 10.2 | 101099.90 | 31.4 | 57.9 | 60.4 | 153.2 | 0.90 | -0.06 | 0.28 | 4.8 | F113 | -91 | 9.25 |
| F1 | 1625 | 685.889 | 9.1 | 9.7 | 101106.14 | 31.4 | 52.5 | 32.3 | -125.7 | -0.60 | 3.27 | 14.08 |  |  | -94 | 9.25 |
| G1 | 1 | 0.000 | 16.8 | -0.1 | 101123.18 | 31.4 | 29.8 | 5.8 | -0.0 | -0.99 | 4.87 | 8.50 | 10.5 | R004 | -90 | 9.00 |
| G1 | 2 | 0.375 | 17.0 | 0.0 | 101121.15 | 31.4 | 29.6 | 6.7 | -0.2 | -1.08 | 4.95 | 8.34 |  |  | -89 | 9.50 |
| G1 | 3 | 0.672 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.4 | 6.8 | -0.1 | -1.12 | 4.97 | 8.37 |  |  | -87 | 9.50 |
| G1 | 4 | 0.968 | 17.0 | 0.0 | 101121.52 | 31.4 | 29.3 | 6.9 | 0.1 | -1.14 | 4.98 | 8.36 | 11.3 | R004 | -87 | 9.25 |
| G1 | 5 | 1.342 | 17.0 | 0.1 | 101120.85 | 31.4 | 29.2 | 7.0 | 0.3 | -1.13 | 4.98 | 8.38 |  |  | -88 | 9.75 |
| G1 | 6 | 1.638 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.2 | 7.0 | 0.5 | -1.13 | 4.98 | 8.37 |  |  | -90 | 9.50 |
| G1 | 7 | 1.935 | 16.9 | -0.0 | 101122.02 | 31.4 | 29.2 | 7.0 | 0.7 | -1.13 | 4.98 | 8.37 | 6.4 | R004 | -88 | 9.50 |
| G1 | 8 | 2.309 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.2 | 7.0 | 0.9 | -1.12 | 4.97 | 8.37 |  |  | -89 | 9.75 |
| G1 | 9 | 2.605 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.2 | 7.0 | 1.1 | -1.13 | 4.98 | 8.36 |  |  | -89 | 9.50 |
| G1 | 10 | 2.902 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.2 | 7.0 | 1.3 | -1.13 | 4.98 | 8.37 | 24.2 | R004 | -89 | 9.00 |
| G1 | 11 | 3.276 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.2 | 7.0 | 1.6 | -1.13 | 4.98 | 8.37 |  |  | -86 | 9.25 |
| G1 | 12 | 3.573 | 16.9 | -0.1 | 101122.20 | 31.4 | 29.2 | 7.0 | 1.8 | -1.14 | 4.99 | 8.39 |  |  | -87 | 9.50 |
| G1 | 13 | 3.869 | 16.9 | -0.1 | 101122.20 | 31.4 | 29.3 | 7.0 | 2.0 | -1.12 | 4.98 | 8.38 | 6.4 | R004 | -88 | 9.75 |
| G1 | 14 | 4.243 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.3 | 7.0 | 2.3 | -1.13 | 4.98 | 8.37 |  |  | -89 | 9.00 |
| G1 | 15 | 4.539 | 17.0 | 0.1 | 101120.66 | 31.4 | 29.3 | 7.0 | 2.5 | -1.13 | 4.99 | 8.37 |  |  | -90 | 10.00 |
| G1 | 16 | 4.836 | 17.0 | 0.0 | 101121.34 | 31.4 | 29.3 | 7.0 | 2.7 | -1.13 | 4.98 | 8.37 | 5.6 | R004 | -89 | 10.75 |
| G1 | 17 | 5.211 | 17.0 | 0.0 | 101121.52 | 31.4 | 29.3 | 7.0 | 2.9 | -1.13 | 4.98 | 8.38 |  |  | -89 | 9.25 |
| G1 | 18 | 5.507 | -0.1 | -0.1 | 101122.20 | 31.4 | 30.7 | 6.6 | -0.0 | -1.12 | 4.97 | 8.36 |  |  | -88 | 9.75 |
| G1 | 19 | 5.804 | 0.0 | 0.1 | 101120.85 | 31.4 | 30.7 | 6.6 | -0.0 | -1.13 | 4.99 | 8.41 | 12.1 | R113 | -88 | 9.50 |
| G1 | 20 | 6.178 | -0.0 | 0.0 | 101121.52 | 31.4 | 30.7 | 6.6 | -0.0 | -1.14 | 4.98 | 8.39 |  |  | -88 | 9.50 |
| G1 | 21 | 6.475 | 0.0 | 0.0 | 101121.00 | 31.4 | 30.7 | 6.6 | 0.0 | -1.13 | 4.99 | 8.37 |  |  | -88 | 10.25 |
| G1 | 22 | 6.772 | 0.1 | 0.1 | 101120.32 | 31.4 | 30.7 | 6.6 | 0.0 | -1.13 | 4.98 | 8.37 | 7.3 | R113 | -88 | 10.50 |
| G1 | 23 | 7.146 | -0.1 | -0.1 | 101122.35 | 31.4 | 30.7 | 6.6 | 0.0 | -1.13 | 4.98 | 8.36 |  |  | -88 | 9.75 |
| G1 | 24 | 7.442 | 0.0 | 0.0 | 101121.00 | 31.4 | 30.7 | 6.6 | 0.0 | -1.14 | 4.98 | 8.40 |  |  | -88 | 9.50 |
| G1 | 25 | 7.739 | -0.0 | -0.0 | 101121.68 | 31.4 | 30.7 | 6.6 | 0.0 | -1.14 | 4.97 | 8.36 | 13.7 | R113 | -88 | 9.50 |
| G1 | 26 | 8.113 | -0.0 | 0.0 | 101121.52 | 31.4 | 30.7 | 6.7 | 0.0 | -1.14 | 4.98 | 8.39 |  |  | -88 | 10.00 |
| G1 | 27 | 8.409 | -0.1 | -0.1 | 101123.03 | 31.4 | 30.7 | 6.6 | 0.0 | -1.13 | 4.97 | 8.38 |  |  | -88 | 9.75 |
| G1 | 28 | 8.706 | -0.2 | -0.1 | 101123.21 | 31.4 | 30.7 | 6.6 | 0.0 | -1.13 | 4.98 | 8.38 | 6.4 | R113 | -88 | 10.00 |
| G1 | 29 | 9.080 | -0.2 | -0.1 | 101123.21 | 31.4 | 30.7 | 6.6 | 0.0 | -1.13 | 4.99 | 8.37 |  |  | -88 | 9.50 |
| G1 | 30 | 9.376 | -0.1 | -0.1 | 101122.54 | 31.4 | 30.7 | 6.6 | 0.0 | -1.12 | 4.98 | 8.39 |  |  | -88 | 9.75 |
| G1 | 31 | 9.673 | -0.0 | -0.0 | 101121.86 | 31.4 | 30.7 | 6.7 | 0.0 | -1.13 | 4.97 | 8.37 | 5.6 | R113 | -88 | 10.50 |
| G1 | 32 | 10.048 | -0.0 | -0.0 | 101121.86 | 31.4 | 30.8 | 6.7 | 0.0 | -1.14 | 4.98 | 8.36 |  |  | -88 | 9.25 |
| G1 | 33 | 10.344 | -0.0 | -0.0 | 101121.86 | 31.4 | 30.8 | 6.7 | 0.0 | -1.13 | 4.97 | 8.36 |  |  | -88 | 9.50 |
| G1 | 34 | 10.640 | -0.2 | -0.2 | 101123.40 | 31.4 | 30.7 | 6.7 | 0.0 | -1.14 | 4.98 | 8.38 | 5.6 | R113 | -88 | 9.75 |
| G1 | 35 | 11.015 | -0.0 | -0.0 | 101121.86 | 31.4 | 30.8 | 6.6 | 0.1 | -1.14 | 5.00 | 8.38 |  |  | -88 | 9.75 |
| G1 | 36 | 11.311 | -0.1 | -0.1 | 101122.72 | 31.4 | 30.8 | 6.7 | 0.1 | -1.16 | 4.98 | 8.37 |  |  | -88 | 9.25 |
| G1 | 37 | 11.608 | 0.0 | 0.0 | 101121.38 | 31.4 | 30.8 | 6.7 | 0.1 | -1.14 | 4.97 | 8.39 | 13.7 | R113 | -88 | 10.25 |
| G1 | 38 | 11.984 | 0.2 | 0.2 | 101119.16 | 31.4 | 30.8 | 6.7 | 0.1 | -1.14 | 4.99 | 8.39 |  |  | -89 | 9.25 |
| G1 | 39 | 12.280 | 0.2 | 0.2 | 101119.16 | 31.4 | 30.8 | 6.7 | 0.1 | -1.13 | 4.98 | 8.39 |  |  | -88 | 9.75 |
| G1 | 40 | 12.578 | 0.1 | 0.1 | 101120.70 | 31.4 | 30.8 | 6.7 | 0.1 | -1.14 | 4.97 | 8.35 | 6.4 | R113 | -88 | 10.25 |
| G1 | 41 | 12.953 | 0.1 | 0.1 | 101120.70 | 31.4 | 30.8 | 6.7 | 0.1 | -1.15 | 4.98 | 8.38 |  |  | -90 | 10.00 |
| F2 | 148 | 102.901 | 1.0 | 1.1 | 100899.29 | 31.1 | 47.7 | -18.1 | 29.6 | -1.98 | -0.58 | 7.30 | 15.3 | R003 | -87 | 9.50 |
| F2 | 149 | 103.600 | -1.0 | -1.1 | 100923.45 | 31.1 | -3.3 | -36.4 | -59.3 | 2.32 | 1.77 | 6.45 | 16.1 | R003 | -90 | 8.50 |
| F2 | 150 | 104.301 | -2.3 | -2.4 | 100938.98 | 31.1 | 2.8 | -18.8 | 83.0 | 0.70 | 4.44 | 18.42 | 16.9 | R003 | -92 | 9.00 |
| F2 | 151 | 105.000 | -3.7 | -4.0 | 100956.35 | 31.1 | 11.9 | -0.2 | 153.0 | -1.37 | -2.67 | 13.13 | 19.3 | R003 | -89 | 10.00 |
| F2 | 152 | 105.704 | -4.6 | -4.8 | 100966.48 | 31.1 | 20.9 | -17.3 | -155.0 | 0.49 | 1.78 | 5.29 | 11.3 | R003 | -94 | 8.75 |
| F2 | 153 | 106.401 | -5.7 | -6.0 | 100979.80 | 31.1 | -39.8 | 16.6 | -169.4 | 0.45 | 1.10 | 8.83 | 8.9 | R003 | -98 | 7.75 |
| F2 | 154 | 107.101 | -7.1 | -7.5 | 100996.50 | 31.1 | 34.9 | 10.5 | -176.1 | -1.16 | 1.01 | 14.11 | 5.6 | R003 | -97 | 8.00 |
| F2 | 155 | 107.801 | -8.3 | -8.8 | 101010.87 | 31.1 | -6.3 | -12.3 | 119.4 | 1.71 | 0.00 | 17.11 | 12.9 | R003 | -100 | 5.50 |
| F2 | 156 | 108.501 | -9.5 | -10.0 | 101025.05 | 31.1 | -12.3 | 26.2 | -143.5 | -1.41 | 1.12 | 8.03 | 36.3 | R003 | -100 | 6.00 |
| F2 | 157 | 109.202 | -10.5 | -11.1 | 101037.02 | 31.1 | 48.5 | 12.2 | 149.0 | -0.08 | 1.42 | 8.54 | 25.8 | R003 | -93 | 9.00 |
| F2 | 158 | 109.901 | -11.7 | -12.4 | 101052.07 | 31.1 | -18.1 | -28.6 | 95.8 | 1.09 | -1.67 | 12.10 | 21.8 | R003 | -94 | 8.75 |
| F2 | 162 | 112.700 | -16.5 | -17.5 | 101109.96 | 31.1 | 11.1 | -2.9 | -128.0 | -0.07 | 3.40 | 15.08 | 19.3 | R003 | -98 | 6.75 |
| F2 | 163 | 113.400 | -17.9 | -18.9 | 101126.17 | 31.1 | -27.7 | -8.7 | -37.5 | 0.18 | -1.44 | 5.55 | 16.1 | R003 | -97 | 7.50 |
| F2 | 164 | 114.100 | -19.6 | -20.7 | 101146.43 | 31.1 | -17.7 | 35.4 | 176.8 | 0.92 | 1.07 | 7.26 | 12.9 | R003 | -106 | 0.00 |
| F2 | 166 | 115.501 | -22.4 | -23.7 | 101179.86 | 31.1 | 4.4 | 11.0 | 136.5 | 1.81 | 3.50 | 17.07 | 11.3 | R003 | -100 | 6.00 |
| F2 | 169 | 117.600 | -26.3 | -27.8 | 101227.13 | 31.1 | 44.1 | -8.1 | -7.0 | 0.54 | 6.21 | 5.92 | 33.0 | R003 | -97 | 7.50 |
| F2 | 170 | 118.301 | -26.9 | -28.4 | 101234.08 | 31.1 | -3.6 | 37.0 | 147.2 | -2.87 | -3.22 | 8.27 | 13.7 | R003 | -101 | 5.00 |
| F2 | 171 | 119.003 | -26.9 | -28.5 | 101234.75 | 31.1 | 9.0 | 49.7 | -70.8 | -8.12 | 3.42 | 12.67 | 16.1 | R003 | -105 | 0.75 |

</div>

## A.4 References

1. SVNIT Physics Club, *CanSat Competition 2026 Rulebook — Judging & Evaluation* (2026 revision).
2. Raspberry Pi Ltd, *RP2040 Datasheet* and *Raspberry Pi Pico Datasheet*.
3. Bosch Sensortec, *BMP280 Digital Pressure Sensor*, data sheet BST-BMP280-DS001.
4. InvenSense / TDK, *MPU-6500 Product Specification* and *MPU-6500 Register Map and Descriptions*.
5. Semtech, *SX1276/77/78/79 — Low Power Long Range Transceiver* data sheet (rev. 7), including §4.1.1.7 on time on air.
6. Semtech, *AN1200.13 — LoRa Modem Designer's Guide*.
7. u-blox, *NEO-6 series data sheet* and *u-blox 6 Receiver Description*; *NMEA 0183* sentence formats.
8. Texas Instruments, *LM393 dual differential comparator* data sheet.
9. SD Association, *SD Specifications Part 1: Physical Layer Simplified Specification*.
10. Microsoft, *FAT32 File System Specification*.
11. ITU-T Recommendation V.41 (CRC-16/CCITT).
12. R. Mahony, T. Hamel and J.-M. Pflimlin, “Nonlinear complementary filters on the special orthogonal group,” *IEEE Transactions on Automatic Control* 53(5), 2008, pp. 1203–1218.
13. T. W. Knacke, *Parachute Recovery Systems Design Manual*, NWC TP 6575, Naval Weapons Center, 1992.
14. NOAA, NASA and USAF, *U.S. Standard Atmosphere, 1976*.
15. S. Maurice et al., “In situ recording of Mars soundscape,” *Nature* 605, 653–658 (2022).
16. M. Fulchignoni et al., “In situ measurements of the physical characteristics of Titan's environment,” *Nature* 438, 785–791 (2005).
17. Autodesk, *Fusion 360 — Simulation, Static Stress* documentation.
18. Software used for the analysis and this report: Python, NumPy, SciPy, pandas, Matplotlib, Python-Markdown, Pygments, Graphviz, and Chromium for PDF output. Typefaces: Inter, Space Grotesk and JetBrains Mono (SIL Open Font License).

## A.5 Glossary

| Term | Meaning |
|---|---|
| **AGL** | Altitude above ground level — here, above the pad baseline of the current power cycle |
| **Armed** | The vehicle has completed its arming delay and calibration, so launch detection is live (`ST-R11x`) |
| **BMP280** | Bosch barometric pressure and temperature sensor |
| **C<sub>d</sub>·S** | Drag coefficient times reference area: the drag area of the descending vehicle |
| **Command window** | The first five minutes after power-on, during which the vehicle listens between packets and has not yet armed |
| **CRC** | Cyclic redundancy check; here CRC-16/CCITT-FALSE on the USB link and the LoRa payload |
| **Descent gate** | The rule that a vehicle cannot be declared landed until it has been observed descending |
| **EWMA** | Exponentially weighted moving average |
| **FSPL** | Free-space path loss |
| **HDOP** | Horizontal dilution of precision, a GPS fix-quality figure |
| **Hypsometric equation** | Δh = (R T / g) ln(p₀/p): height from a pressure ratio at a given air temperature |
| **IMU** | Inertial measurement unit: accelerometer and gyroscope |
| **ISA** | International Standard Atmosphere (15 °C at sea level) |
| **Lean / rich packet** | Mandatory-fields-only packet / packet that also carries GPS, sound and status |
| **LoRa** | A chirp-spread-spectrum radio modulation |
| **Max rate** | The 3.11 Hz three-slot transmit pattern the vehicle adopts when the command window closes |
| **RSSI / SNR** | Received signal strength (dBm) and signal-to-noise ratio (dB) measured by the receiving radio |
| **SF** | LoRa spreading factor |
| **Specific force** | What an accelerometer measures: 1 g at rest, 0 in free fall |
| **ST-** | The status field: state letter, armed, calibrated, active-fault count |
| **Swing angle** | The angle between the vehicle's z axis and the measured specific force |
| **Watchdog** | A hardware timer that restarts the flight computer if the loop stops feeding it |
