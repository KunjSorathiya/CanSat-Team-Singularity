@@chapter 5 | Components | Every part on the vehicle: what it is, what it does, why it was chosen over the alternatives, and how it was verified.@@

## 5.1 Bill of materials

Every module was bought individually, photographed on arrival, and identified from the board and — where the silkscreen was not enough — from a register read over the bus. **The datasheet describes a chip; a photograph and a register read describe the part that was delivered.**

@@tab t-bom | Bill of materials@@

| Subsystem | Component | Qty | Purpose |
|---|---|---:|---|
| Flight computer | Raspberry Pi Pico (RP2040) | 2 | Vehicle flight computer + ground bridge |
| Telemetry | SX1278 RA-02 433 MHz LoRa module | 2 | Vehicle + ground radio |
| Telemetry | 433 MHz whip antenna, SMA | 2 | Radiating element on each end |
| Telemetry | 10 cm IPEX-to-SMA RG1.13 pigtail | 2 | Radio-to-antenna feed, panel-mounted |
| Sensors | MPU-6500 six-axis IMU on a GY-6500/9250 breakout | 1 | 3-axis acceleration, 3-axis angular rate |
| Sensors | GY-BMP280-3.3 barometer | 1 | Pressure, altitude, temperature |
| Sensors | NEO-6M GPS with EEPROM, active patch antenna | 1 | Position and time |
| Sensors | LM393 sound module, 4-pin | 1 | Acoustic level during descent |
| Storage | microSD card reader, 3.3 V | 1 | Onboard flight log |
| Power | 1S LiPo, 3.7 V, 1500 mAh, 25C | 1 | Primary power |
| Power | ON/OFF switch; red power LED + 1 kΩ; green status LED + 1 kΩ | 1 each | Mandatory switch and indicator; mission-state blink |
| Structure | `Cansat_D1`, white PETG, 3D printed, with egg chamber | 1 | Airframe |
| Recovery | **6 ft (1.83 m) diameter** sewn canopy, lines and harness | 1 | Descent at ≤ 5 m/s |
| Integration | 10 × 10 cm universal prototype board, 2.54 mm pitch | 2 | One built, one spare |
| Passives | 470 µF + 100 nF (microSD), 10 µF + 100 nF (radio), 33 kΩ/33 kΩ divider | — | Decoupling and battery sensing |

@@gallery g4 tall
894292-pico-front.jpg | Raspberry Pi Pico (RP2040). Two were fitted with headers and used: vehicle and ground bridge.
1150780-ra02-antenna-mated.jpg | SX1278 RA-02 with its antenna mated through the IPEX-to-SMA pigtail.
2846-mpu9250-front.jpg | IMU breakout. The device answers as an MPU-6500 at address 0x68.
835813-bmp280-front.jpg | GY-BMP280-3.3 barometer module, six-pin I²C/SPI variant.
@@
@@gallery g4 tall
11782-neo6m-front.jpg | NEO-6M GPS with EEPROM and active patch antenna.
11566-sd-reader-front.jpg | 3.3 V microSD reader: four 10 kΩ pull-ups and two capacitors, no regulator.
1125094-lipo-front.jpg | 1S 1500 mAh LiPo with JST-RCY and JST-XH balance leads.
lm393-sound-front.jpg | LM393 sound module: electret capsule, comparator and gain trimmer.
@@

## 5.2 The flight computer — Raspberry Pi Pico (RP2040)

| | |
|---|---|
| Cores / clock | Dual Arm Cortex-M0+, 133 MHz |
| Memory | 264 KB SRAM, 2 MB flash |
| Peripherals used | I²C0 (IMU + barometer), SPI0 (radio + card), UART0 (GPS), ADC0/ADC1 (battery, microphone), hardware watchdog, 1 µs timer |
| Supply | 1.8 – 5.5 V at VSYS; on-board regulator provides 3.3 V |

<div class="callout why"><div class="ct">Why the Pico</div>

* **Enough of everything, nothing in excess.** 264 KB of RAM holds every fixed buffer in the flight core many times over; the loop uses a small fraction of one core at a 2 ms tick, so the second core is spare.
* **A free, hardware watchdog and a 12-bit ADC** — the two peripherals this design leans on hardest. The watchdog is what makes "telemetry never stops" a property of the hardware and not only of the code; the ADC reads the microphone and the battery without extra parts.
* **A C/C++ SDK with a stable build.** The firmware is C++17 with no third-party libraries in the flight path; a toolchain that builds the same code on a laptop and on the target is what makes the host-tested core trustworthy.
* **No radio of its own.** A Pico W would add a 2.4 GHz radio the competition does not use, more current, and a second source of interference beside the GPS. The plain Pico leaves the 433 MHz LoRa module as the only transmitter on the board.
* **Cost and availability.** Two were needed — one flies, one is the ground bridge — and both were identical, so any firmware or driver verified on one is verified on the other.

