@@chapter 11 | Telemetry protocol and the radio link | What goes over the air, how big it is allowed to be, why the modem is configured the way it is — and how the link budget compared with the flights.@@

## 11.1 The packet

Every packet is the rulebook string — text, not a binary struct — so any receiver, and any human with a serial terminal, can read it. This is a real packet from Flight 1 (P-1585, received at 18:25:47 IST), split by what each part carries:

<div class="packet">
<span style="border-color:#0b2545"><i style="color:#0b2545">identity</i>CAN-Team-25; P-1585;</span>
<span style="border-color:#1d4ed8"><i style="color:#1d4ed8">mission clock</i>Ti-00:11:12:929;</span>
<span style="border-color:#0f8b8d"><i style="color:#0f8b8d">altitude · pressure · temp</i>A-27.6; Pr-100884.95; T-31.4;</span>
<span style="border-color:#7b2cbf"><i style="color:#7b2cbf">attitude</i>Ro-62.2; Pi-16.0; Ya-153.1;</span>
<span style="border-color:#f2a900"><i style="color:#b07d00">acceleration</i>AX--2.66; AY-10.51; AZ-4.48;</span>
<span style="border-color:#e4572e"><i style="color:#e4572e">GPS (optional)</i>GP-Lat-21.15994; GP-Lon-72.78813; GP-Alt-42;</span>
<span style="border-color:#2e9e5b"><i style="color:#2e9e5b">sound</i>SN-10.5;</span>
<span style="border-color:#64748b"><i style="color:#64748b">status</i>ST-F111;</span>
</div>

@@tab t-fields | Packet fields@@

| Field | Meaning | Format |
|---|---|---|
| `CAN-Team-XX` | Team identifier | Correct identifier in every packet |
| `P-XXX` | Packet number | Starts at `P-001`, increments sequentially |
| `Ti-HH:MM:SS:MS` | Mission clock since power-on | Hours wrap at 100 so the field never widens |
| `A-XXX.X` | Altitude | Metres, 1 decimal, relative to the pad baseline |
| `Pr-XXXX.XX` | Pressure | Pa, 2 decimals |
| `T-XX.X` | Temperature | °C, 1 decimal |
| `Ro-` / `Pi-` / `Ya-` | Roll / pitch / yaw | Degrees, 1 decimal |
| `AX-` / `AY-` / `AZ-` | Acceleration | m/s², 2 decimals |
| `GP-Lat` / `GP-Lon` / `GP-Alt` | GPS position, only when a valid fix exists | 5 decimals / whole metres |
| `SN-` | Acoustic level | mV peak-to-peak |
| `ST-` | Status: state letter, armed, calibrated, active faults — `ST-F110` is FLIGHT, armed, calibrated, none | Dropped from any packet it would push past 200 bytes |

**Precision is enforced exactly, in the formatter and in all three parsers.** The C++, Python and JavaScript implementations are held to **one shared fixture file** (`test-data/protocol-fixtures.tsv`), so they cannot drift apart. A negative value keeps its own minus sign after the separator (`AX--2.66`), which is why a parser must split on the last dash that is not itself a sign; a dedicated fixture holds every parser to that.

## 11.2 Two packet shapes and a 200-byte ceiling

@@tab t-shapes | The two packet shapes@@

| Shape | Carries | Worst case |
|---|---|---:|
| **Rich** | The twelve mandatory fields, then `GP-Lat`, `GP-Lon`, `GP-Alt`, then `SN-`, then `ST-` | 209 B, held to **200 B** on the air |
| **Lean** | The twelve mandatory fields only | 147 B |

Measured in the flights: **lean packets 118–130 bytes, rich packets 136–188 bytes**, none above 188.

<div class="callout why"><div class="ct">Why 200 bytes</div>

**The 200-byte ceiling is not the team's.** The organizers' receiver — an ESP32 running the arduino-LoRa library — reads into a 201-byte buffer and discards anything longer. Their station is the one that scores, so 200 is the ceiling whatever the team's own bridge can hear. At 6 decimals of latitude and 1 of altitude the GPS block was 55 bytes and mandatory + GPS was 202 — two bytes over. Printed to what the NEO-6M actually resolves (**5 decimals = 1.1 m against its ~2.5 m error, and whole metres**) the block is 51 bytes and the total is 198. The SD log keeps the full precision.

The byte figures are defended **by construction, not by arithmetic**: a test builds the widest packet each shape can produce — packet number 4,294,967,295, a 99:59:59:999 clock, every axis at full scale — and checks it against its constant. That test corrected the design twice, once by two bytes on the lean packet, which crossed a LoRa symbol boundary and cost 5 ms of airtime on every packet.

</div>

When a packet would be too long the vehicle sheds optional content in the rulebook's priority order — status field, then sound, then GPS — and never lets the radio truncate silently; if the mandatory block alone overflowed, it would suppress the packet rather than send one that reads as corruption.

## 11.3 The radio configuration

@@tab t-radio | Modem parameters@@

| Parameter | Value | Fixed by |
|---|---|---|
| Frequency | 433 MHz | Rulebook band |
| Spreading factor | SF7 | Engineering choice — airtime |
| Bandwidth | 125 kHz | Engineering choice |
| Coding rate | 4/5 | Engineering choice — lowest overhead |
| Preamble / CRC | 8 symbols / on | SX127x default; corruption must be detectable |
| TX power | 17 dBm (PA_BOOST) | RA-02 maximum without PA_DAC |
| **Sync word** | **`0xA5`** | **Rulebook — and the organizers' station listens on nothing else** |

