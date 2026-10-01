@@chapter 9 | Descent system and simulation | How the canopy was sized with a closed-form model, why it was sized for the heaviest, hottest case — and how the flights compared with the model.@@

## 9.1 What the simulation computes

`simulations/descent.py` sizes the canopy and models the fall. It runs in the host test suite, so a change that breaks the physics fails the same build as a change that breaks the firmware, and it is pinned to closed-form limits that can be checked by hand.

* **Canopy area and flat diameter** for a target descent rate: **S = 2 m g / (ρ · Cd · v²)**.
* **The descent rate a canopy you already have will produce**: v = √(2 m g / (ρ Cd S)).
* **Descent time** from the closed-form solution of **m·dv/dt = m g − ½ ρ Cd S v²**, rather than height ÷ rate: the vehicle starts at rest and accelerates into terminal velocity, and over a 30 m drop that transient matters (v(t) = v<sub>t</sub> · tanh(g t / v<sub>t</sub>)).
* **Air density from the gas law, using the pressure and temperature the vehicle itself measures.** A 35 °C launch day is ~6.5 % thinner than ISA, which is ~7 % more canopy for the same descent rate.
* **The number of telemetry packets** the descent yields at the vehicle's rate.

Deployment delay is modelled as free fall, which is pessimistic on altitude and therefore safe. Canopy opening dynamics, oscillation and wind drift are outside the model; Chapter 14 measures them.

## 9.2 Two answers from one model: the minimum canopy, and the canopy flown

The model answers two different questions, and both matter.

**What is the smallest canopy that is guaranteed to meet the 5 m/s limit?** Size it for the worst case — the heaviest vehicle on the hottest day, with the lowest plausible drag coefficient:

@@tab t-sizing | Minimum canopy sizing cases@@

| Case | Flat diameter | Rate | Time from 30.5 m |
|---|---:|---:|---:|
| 500 g, ISA 15 °C, vented flat circular | 73.7 cm | 5.00 m/s | 6.45 s |
| **550 g, 35 °C — the sizing case** | **80.0 cm** | **5.00 m/s** | **6.45 s** |

Canopy area is linear in mass, so ±10 % of mass is ±10 % of area but only ~5 % of diameter: a canopy sized at 500 g and flown at 550 g **breaks the 5 m/s cap**; one sized at 550 g is compliant across the whole band and costs 6 cm of cloth. The hot day is the sizing day because thinner air is the failure direction. **80 cm is therefore the floor: below it the cap is not guaranteed.**

**What canopy was flown?** A **6 ft (1.83 m) canopy** — 2.3 times the floor's diameter and 5.2 times its area.

<div class="callout why"><div class="ct">Why a 6 ft canopy, well above the 80 cm floor</div>

* **The floor is a guarantee at the edge of the model; the mission wants margin inside it.** The model's drag coefficient is the dominant uncertainty — canopy types span Cd 0.75 to 1.40 — and the vehicle's mass is only known to lie in a ±10 % band. A canopy several times the floor turns a prediction that is *just* compliant in its worst case into one that is comfortably compliant in every case.
* **A hand-thrown launch gives the canopy a harder start than a drone release.** The vehicle leaves the hand moving at about 5 m/s with no carrier to clear it, so a large canopy that fills fast and has reserve drag is the safer answer to the question "will it open in time from 30 m?".
* **A slow descent is a benign descent.** At about 2 m/s the vehicle arrives with about 1 J of kinetic energy — the energy of a step of 18–26 cm — which protects the structure, the board and the egg chamber, and gives a longer, steadier flight with more telemetry per metre of altitude (about 45 packets at the max rate).
* **The price is drift and cloth.** A larger canopy drifts further with the wind (measured: ≈ 1.9 m/s of ground speed in Flight 1) and adds mass; at 30 m and a ~15 s descent the drift is a few tens of metres, which the recovery plan absorbs.

</div>

## 9.3 The 6 ft canopy across the mass band