</div>

**Alternatives considered:** an ESP32 (Wi-Fi/Bluetooth radio noise, higher idle current, and a flash cache that complicates hard real-time behaviour), an Arduino-class AVR (too little RAM for the buffers and no hardware watchdog with a configurable period), and a bare STM32 (no ready-to-solder board in the available time).

**Verified:** both Picos identified by silkscreen (`RP2-B2` stepping) and exercised end to end; headers fitted and soldered; the vehicle Pico's pins pass through the board and are soldered directly, so there is no socket to work loose under launch vibration.

## 5.3 The radio — SX1278 RA-02

| | |
|---|---|
| Band / modulation | 433 MHz ISM, LoRa (chirp spread spectrum) |
| Configured | SF7, 125 kHz, coding rate 4/5, preamble 8, CRC on, +17 dBm on PA_BOOST |
| Interface | SPI; `RST`, `DIO0`, `DIO1` wired |
| Supply | 3.3 V directly (no regulator on the carrier), 87 mA at +17 dBm TX, 12 mA RX |

<div class="callout why"><div class="ct">Why this radio, and why these modem settings</div>

* **The organizers' ground station is an SX1278 RA-02 on 433 MHz.** The rulebook offers two compatible radios (SX1278 LoRa, nRF24L01). Choosing the LoRa module means the vehicle and the scoring receiver are the same silicon, so compatibility is by construction.
* **LoRa over nRF24L01.** The nRF24L01 is a 2.4 GHz short-range link; LoRa at 433 MHz penetrates structures and ground clutter far better and has tens of dB more link margin than a 30 m descent needs.
* **SF7 is chosen for airtime, not range.** A ~190-byte packet needs 943 ms at SF9/125 kHz and about 302 ms at SF7/125 kHz; only the latter meets 1 Hz with margin. The link budget still closes with ≥ 14 dB of margin on the weakest flight packet (Chapter 11).
* **17 dBm, not 20.** +17 dBm is the PA_BOOST maximum without enabling the high-power DAC; +20 dBm would draw 120 mA instead of 87 mA and stress the 3.3 V rail for a link that does not need it.
* **One modem definition for both ends.** The vehicle and the bridge read the same `link_profile.hpp`, because before it existed the two carried separate copies that agreed only by coincidence.

</div>

## 5.4 The inertial sensor — MPU-6500

| | |
|---|---|
| Measures | 3-axis acceleration (±16 g configured), 3-axis angular rate (±2000 °/s configured) |
| Filters | Digital low-pass 21.2 Hz (accelerometer) and 20 Hz (gyro); 200 Hz internal data rate |
| Bus | I²C0 at `0x68` |
| Supply | 3.3 V |

<div class="callout why"><div class="ct">Why a six-axis IMU, and why these ranges</div>

* **The rulebook's reference IMU is the six-axis MPU-6050.** The MPU-6500 is its successor in the same family — same measurements, same register style, lower noise — so it meets the "gyroscope + accelerometer" requirement exactly.
* **±16 g and ±2000 °/s.** The loads in this mission are the throw (measured 5.2 g in Flight 1), a canopy opening (2.1 g) and a touchdown (1.6 g). ±16 g leaves a factor of three of headroom over the worst of them; ±2000 °/s covers a vehicle tumbling at several revolutions per second without saturating the integrator.
* **A 20 Hz filter against a 30 Hz sample rate.** The filter bandwidth is set so that the loop's 30 Hz sampling does not alias vibration into the attitude estimate.
* **Yaw is a relative angle.** Roll and pitch are referenced to gravity through the accelerometer and are absolute. Yaw is integrated from the gyro and zeroed at calibration; the telemetry declares it as such. Firmware for a magnetometer-referenced yaw is also present and tested against simulated fields for a nine-axis part.
* **Bias is measured, not assumed.** Gyro bias per axis was measured on the bench at X −3.30, Y +0.86, Z −0.06 °/s; at every power-up the pad calibration re-measures it, which is why the post-landing session in Chapter 14 shows yaw frozen to ±0.1° after calibration.

</div>

## 5.5 The barometer — BMP280

| | |
|---|---|
| Measures | Pressure 300 – 1100 hPa, temperature −40 … +85 °C |
| Output rate | ≈ 83 Hz at the configured oversampling (measured 83.0 Hz) |
| Bus | I²C0 at `0x76` |
| Compensation | Bosch 64-bit integer path; reproduces the datasheet's own reference vector |

<div class="callout why"><div class="ct">Why the BMP280, and why the altitude is computed the way it is</div>

