@@chapter 6 | Electrical design | One battery, one rail, two shared buses — the power path, the current budget, the pin map, and the decoupling that keeps the radio and the card from disturbing each other.@@

## 6.1 The power path

@@fig f-power | d12_power_path.png | From battery to every load. The switch sits in the battery lead ahead of everything; every peripheral runs from the Pico's own 3.3 V output. | 100%@@

**The power LED hangs off the regulated rail through a series resistor, not off a GPIO.** The rulebook requires the LED to light *immediately* on power-up; a firmware-driven LED would wait for the boot. The firmware separately drives a green status LED on GP14 whose blink rate encodes the mission state.

<div class="callout why"><div class="ct">Design decision — which node the power LED hangs off</div>

| Hung off the switched battery | Hung off the regulated 3.3 V rail — **chosen** |
|---|---|
| Means "the battery is connected" | Means "the system is actually powered" |
| Stays lit with a dead flight computer | Goes dark if the regulator fails — the honest signal |
| 3.4 – 4.2 V, so it dims visibly as the cell drains | Regulated: constant brightness and current |

A red LED at 1 kΩ from 3.3 V draws 1.30 mA — bench-bright and cheap in current, which is the right direction for a battery vehicle.

</div>

## 6.2 One rail, answered by measurement

Three hardware questions held the design up for days. All three closed by measurement, and how they closed is more useful than the fact that they did.

@@tab t-rail | The 3.3 V rail under every load@@

| Condition | Rail voltage |
|---|---|
| Idle | 3.30 V |
| 45 back-to-back radio transmits (+17 dBm) | **3.28 – 3.29 V** |
| 100 % microSD write duty | **3.28 – 3.30 V** |
| Radio at 100 % TX duty | 3.26 – 3.27 V |

**No external regulator is needed**, and the microSD reader turned out to be a **3.3 V board**: its supply pin is printed `3V3` and its entire parts list is four 10 kΩ pull-ups and two capacitors. A listing that described a 4.5–5.5 V board with an on-board regulator described a different product; the delivered board is simpler and runs from the same rail as everything else.

## 6.3 The current budget

@@fig f-power-budget | c10_power_budget.png | Duty-weighted current by device (left) and the three load cases (right). | 96%@@

@@tab t-power | Per-device worst-case draw@@

| Device | Worst case | Condition | Duty in flight |
|---|---:|---|---:|
| SX1278 RA-02 | **87 mA** | TX at +17 dBm (PA_BOOST) | 33 % (333.7 ms of every second) |
| | 12 mA | RX continuous | the other 67 % |
| microSD + reader | ~100 mA | block write | ~1 % (two writes ≈ 10 ms per telemetry second) |
| NEO-6M | ~70 mA / ~45 mA | cold acquisition / tracking | start-up / continuous |
| MPU-6500 | ~4 mA | gyro + accel active | continuous |
| BMP280 | ~1 mA | 83 Hz, high oversampling | continuous |
| Microphone module | ~5 mA | continuous | continuous |
| LEDs | 2.6 mA | both lit | power LED continuous; status LED ≤ 50 % |

**Steady-state flight draw is about 130 mA including the RP2040** (TX at 33 % duty, RX otherwise, GPS tracking). A 1500 mAh cell therefore carries roughly eleven hours of flight-state running — against a mission whose pad phase is five minutes and whose flight is seconds. The worst simultaneous case (TX, SD write, GPS acquiring, all sensors, both LEDs) is 306 mA; it is brief and the measured rail holds through it.

## 6.4 Buses, and the lesson each one taught

Two shared buses carry everything except the GPS:

* **I²C0 (GP4/GP5)** carries the IMU at `0x68` and the barometer at `0x76`. Both verified together on the soldered board, 400 kHz.
* **SPI0 (GP16/GP18/GP19)** carries the radio and the microSD, with separate chip selects on GP17 (radio) and GP6 (card).