<div class="callout why"><div class="ct">Why both Picos fly the launch sync word, always</div>

The rulebook gives `0xF3` for testing and `0xA5` for the launch. On the 10 September range test the vehicle was on the test word and the organizers' station heard only the few packets an SX127x sync filter lets through, while the team's own station heard every one — a silent, near-total loss of telemetry that looks exactly like a dead radio. **Both images now fly `0xA5` for testing as well as for launch**, so what the team's bridge hears is what the organizers' station hears. The 30 September log is the confirmation: the organizers' station recorded both flights.

</div>

One definition of the modem parameters is shared by both ends — `link_profile.hpp` — because before it existed the two carried separate copies and agreed only by coincidence.

## 11.4 Airtime decides the rate

LoRa trades data rate for sensitivity: at a high spreading factor a single packet can occupy the channel for longer than the interval it must fit in. From the Semtech datasheet formula (verified against two published reference vectors, in two languages, and against a radio):

```text
Tsym      = 2^SF / BW
Tpreamble = (n_preamble + 4.25) * Tsym
n_payload = 8 + max(ceil((8*PL - 4*SF + 28 + 16*CRC - 20*IH) / (4*(SF - 2*DE))) * (CR + 4), 0)
ToA       = Tpreamble + n_payload * Tsym
```

@@tab t-airtime | Airtime of a 255-byte packet at coding rate 4/5@@

| Config | Airtime | Max rate | Rate at 50 % duty | Meets 1 Hz? |
|---|---:|---:|---:|---|
| **SF7 / 125 kHz** | **399.6 ms** | 2.50 Hz | **1.25 Hz** | **yes** |
| SF8 / 125 kHz | 707.1 ms | 1.41 Hz | 0.71 Hz | over duty |
| SF9 / 125 kHz | 1250.3 ms | 0.80 Hz | 0.40 Hz | no |
| SF7 / 250 kHz | 199.8 ms | 5.00 Hz | 2.50 Hz | yes |
| SF12 / 125 kHz | 9019.4 ms | 0.11 Hz | 0.06 Hz | no |

<div class="callout why"><div class="ct">The finding that changed the design</div>

The provisional default was SF9 / 125 kHz. At that setting a full packet takes **1,250 ms** of airtime — longer than the interval it was supposed to fit inside. The scheduler had been configured for a 500 ms period, a rate the radio could never have delivered. Re-deriving the rate from airtime moved the modem to **SF7**, which is the only spreading factor that meets 1 Hz with duty margin on a full packet. SF7 costs about 6 dB of sensitivity against SF9 and buys a threefold airtime reduction — a favourable trade for a 30 m descent.

</div>

**Measured on the delivered module:** a 206-byte packet took 333.7 ms against 327.9 predicted, and a 255-byte one 406.9 ms against 399.6 — both about 1.8 % over the model, reproduced to 0.1 ms across four sessions. The slots are therefore sized from **measured** airtime plus a 50 ms guard.

### The rate: 1.43 Hz in the window, 3.1 Hz in flight

@@fig f-airtime | c03_airtime_cycle.png | The max-rate transmit cycle: one rich slot (374 ms) and two lean slots (296 ms each) per 966 ms. | 94%@@

@@tab t-rates2 | Telemetry rates@@

| | Command window | Flight, after the window closes |
|---|---:|---:|
| Period / cycle | 700 ms | 966 ms (374 + 296 + 296) |
| **Packet rate** | **1.43 Hz** | **3.11 Hz designed · 3.09 Hz measured in Flight 1** |
| Sensors on the air | 1.43 Hz | 1.04 Hz (one rich packet per cycle) |
| Channel duty | 46 % measured | 84 % |

The measured cadence in the flight log — gaps of 0.374 s, 0.296 s and 0.297 s repeating exactly — is the designed pattern to the millisecond (Chapter 14, Figure "Max-rate cadence"). **The 50 ms guard does two jobs in the same gap:** it covers the vehicle's own worst-case SD block write (30 ms), and the organizers' receiver, which is deaf for about 35 ms after every packet while it prints what it just heard at 115200 baud.

**The rulebook's 1 Hz is a floor this vehicle cannot be configured onto.** Three independent mechanisms enforce it: a `static_assert` refuses to compile a profile above 950 ms, `validate_config()` refuses to run one, and the documentation checker refuses to pass a repository whose text disagrees. A flight build silently running at 1 Hz is exactly the failure the design guards against.

## 11.5 The link budget, against the flights

@@fig f-linkbudget | c09_link_budget.png | Free-space prediction (17 dBm, 0 dBi antennas) with the receiver floor, and the band of RSSI the organizers' station actually recorded in flight. | 88%@@

Free-space path loss at 433 MHz is FSPL = 32.45 + 20 log₁₀(433) + 20 log₁₀(d<sub>km</sub>) dB: 79 dB at 500 m, 85 dB at 1 km, 91 dB at 2 km. Typical SX127x sensitivity at 125 kHz is about **−123 dBm at SF7**. The calculation said SF7 is *not range-limited* for a 30 m descent. The flights say so with measured data:

* **RSSI in flight: −109 to −79 dBm** (mean −92.1 dBm over 102 packets).
* **Link margin over the receiver floor: 14 dB on the weakest packet, 31 dB on average, 44 dB at best.**
* **SNR: −6.75 to +10.75 dB**, and it saturates near +10 dB for any RSSI better than about −90 dBm — the receiver's own noise floor, not the vehicle's.

Chapter 14 analyses the link packet by packet.
