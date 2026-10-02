# Avionics

The three onboard subsystems, each summarised against what has actually been measured.

**Status: 2026-10-02 — flown.** The vehicle board is built, every device on it answered, and it
flew inside the printed structure at the competition on 2026-09-30: two descents from a hand
throw off a terrace at about 29.5 m, recorded by the organizers' ground station (41 and 18
packets received, RSSI −109…−79 dBm, link margin at least 14 dB). The analysis is in
[`analysis/flight-2026-09-30/`](../analysis/flight-2026-09-30/README.md). The per-subsystem rows
below keep their dated bench records; each now carries a flight note.

| Subsystem | State | Detail |
|---|---|---|
| [Sensors](sensors/) | 🟢 **All four verified on the soldered board, and measured in flight** | IMU, barometer, GPS and microphone all produced flight data. One part is not what it was sold as |
| [Telemetry](telemetry/) | 🟢 **Link closed on the bench 2026-09-07** | Bench: 66 packets, no gaps, no duplicates, −44 dBm. **Flight 2026-09-30:** 102 distinct packets received by the organizers' station on `0xA5`, RSSI −109…−79 dBm |
| [Power](power/) | 🟢 **Rail measured; switch, power LED and divider fitted** | No regulator needed. The Schottky was not fitted, so USB and battery must never be connected together. **Flew** on the LiPo through two flights and a watchdog restart |

---

## What this directory is, and is not

Each subdirectory holds a **subsystem summary**: what the parts are, what has been measured
on them, what the firmware does with them, and what is still open. One page each, current
as of the date at the top.

**It is not the authority for any of it.** Every number here is quoted from somewhere that
owns it:

| Kind of fact | Owned by |
|---|---|
| Measurements taken on hardware | [bring-up-record.md](../documentation/testing/bring-up-record.md) |
| Pin assignment | [`BoardPins`](../firmware/flight-computer/include/flight/config.hpp) |
| Part identification and inspection | [receiving-inspection.md](../documentation/hardware/receiving-inspection.md) |
| Wire-level connections | [vehicle-netlist.tsv](../electrical/schematics/vehicle-netlist.tsv) |
| Wire format and radio parameters | [telemetry-protocol.md](../documentation/design/telemetry-protocol.md) |
| Requirement status | [requirements.md](../documentation/requirements/requirements.md) |

**When a summary here disagrees with one of those, the source wins and this page is the
bug.** These pages exist because "what is the state of the radio" is a question that
otherwise needs four documents to answer.

---

## The one thing to know about each

**Sensors — the IMU is not the part on the invoice.** It was sold as a nine-axis MPU-9250
and delivered as a six-axis MPU-6500: `WHO_AM_I` reads `0x70` and `0x0C` never answers.
There is no magnetometer, so yaw is a gyro integration with an arbitrary zero, declared
`YR-G` in every packet. It drifts, and it has been measured drifting **more than a full
revolution in a 36.8-minute stationary log**.

**Telemetry — the link worked in flight.** *Written 2026-09-14:* 66 packets end to end at
−44 dBm on the bench, nothing tested past a bench, `0xA5` never tried. *Update 2026-10-02:* the
organizers' station received the vehicle on `0xA5` at the competition — RSSI −109…−79 dBm, link
margin at least 14 dB (mean 31 dB) over the −123 dBm SF7 sensitivity, packets 118–188 bytes
against the 200-byte ceiling.

**Power — the regulator question resolved itself.** Every load runs from the Pico's own
`3V3(OUT)`, which held 3.28–3.29 V through 45 back-to-back transmits. The AMS1117 that
blocked the design for weeks turned out not to be needed. What is left is the battery end:
a switch, a diode and two resistors. The switch and the divider went in before submission; the
diode did not. The switch is a rocker ON/OFF on short leads outside the frame (not in the CAD
cut-out), with a power LED fitted. The vehicle flew on the battery.

---

Related: [documentation/README.md](../documentation/README.md) ·
[electrical/](../electrical/) · [mechanical/](../mechanical/) ·
[firmware/](../firmware/)
