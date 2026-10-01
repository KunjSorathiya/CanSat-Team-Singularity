@@chapter 7 | Mechanical design | `Cansat_D1`: an open PETG frame with an egg chamber — geometry, material, mass budget and the reasoning behind each.@@

## 7.1 The design

`Cansat_D1` is modelled in Fusion 360 and exported to STEP. **Every dimension quoted in this report is read out of the STEP file by `tools/cad_dimensions.py`, and the build fails if the documentation and the model disagree.**

@@gallery g2
cansat-d1-render-1.png | Render, three-quarter view from above: switch cut-out and two LED holes on the upper face.
cansat-d1-render-2.png | Render from below: arched openings, central spine and harness slots.
@@

@@tab t-cad | Cansat_D1 geometry, read from the STEP file@@

| | |
|---|---:|
| Solids | one, `Body1`, 56 faces |
| **Bounding box** | **118.5 × 115.0 × 110.0 mm** |
| Cross-section diagonal | 159.1 mm |
| Height against the 210 mm allowance | **91.5 mm unused** |
| Clearance per side against the 120 mm section | 2.5 mm and 5.0 mm |

It is an **open box frame**: two solid side panels, two faces opened out with large arched cutouts, a central vertical spine, harness slots top and bottom, round holes in the side panels and spine, and a rectangular cut-out for the switch with two small holes beside it for the LEDs.

@@fig f-envelope | c11_envelope.png | The vehicle against the rulebook envelope: elevation (left) and the section looking down (right). | 92%@@

<div class="callout why"><div class="ct">Why an open frame</div>

* **Material goes where the load path is.** The solid side panels and central spine carry load; everything else is air. The three structural studies (Chapter 8) confirm the load path with a safety factor of 7.6 or more even after worst-case derating.
* **The barometer must breathe.** A sealed body would lag the vehicle's true pressure during a fast descent; open arched faces keep the BMP280 in moving ambient air and keep the altitude channel honest.
* **Access.** The board is reached from two sides without disassembly; the antenna, GPS patch and switch are on the outside faces.
* **Mass.** The printed frame weighs ≈ 128.7 g including the egg chamber — light enough that the vehicle is trimmed up to the mass band rather than fighting its upper edge.
* **A prismatic form is the most efficient way to carry a flat board.** The 100 × 100 mm board fits flat inside the 115 × 110 mm section, with 15 and 10 mm to spare for walls and standoffs.

</div>

## 7.2 Material — white PETG

The rulebook permits any outer material and offers a bonus for sustainable or unconventional ones; PETG was chosen and the reasoning recorded.

@@tab t-material | Why PETG@@

| Criterion | PETG | PLA | ABS |
|---|---|---|---|
| Toughness under one impact | Deforms before it fractures | Brittle | Tough |
| Printable without an enclosure | Yes, little warping | Yes | No — warps, fumes |
| Heat in a sunlit pad | Safe to ~70 °C | Softens near 55 °C | Safe |
| Interlayer adhesion | Good | Fair | Good |
| Recyclable / widely available | Yes | Yes | Less so |

* **Impact energy goes into deformation rather than fracture** — a bent frame is a recovered vehicle, a shattered one is not.
* **Print orientation was decided before printing and recorded**: as modelled, sitting on its base. It was the single free variable that changes a printed part's strength, it costs nothing at slicing time, and it cannot be changed afterwards. Layers stack vertically, so the weak directions are tension normal to the layers and interlayer shear — which is why the structural studies are derated for it.
* **White** shows a clean print rather than hiding a poor one, photographs cleanly against any background, and runs cooler in sunlight on a pad than a dark part.

## 7.3 The mass budget

@@fig f-mass | c02_mass_budget.png | From weighed parts to the mass band. The electronics were weighed separately (110.573 g board, 40.726 g battery); the 280 g bare vehicle was weighed after assembly; the structure is the difference. | 96%@@

@@tab t-mass | Mass budget@@

| Item | Mass | How |
|---|---:|---|
| Assembled vehicle board, no battery | 110.573 g | Weighed 9 Sep |
| Battery — 1500 mAh 1S LiPo | 40.726 g | Weighed 9 Sep |
| **Electronics, all-up** | **151.299 g** | Sum |
| **Printed structure + egg chamber** | **≈ 128.7 g** | By difference: 280 − 151.299 |
| **Assembled vehicle, no canopy** | **280 g** | Weighed 12 Sep |
| Canopy, lines, harness | 30 – 55 g | Fitted after that reading |
| Switch, power LED, divider | 5 – 10 g | Fitted after that reading |
| Egg payload / trim mass | to the band | Added to bring the vehicle into 450 – 550 g |
| **Flight mass** | **450 – 550 g** | Within the rulebook's 500 g ± 10 % |

**What was measured and what was derived.** The scale figure is the 280 g assembled vehicle; the electronics were weighed separately three days earlier; the structure line is arithmetic on two measurements. The submitted mass lies in the 450–550 g band, and the descent system was sized for the top of it (Chapter 9).

### The structure came in 33 % lighter than the estimate

| | |
|---|---:|
| Predicted — solid volume × 1.27 g/cm³ | 193.0 g |
| Printed — and that includes an egg chamber the estimate did not | ≈ 128.7 g |
| Difference | −64 g, −33 % |

Infill is the whole of it: the 193 g assumed no infill saving; a real slice of a thin-walled open frame is mostly perimeter and air. The estimate was labelled an upper bound and behaved like one. **Both estimates in the project — the avionics estimate was 31 g low and the structure estimate 64 g high — were corrected by a scale in one minute**, which is why every mass in the budget above is a weighed number.

## 7.4 Egg chamber and recovery hardware

* **Egg chamber.** A cushioned, secure chamber is part of the printed structure and sits inside the +7 cm allowance the rulebook gives it; it holds the egg against the descent and landing loads and is included in the 128.7 g printed mass.
* **Parachute placement.** The rulebook requires the canopy to deploy instantly on release and forbids burying it tightly inside the structure. The canopy is therefore carried external / semi-exposed, attached through the frame's harness slots, so the first moments of free fall pull it open (Flight 1: canopy fully loaded 1.0 s after release).
* **Antenna and power hardware.** The pigtail's panel nut clamps through the frame wall; the switch and its two LED holes are in the upper face cut-out, reachable on the pad without opening the vehicle.

## 7.5 Fabrication

The structure is original work printed from the team's own CAD model — not an off-the-shelf enclosure. The frame, the egg chamber, the harness points, the switch cut-out and the antenna clamp are all features of the one model, so nothing is bolted on afterwards that was not planned. The vehicle was printed, assembled with the electronics and egg chamber, and weighed on 12 September 2026; the canopy, switch and LED were fitted and the mass trimmed into the band on 13–14 September.