@@fig f-descent-model | c04_descent_model.png | Left: terminal descent rate against flat canopy diameter for the three masses of the band, on a standard day (solid) and a 35 °C day (dashed). The 80 cm sizing floor and the 6 ft canopy flown are marked, with the two measured flight rates. Right: the diameter needed for 5 m/s at 500 g for each canopy type. | 100%@@

@@tab t-band | Model for the 6 ft vented-flat canopy (Cd 0.75) across the band, 29.5 m launch height@@

| Flight mass | Air | Rate | Descent time | Packets at 0.7 s | Packets at 3.09 Hz |
|---|---|---:|---:|---:|---:|
| 450 g | ISA 15 °C | 1.91 m/s | 15.6 s | 22 | ~48 |
| 450 g | 31.4 °C (flight day) | 1.97 m/s | 15.1 s | 21 | ~47 |
| 500 g | ISA 15 °C | 2.02 m/s | 14.8 s | 21 | ~46 |
| 500 g | 31.4 °C (flight day) | **2.07 m/s** | **14.4 s** | 20 | ~44 |
| 550 g | 31.4 °C (flight day) | 2.17 m/s | 13.7 s | 19 | ~42 |

## 9.4 Three constraints on the canopy that are not the diameter

* **It must not be tightly packed** — external or semi-exposed, so it deploys immediately on launch (a rulebook requirement). A canopy stuffed inside the body risks the deployment itself.
* **The descent must be stable**, without tumbling or spinning. An unvented flat circular canopy oscillates; a central vent of roughly 10 % of the diameter costs a little drag and buys a great deal of stability.
* **The structure must be intact after landing and telemetry must continue** — so the antenna and the battery connection have to survive the arrival.

### Canopy type is the largest uncertainty in the model

@@tab t-canopy | Drag coefficient and the diameter it implies for 5 m/s at 500 g@@

| Canopy | Cd | Diameter at 500 g |
|---|---:|---:|
| Cruciform | 0.85 | 69.3 cm |
| Flat circular | 0.80 | 71.4 cm |
| Vented flat | 0.75 | 73.7 cm |
| Hemispherical | 1.40 | 54.0 cm |

The sizing uses the *lowest* plausible Cd for a stable canopy (vented flat, 0.75) — the choice that makes the canopy largest and the descent slowest.

## 9.5 The flights against the model

The model was written before the flights; the 6 ft canopy flew twice. The comparison is a direct test of it:

@@tab t-model-vs-flight | Model and measurement@@

| | Model, 6 ft canopy, Cd 0.75 | Flight 1 | Flight 2 |
|---|---:|---:|---:|
| Steady descent rate, 450 – 550 g | **1.97 – 2.18 m/s** (2.07 at 500 g) | **2.27 ± 0.05 m/s** | **1.88 ± 0.02 m/s** |
| Deviation from the 500 g prediction | — | +9 % | −9 % |
| Time to fall 29.5 m | 13.7 – 15.1 s (31 °C air) | — (record ends 1.3 m above the ground) | **15.4 s** for 29.6 m |
| Cd implied for the 6 ft canopy, 450 – 550 g | 0.75 assumed | **0.57 – 0.69** | **0.82 – 1.00** |

**The model predicted both flights to within 10 %.** The two flights bracket the 500 g prediction on either side, and the Cd they imply (0.57–1.00) brackets the 0.75 the model assumed — the spread being the same ±10 % uncertainty in the flown mass that the sizing allowed for. A closed-form model with one tabulated coefficient, written before anything had flown, predicted the descent rate of a vehicle thrown from a terrace to within a tenth.

<div class="callout note"><div class="ct">How the drag coefficient is inferred</div>

At steady descent weight equals drag, so Cd·S = 2 m g / (ρ v²). ρ is computed from the pressure and temperature the vehicle measured in the descent (1.156 kg/m³ and 1.157 kg/m³ for the two flights), v is the least-squares slope of the temperature-corrected height, S is the flat area of a 6 ft disc (2.63 m²) and m is taken across the 450–550 g band. Chapter 14 tabulates the values for each mass.

</div>