<div class="callout why"><div class="ct">Design decision — chip-select discipline on the shared SPI bus</div>

Running the sealed flight image on the soldered board revealed a defect that no host test could have found. The radio's chip select (GP17) was configured only by the radio driver, which initialises *second*. Through the whole SD-card initialisation GP17 was an unconfigured pad, and an RP2040 pad resets with its pull-down enabled — which holds it **low**, which on the RA-02 means *selected*. The radio drove MISO for the entire card sequence.

The fix is a rule: **both chip selects are driven high together with the bus, before any device on it is touched.** A SPI bus is only shared safely if every device on it is deselected by construction rather than by the order in which drivers happen to start.

</div>

## 6.5 Decoupling, sized against a failure that actually happened

@@tab t-decoupling | Decoupling capacitors and what each is for@@

| Where | Value | What it is for |
|---|---|---|
| microSD reader, across its own 3V3 and GND | **470 µF** electrolytic | The write-current spike, ~100 mA for a few ms; it must not reach the regulator and stack on the radio's peak |
| Same pins | **100 nF** ceramic | Fast edges the electrolytic is too slow for |
| RA-02, across its 3.3 V and GND | **10 µF** | PA key-up: 1.5 mA standby to 87 mA in microseconds, 45 times a minute |
| Same pins | **100 nF** ceramic | As above |

Why the card gets the largest capacitor: on the breadboard a long 3.3 V jumper let the card initialise, read its filesystem — then go silent on the first write, five runs running. A short jumper fixed it outright (100/100). The write-current spike arrives down whatever wire the supply has; reads never draw enough current to expose it. On the soldered board the supply became a short track and a local 470 µF bulk capacitor. The same fault explained a radio that transmitted 5/5 and then 0/5: **two intermittents, one cause, on two different modules.**

## 6.6 Pin assignment

`BoardPins` in `firmware/flight-computer/include/flight/config.hpp` is the single source of truth. The netlist at `electrical/schematics/vehicle-netlist.tsv` is **generated from it**, and the generator refuses to run if the two disagree; the wiring diagrams come from the same source. A pin cannot drift between the code and the documentation.

@@tab t-pins | Pin assignment (vehicle Pico)@@

| GPIO | Function | Device |
|---:|---|---|
| GP4 / GP5 | I²C0 SDA / SCL | MPU-6500 (`0x68`) + BMP280 (`0x76`) |
| GP16 / GP18 / GP19 | SPI0 MISO / SCK / MOSI | RA-02 + microSD |
| GP17 | Chip select | RA-02 |
| GP6 | Chip select | microSD |
| GP20 / GP21 / GP22 | RESET / DIO0 / DIO1 | RA-02 |
| GP12 / GP13 | UART0 TX / RX | NEO-6M |
| GP7 | Interrupt | MPU-6500 INT, wired |
| GP14 | Status LED | Green LED, blink rate encodes mission state |
| GP15 | Comparator input | LM393 `DO` |
| GP26 | ADC0 | Battery sense, divider 33 kΩ / 33 kΩ (ratio 2.0) |
| GP27 | ADC1 | LM393 `AO` (microphone) |

## 6.7 Why a hand-assembled universal board

A 10 × 10 cm single-sided universal board carries the electronics, with every module's pins soldered directly (no sockets). The choice was deliberate:

* **The pin map was frozen and hardware-verified before the board was built**, so the wiring is known rather than discovered; the build followed a sixteen-step gated assembly plan, each step with a measurement.
* **Short, direct runs.** Radio, card and Pico sit within a few centimetres of each other, so the high-current supply runs are short tracks and the two noisiest loads have their own local capacitors.
* **Fast iteration for a twelve-day schedule.** A custom board needs a fabrication round trip the schedule could not spare; the universal board let the supply wiring be changed the same day a bench finding called for it — the short card supply in Section 6.5 is exactly such a change.
* **Photographable and inspectable.** Every joint is visible, which made the bring-up measurements — and the board photographs in the report — straightforward.
