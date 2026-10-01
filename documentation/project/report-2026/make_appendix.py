"""Writes content/90_appendices.md: constants, repository map, the complete flight dataset
(generated from flight_data_clean.csv), references and glossary."""
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
d = pd.read_csv(HERE.parents[2] / "analysis/flight-2026-09-30/flight_data_clean.csv")
names = {"F1": "F1", "G1": "G1", "F2": "F2", "S0": "S0"}
order = ["S0", "F1", "G1", "F2"]
rows = []
for nm in order:
    g = d[d.name == nm].sort_values("ti")
    for _, r in g.iterrows():
        f = lambda v, k: "" if pd.isna(v) else f"{v:.{k}f}"
        rows.append(f"| {nm} | {int(r.P)} | {r.ti:.3f} | {r.A:.1f} | {r.h_base:.1f} | {r.Pr:.2f} | {r['T']:.1f} | {r.Ro:.1f} | {r.Pi:.1f} | {r.Ya:.1f} | {r.AX:.2f} | {r.AY:.2f} | {r.AZ:.2f} | {f(r.SN,1)} | {'' if pd.isna(r.ST) else r.ST} | {r.rssi:.0f} | {r.snr:.2f} |")
tbl = "\n".join(rows)
txt = f'''@@chapter A | Appendices | Flight constants, the repository map, the complete flight dataset, references and a glossary.@@

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
{tbl}

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
'''
(HERE / "content" / "90_appendices.md").write_text(txt)
print("ok", len(txt))
