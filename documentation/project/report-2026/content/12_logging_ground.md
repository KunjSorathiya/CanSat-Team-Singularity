@@chapter 12 | Onboard logging and the ground station | The card that keeps what the radio can lose, and the three-language pipeline that turns packets into data.@@

## 12.1 Onboard logging

The onboard log writes into **raw 512-byte blocks with no filesystem**, rewriting its header after every record. A brownout or an impact reset therefore resumes at the correct block instead of overwriting flight data.

@@fig f-sd | d13_sd_layout.png | The raw-block log layout. Two header copies alternate, each with a sequence number and checksum. | 100%@@

**The log writes one row per telemetry packet**, appended in `Controller::emit_telemetry()` as the packet goes on the air, so it runs at the radio's cadence — 3.11 Hz in flight — not at the 30 Hz sensor rate. Each row carries the packet text plus the satellite count, HDOP and full-precision position that never go on the air, the sound gate percentage, and the fault total.

<div class="callout why"><div class="ct">Why raw blocks, and why two headers</div>

* **No filesystem to corrupt.** A FAT volume updates a directory entry and an allocation table on every extension; an impact or brownout between those writes can leave a card that mounts as empty. A raw block log has nothing to be inconsistent with.
* **The header is rewritten after *every* record**, so power can fail during a header write. With a single header there would then be no valid resume point and the next boot would restart at the first record block and **overwrite the entire flight it had just recorded.** With two alternating copies, each carrying a sequence number and a checksum, only the copy being written can be damaged; the other still holds the previous complete resume point. A test destroys each copy in turn and checks that the log resumes with its records intact.
* **A full region stops writing rather than wrapping**, so older data is never silently overwritten.
* **A file in a few pieces is not a fault.** The firmware maps log block numbers through an extent list of up to 16 runs; `tools/prepare_sd_card.py` creates and sizes the file and `tools/inspect_sd_log.py` reports its layout.

</div>

The SD log is the complete record: it holds every packet the radio sent, and every column the packet leaves out. The post-flight analysis reads it with `tools/read_flight_log.py`, which splits it by power cycle and stops exactly where the data stops.

## 12.2 Ground station

Three interfaces over one pipeline:

@@tab t-ground | Ground-station interfaces@@

| Interface | Use |
|---|---|
| **Web console** — `ground-station/web/index.html` | Single file, no build, no dependencies. Demo replay, file replay, or live Web Serial straight from the bridge |
| **Tk dashboard** — `python src/main.py live --port COM5 --framed` | Live numeric view, with plots when matplotlib is installed |
| **CLI replay** — `python src/main.py replay … --export out.csv` | Offline parse, validate, log and export |

@@fig f-pipeline | d10_ground_pipeline.png | The receive pipeline. Each stage counts its rejections separately, so a transport fault is never mistaken for a sensor fault. | 100%@@

The bridge firmware is a pure bridge: the SX1278 sits in continuous receive and every received payload is framed onto USB serial as `$<len>,<crc16>,<payload>\n`, with a CRC-16/CCITT-FALSE (polynomial `0x1021`, initial value `0xFFFF`) over the raw payload. It emits a status line at 1 Hz with its own frame and drop counters, re-initialises the radio after 20 consecutive unhealthy polls and runs a 3 s watchdog so a hung bridge reboots and the PC reconnects by itself.

<div class="callout why"><div class="ct">Design decisions in the ground station</div>

* **A CRC on the USB link** separates *transport* corruption from a *malformed packet* — the two need different reactions and look identical without it. The known-answer vector `crc16_ccitt("123456789") == 0x29B1` is asserted in the C++ and Python suites.
* **Three implementations, one fixture file.** The framing and the packet parser exist in C++, Python and JavaScript. They are held to a single shared set of test vectors so they cannot drift, which would otherwise fail silently and totally.
* **Nothing received is ever discarded.** Malformed packets, CRC failures and rejected packets all reach the raw log with their receipt time and the reason.
* **The pipeline runs on a background thread** and hands the interface a snapshot through a bounded queue; when the queue fills, the oldest event is dropped rather than blocking reception, so a slow display can never stall logging.
* **The bridge agreed with the packet stream exactly** on the first closed link: the frame counter incremented once per packet with zero drops — which is how it is known that the radio delivered everything it heard and USB carried everything the radio delivered.

</div>

The validator checks team identity, sequence continuity, duplicates, timestamp monotonicity and GPS plausibility; link health is a 5 s sliding window of rate, loss percentage and staleness, and it reports whether the rate that *arrived* cleared 1 Hz — a different question from what the vehicle transmitted.

**The vehicle-restart case is handled by design:** when the packet counter restarts at `P-001` the ground station recognises a vehicle restart and keeps counting cleanly — the case that appears in Flight 1's logs.

## 12.3 The web console at the competition

The single-file web console ran live at the competition launch. Its panels — flight profile, attitude, GPS, sound and a raw packet monitor — are driven by the same parser and validator as the Python pipeline.

@@fig f-gs-profile | photos/gs-flight-profile.jpg | **Flight profile panel, live.** Altitude above ground (and vertical speed), pressure, temperature and specific force against time, with the pad period shaded, the apogee and peak-g markers, a 30 s / 60 s / all window, a data-table view and an inspect slider that scrubs back through the record. Here the vehicle sits on the pad at 0 m, is carried up the building to about 27 m, and is held at height before the throw. | 100%@@

@@fig f-gs-att | photos/gs-attitude-gps.jpg | **Attitude and GPS panels.** An artificial horizon and compass show roll 131.7°, pitch −15.0° and relative yaw 156.7° (the vehicle held on its side at the terrace edge), with the spin rate; the GPS panel shows the fix, the position relative to the pad (38.2 m at 154°), latitude 21.15995°, longitude 72.78817°, GPS altitude 39 m and the microphone level of 14.5 mV p-p. | 100%@@

@@fig f-gs-3d | photos/gs-track-3d.jpg | **Three-dimensional track.** The climb up the building (vertical line), the walk along the terrace (orange: faster segments, blue: slower) and the vehicle's current position, built from altitude, GPS and attitude. | 100%@@

The console shows exactly what the flight analysis of Chapter 14 later confirmed: the carry up the building, the hold at the terrace edge with the vehicle on its side, and a live link throughout.
