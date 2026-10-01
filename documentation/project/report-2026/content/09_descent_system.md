@@chapter 9 | Descent system and simulation | How the canopy was sized with a closed-form model, why it was sized for the heaviest, hottest case — and how the flights compared with the model.@@

## 9.1 What the simulation computes

`simulations/descent.py` sizes the canopy and models the fall. It runs in the host test suite, so a change that breaks the physics fails the same build as a change that breaks the firmware, and it is pinned to closed-form limits that can be checked by hand.

* **Canopy area and flat diameter** for a target descent rate: **S = 2 m g / (ρ · Cd · v²)**.
* **The descent rate a canopy you already have will produce**: v = √(2 m g / (ρ Cd S)).
* **Descent time** from the closed-form solution of **m·dv/dt = m g − ½ ρ Cd S v²**, rather than height ÷ rate: the vehicle starts at rest and accelerates into terminal velocity, and over a 30 m drop that transient matters (v(t) = v<sub>t</sub> · tanh(g t / v<sub>t</sub>)).
* **Air density from the gas law, using the pressure and temperature the vehicle itself measures.** A 35 °C launch day is ~6.5 % thinner than ISA, which is ~7 % more canopy for the same descent rate.
* **The number of telemetry packets** the descent yields at the vehicle's rate.

Deployment delay is modelled as free fall, which is pessimistic on altitude and therefore safe. Canopy opening dynamics, oscillation and wind drift are outside the model; Chapter 14 measures them.

## 9.2 Sizing at the top of the mass band

@@tab t-sizing | Canopy sizing cases@@

| Case | Flat diameter | Rate | Time |
|---|---:|---:|---:|
| 500 g, ISA 15 °C, vented flat circular | 73.7 cm | 5.00 m/s | 6.45 s |
| **550 g, 35 °C — size to this** | **80.0 cm** | **5.00 m/s** | **6.45 s** |

<div class="callout why"><div class="ct">Why size at 550 g and 35 °C, not at the nominal mass</div>

Canopy area is linear in mass, so ±10 % of mass is ±10 % of area but only ~5 % of diameter. A canopy sized at 500 g and flown at 550 g **breaks the 5 m/s cap**; one sized at 550 g is compliant across the whole band and costs 6 cm of cloth. A test asserts exactly this. The hot day is the sizing day because thinner air is the failure direction: the same canopy falls faster on a 35 °C afternoon than on a standard one. The result is a canopy whose worst case — heaviest vehicle, hottest air — still just meets the limit, so every other case beats it.

</div>

@@fig f-descent-model | c04_descent_model.png | Left: terminal descent rate against flat canopy diameter for the three masses of the band, on a standard day (solid) and a 35 °C day (dashed); the design floor is 80 cm. Right: the diameter needed for 5 m/s at 500 g for each canopy type. | 100%@@

### The canopy across the mass band (80 cm design floor)

@@tab t-band | Modelled descent for the 80 cm design floor across the band@@

| Flight mass | Rate | Descent time from 30.5 m | Packets at 3.11 Hz |
|---|---:|---:|---:|
| 450 g, ISA | 4.37 m/s | 7.28 s | ~22 |
| 500 g, ISA — nominal | 4.61 m/s | 6.94 s | ~21 |
| **550 g, 35 °C — the sizing case** | **5.00 m/s** | **6.45 s** | **~20** |

## 9.3 Three constraints on the canopy that are not the diameter

* **It must not be tightly packed** — external or semi-exposed, so it deploys immediately on release (a rulebook requirement). A canopy stuffed inside the body risks the deployment itself.
* **The descent must be stable**, without tumbling or spinning. An unvented flat circular canopy oscillates; a central vent of roughly 10 % of the diameter costs a little drag and buys a great deal of stability; a cruciform is better still and easy to sew.
* **The structure must be intact after landing and telemetry must continue** — so the antenna and the battery connection have to survive the arrival.

### Canopy type is the largest uncertainty in the model

@@tab t-canopy | Drag coefficient and the diameter it implies at 500 g@@

| Canopy | Cd | Diameter at 500 g |
|---|---:|---:|
| Cruciform | 0.85 | 69.3 cm |
| Flat circular | 0.80 | 71.4 cm |
| Vented flat | 0.75 | 73.7 cm |
| Hemispherical | 1.40 | 54.0 cm |

Drag coefficient is the dominant term in the model, which is why the sizing uses the *lowest* plausible Cd for a stable canopy (vented flat, 0.75) — the choice that makes the canopy largest and the descent slowest.

## 9.4 The flights against the model

The model was written to guarantee that the cap is respected. The flights say how much margin that guarantee left:

@@tab t-model-vs-flight | Model and measurement@@

| | Model, 80 cm design floor, 500 g | Flight 1 | Flight 2 |
|---|---:|---:|---:|
| Steady descent rate | 4.61 m/s (5.00 at the sizing case) | **2.27 ± 0.05 m/s** | **1.88 ± 0.02 m/s** |
| Time to fall 30 m | ≈ 6.9 s | ≈ 13 s equivalent | 15.4 s for 29.6 m |
| Equivalent drag area for 500 g | 0.38 m² (Cd·S, vented flat) | **1.65 m²** | **2.40 m²** |

The vehicle came down slower than the design floor guarantees. A slower descent is the right direction for every flight requirement — a longer flight, a gentler arrival, a lower touchdown load — and it means the design carries a real margin: **the measured drag area is 4 – 6× the floor the sizing demanded.** That margin is the reason the 5 m/s cap holds even with the heaviest vehicle on the hottest day.

<div class="callout note"><div class="ct">How the drag area is inferred</div>

At steady descent weight equals drag, so Cd·S = 2 m g / (ρ v²). ρ is computed from the pressure and temperature the vehicle measured in the descent (1.156 kg/m³ and 1.157 kg/m³ for the two flights), v is the least-squares slope of the temperature-corrected height, and m is taken across the 450–550 g band. Chapter 14 tabulates the values for each mass.

</div>
