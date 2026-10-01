@@chapter 15 | Engineering discoveries | The defects and surprises found by running things — each one found, understood and closed — and what each one changed in the design.@@

## 15.1 What running the vehicle taught that reading it could not

Every item below came from *running* something rather than from reading it. Each is closed, and most changed a rule that now protects the rest of the design.

@@tab t-findings | Discoveries and their resolution@@

| # | What was expected | What was found | Resolution |
|---|---|---|---|
| **D-1** | A radio that either works or does not | The same transmit failed 5/5 and then succeeded 45/45 minutes later — same code, same antenna | **Closed** with D-2: a long 3V3 jumper on the RA-02 |
| **D-2** | A card that reads is a card that writes | With a long 3V3 jumper the card initialised, read its filesystem, then went silent on the first write — five runs running. A short jumper fixed it outright: **100 / 100** | **Closed.** The write-current spike arrives down whatever wire the supply has; reads never draw enough to expose it. Soldered board: short track + 470 µF bulk capacitor |
| **D-3** | The card to work under the flight image as under the bring-up image | It failed every time under the flight image while passing twelve times under bring-up | **Root cause found, and it is not the card.** The radio's chip select was configured only by the radio driver, which initialises second, so GP17 floated low (selected) through the whole SD sequence. Fixed by driving both chip selects high with the bus |
| **D-4** | Landing detection to need a landing | A landing declared under a **hovering drone, 12 s before release** — the same condition as a vehicle held still at a terrace edge | **Closed by the descent gate** (Section 3.3) |
| **D-5** | The vehicle's altitude to be its height above the pad | **5.7 % small on a hot day** — the ISA formula assumes 15 °C | **Corrected in the analysis**; confirmed in flight (Section 14.7) |
| **D-6** | A reported GPS fix to be a holdable fix | 739 fixes from a stationary receiver: median 8.1 m from the centroid, maximum 50.9 m, largest one-second jump 55.6 m | **Gated.** The parser refuses a fix below 4 satellites or above HDOP 5.0, and parses HDOP, which it previously discarded |
| **D-7** | A telemetry rate that the radio can deliver | The provisional SF9 profile needs 1,250 ms of airtime per packet — longer than the 500 ms period it was configured for | **Closed.** The modem moved to SF7; rate re-derived from measured airtime; three layers of guards (Section 11.4) |
| **D-8** | The organizers' receiver to hear what the team's bridge hears | It discards anything over 200 bytes, and listens on one sync word only | **Closed.** Packet budget cut to 200 B (GPS printed to its real resolution); both Picos fly `0xA5` always |
| **D-9** | Code that builds and passes to be correct | A second review pass found **nine defects** in code that already built and passed | **Closed.** Each got a test |
| **D-10** | Mass estimates to be roughly right | Avionics estimate 31 g low; structure estimate 64 g high | **Closed by weighing.** Every mass in the budget is a measurement |

## 15.2 The defects a host suite cannot reach

Five thousand host assertions did not find D-3, D-2 or the supply-sensitivity of the radio: all three needed a powered board. **The tests catch what the logic gets wrong; the bench catches what the wiring gets wrong; the flight catches what the world does.** The three layers are cumulative, and the project's habit was to move a finding from the outer layer inward — every hardware discovery above became a rule in the code (chip selects together with the bus), a test, and a documented design decision.

## 15.3 How each discovery changed the design

* **D-3 → rule:** *both chip selects are driven high with the bus.* The order in which drivers start can no longer decide whether the bus is safe.
* **D-4 → rule:** *a vehicle cannot land without descending first.* A physical gate replaced a tuned threshold.
* **D-5 → procedure:** *rates are computed from temperature-corrected height*, and both numbers are always quoted.
* **D-7, D-8 → process:** *airtime is measured, budgets are held to the receiver's real limits, and the same modem definition is shared by both ends.*
* **D-9 → habit:** *a second pass over passing code is part of the work*, not a luxury.