* **The rulebook names a BMP as the altitude sensor** and lists pressure and temperature as mandatory fields. One chip supplies all three.
* **Resolution fits the task.** The pressure noise measured on the ground is 1.15 Pa (σ), which is 0.10 m of altitude — one tenth of a metre against a 30 m flight.
* **Baseline-relative altitude.** The firmware converts pressure to altitude with the international standard atmosphere formula and subtracts a ground baseline averaged over 80 samples at calibration, so the packet reads ≈ 0 m on the pad as the rulebook asks, whatever the weather. Chapter 14 shows the formula reproduces the transmitted altitude to ±0.03 m.
* **Why the temperature field is the barometer's.** The chip measures its own die temperature for compensation, so it is free, always valid and in the same burst read as the pressure.

</div>

## 5.6 The additional sensors

### GPS — NEO-6M

u-blox NEO-6 receiver on a GY-NEO6MV2 board with a 24C32A EEPROM, backup cell and active patch antenna on a u.FL lead. UART0 at 9600 baud; all six NMEA sentences, zero checksum errors in bench logs. Parsed by the project's own streaming GGA/RMC parser, which **refuses a fix below 4 satellites or above HDOP 5.0**. Printed on the air as 5-decimal latitude/longitude (1.1 m resolution against the receiver's ~2.5 m error) and whole-metre altitude; the SD log keeps full precision plus satellite count and HDOP.

**Why GPS:** it is the textbook additional sensor for a descent — position, drift and an independent altitude — and in the flight it measured the vehicle's ground track under canopy (Chapter 14).

### Microphone — LM393 sound module

An electret capsule with an LM393 comparator and gain trimmer; the analogue output goes to ADC1 on GP27. Each loop tick samples a burst of conversions and reduces it to a peak-to-peak envelope; a second channel records what fraction of the window exceeded a threshold. Resolution is 3.3 V / 4096 = 0.806 mV per count.

<div class="callout why"><div class="ct">Why a microphone</div>

**A microphone on a descending probe is a flight-proven atmospheric instrument.** Mars 2020 *Perseverance* carried one dedicated to entry, descent and landing; the *Huygens* probe carried an acoustic sensor through Titan's atmosphere in 2005; *Venera 13* and *14* recorded wind noise on Venus. Acoustics is one of the cheapest ways to instrument a descent. In order of usefulness it measures: **impulsive events** (the throw is the loudest packet of Flight 1 — 36.3 mV p-p), **flow noise** against descent speed, and canopy dynamics. Two channels are recorded deliberately — *how loud* and *what fraction of the time* — because a sharp crack and a steady roar can reach the same peak and mean opposite things. The level is a relative envelope in millivolts, comparable within a flight at one gain setting.

</div>

## 5.7 Storage — microSD

3.3 V reader (no regulator, no level shifter — the host is 3.3 V, so none is needed), on the shared SPI0 bus with its own chip select (GP6). The project's driver implements the SD protocol from CMD0/CMD8/ACMD41 initialisation through SDHC/SDSC block addressing. Measured: 100/100 writes; 2.68 ms mean block write; ~300 writes/s sustained.

**Why a card at all:** the radio link is lossy by nature; the SD log is the record that cannot be. It holds every packet the radio sent, plus fields that never go on the air.

## 5.8 Power

| | |
|---|---|
| Battery | 1S LiPo, 3.7 V nominal (4.2 V full), 1500 mAh, 25C, JST-RCY discharge lead |
| Rail | Pico's on-board regulator: 3V3(OUT) — measured **3.28–3.29 V under 45 back-to-back radio transmits** and **3.28–3.30 V at 100 % microSD write duty** |
| Switch | In the battery positive lead, ahead of everything |
| Power LED | Red, 1 kΩ, on the regulated 3.3 V rail |
| Battery sense | GP26 (ADC0) through a 33 kΩ / 33 kΩ divider |

<div class="callout why"><div class="ct">Why no external regulator</div>

An AMS1117-3.3 was assessed and rejected: at a full cell of ≈ 4.2 V it does not clear its high-load dropout. The Pico's own regulator was then **measured** carrying every load on the vehicle, and it held 3.28 V or better in the worst cases. One rail, no external part, one fewer thing to fail. Chapter 6 gives the current budget.

</div>

## 5.9 Telemetry antenna and structure parts

The whip antenna and its IPEX-to-SMA pigtail were verified to mate hand-tight with no adapter; the pigtail is a bulkhead type, so its nut and star washer clamp it through the airframe wall, which is also its strain relief. The GPS patch antenna sits skyward and the LoRa antenna is routed away from it, because a +17 dBm transmitter beside a receiver working near −130 dBm can overload its front end.

@@gallery g3
1121334-antenna-front.jpg | 433 MHz whip antenna on a hinged base.
1674982-ipex-sma-cable.jpg | IPEX-to-SMA bulkhead pigtail with panel nut and star washer.
1031002-protoboard-front.jpg | 10 × 10 cm universal board that carries the vehicle electronics.
@@
