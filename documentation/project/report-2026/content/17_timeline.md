@@chapter 17 | Project timeline | Twelve days from the first line of code to a built vehicle — and the flights at the end of it.@@

## 17.1 The schedule

@@fig f-timeline | c07_timeline.png | Development schedule, September 2026. | 96%@@

@@tab t-timeline | What happened, day by day@@

| Days | What happened |
|---|---|
| **3 – 4 Sep** | The whole software stack, written and tested on the host, then a second pass that found **nine defects in code that already built and passed** |
| **4 – 5 Sep** | Parts arrive and are photographed and identified one board at a time; the microSD reader turns out to be a 3.3 V board, closing the power-design question |
| **5 Sep** | Breadboard bring-up. The radio answers and transmits, the card initialises and writes, and **two intermittents both turn out to be one long supply jumper** |
| **6 Sep** | The board is *designed* rather than assembled: floorplan to scale, coupling analysis, decoupling sized against a failure that actually happened, sixteen gated build steps |
| **7 Sep** | The board is built and gates 3–7 pass on it. **The first radio link closes** — 66 packets, no gaps. Running the flight image finds the chip-select ordering defect |
| **8 Sep** | Telemetry to 1.43 Hz; an authorised erase command; GPS gated on satellite count and HDOP; the first mission analysis, which finds the hover problem |
| **9 Sep** | The mechanical design: `Cansat_D1` modelled, 12 cm sided box confirmed, PETG chosen, three stress studies, electronics weighed at 151.299 g |
| **10 – 11 Sep** | The first range test; the sync word moves to `0xA5` on both ends; packet budget cut to 200 B; GPS and sound go on the air; `MAX_RATE` measured at 3.11 Hz |
| **12 Sep** | The structure is printed; the vehicle becomes a physical object: 280 g on a scale |
| **13 – 14 Sep** | Canopy, switch and power LED fitted; mass trimmed into the 450–550 g band; vehicle and report submitted |
| **30 Sep** | **Two flights**, hand-thrown from a building terrace at 29–30 m under the 6 ft canopy. Both descents at 38–45 % of the 5 m/s limit; the analysis in Chapter 14 |

## 17.2 The flight-day analysis was ready before the flights

The rulebook gives four hours after the launch to analyse the data. The analysis pipeline — a one-command tool and a notebook that write the three mandatory graphs, the descent rate by regression, the implied drag coefficient, acceleration, orientation, GPS drift, acoustic level and the comparison of the SD log against the ground log — was written and tested **before there was a flight**, against a synthetic flight whose answers were known: descent rate within 3 %, drag coefficient within 6 %, release time within 0.15 s, and the altitude-formula bias corrected. On the day, the work was to interpret, not to write code; Chapter 14 is that interpretation.
