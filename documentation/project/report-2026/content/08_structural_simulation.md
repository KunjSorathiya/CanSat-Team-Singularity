@@chapter 8 | Structural simulation | Three static-stress studies on the printed frame — what was loaded, what the stresses were, and how the margin holds up against the real flight loads.@@

## 8.1 What was simulated

Three static-stress studies were run in Fusion 360 on `Cansat_D1` on 9 September 2026: static stress, one fixed constraint, parabolic elements.

@@tab t-struct | The three studies@@

| Study | Load | Mesh | Peak von Mises | Yield ÷ stress |
|---|---|---|---:|---:|
| **1 · Horizontal** | 30 N on +Z | 5,838 nodes / 2,619 elements | 2.885 MPa | **18.9** |
| **2 · Tearing** | 30 N on −X | 5,838 nodes / 2,619 elements | 1.330 MPa | **40.9** |
| **3 · Impact** | 100 N on −X | 7,148 nodes / 3,299 elements | 2.345 MPa | **23.2** |

In all three, Fusion's minimum safety-factor plot reads its display ceiling of 15 everywhere on the part: **at or above 15 across the whole frame** in every load case. The three yield-derived figures above are the sharper statement, because the plot saturates.

@@fig f-sf | c05_safety_factors.png | Safety factor by load case: isotropic, and derated for the layered structure of a printed part. | 92%@@

<div class="callout why"><div class="ct">Why these three load cases</div>

* **Horizontal (30 N)** — the side load of a gust, a harness pull or a lift-off scrape.
* **Tearing (30 N)** — a pull on the harness points that tries to peel the frame apart.
* **Impact (100 N)** — the touchdown. 100 N is a 500 g vehicle at 5 m/s (2.5 N·s) stopped in 25 ms: a landing on grass or soil with the canopy and the structure doing part of the work. The stopping time was chosen to represent ordinary ground, and the bar is deliberately set at the rulebook's 5 m/s cap rather than at the vehicle's real descent rate.

</div>

## 8.2 Material properties, and derating for a printed part

The studies use Fusion's PET plastic (E = 2758 MPa, yield 54.4 MPa). Bulk PETG is slightly softer and about 10 % lower in yield (E ≈ 2000–2100 MPa, ≈ 50 MPa), and an FDM part is anisotropic: interlayer adhesion is typically 40–70 % of in-plane strength. Print orientation was therefore fixed in advance (sitting on its base, as modelled) and the safety factors are reported with the derating applied:

@@tab t-derate | Safety factor after derating for the printed layer structure@@

| Study | Isotropic | × 0.70 | × 0.55 | × 0.40 |
|---|---:|---:|---:|---:|
| Horizontal | 18.9 | 13.2 | 10.4 | **7.6** |
| Tearing | 40.9 | 28.6 | 22.5 | 16.4 |
| Impact | 23.2 | 16.2 | 12.8 | **9.3** |

**Even at the pessimistic 40 % factor the smallest margin is 7.6** — and taking the plot's capped value of 15 instead of the yield-derived number gives an effective floor of 6. The structure is designed with margin to spare, not argued into compliance.

## 8.3 The studied loads against the loads the vehicle actually met

The 100 N touchdown assumption can now be set against the flights. From the measured steady rates, the momentum of the vehicle at arrival and the force for a 25 ms stop are:

@@tab t-touchdown | Touchdown load: the study against the flights, for a vehicle in the 450–550 g band@@

| Case | Mass | Rate | Momentum | Force at 25 ms | at 10 ms |
|---|---:|---:|---:|---:|---:|
| **Study 3's assumption** | 500 g | 5.00 m/s | 2.50 N·s | **100 N** | 250 N |
| **Flight 1, measured** | 450 – 550 g | 2.27 m/s | 1.02 – 1.25 N·s | **41 – 50 N** | 102 – 125 N |
| **Flight 2, measured** | 450 – 550 g | 1.88 m/s | 0.85 – 1.03 N·s | **34 – 41 N** | 85 – 103 N |

@@fig f-touchdown-load | 20_descent_physics.png | Left: drag area (Cd·S) implied by each flight's steady rate against vehicle mass, with the model's value for the 6 ft canopy. Centre: the drag coefficient of the 6 ft canopy that each flight implies. Right: mean touchdown force against stopping time, with the 100 N study load. | 100%@@

**The flights landed with 40–50 % of the momentum the structure was analysed for.** The accelerometer agrees: Flight 2's touchdown packet read 1.57 g and the steady-descent swing peaks stayed below 2 g in both flights. Even in the unlikely case of a 10 ms stop the force (≈ 85 – 125 N) is the same order as the 100 N the study covers — against an isotropic safety factor of 23.

<div class="callout result"><div class="ct">Conclusion of the structural work</div>

Under every load the studies applied, the stress is a small fraction of yield, and the real flight loads are a fraction of the studied loads. The frame has margin in the studied directions by a factor of 7.6 to 40.9, and the measured landing momentum is below half of what the impact study assumed.

</div>

## 8.4 The Fusion 360 results

The three figures below are the result plots exported by Fusion 360 itself (the full HTML reports are in `mechanical/simulation/`): von Mises stress, the deformed shape drawn magnified, the safety-factor plot, and the constraint and load set-up. In every study one face is held fixed (blue) and the load acts on the opposite structure.

@@fig f-fusion1 | photos/fusion-study-1.jpg | **Study 1 — horizontal force, 30 N on +Z.** The stress concentrates around the arched cut-outs and where the central spine meets the top rail, peaking at 2.885 MPa; the safety-factor plot shows no region below the study target (the frame is left uncoloured). | 100%@@

@@fig f-fusion2 | photos/fusion-study-2.jpg | **Study 2 — tearing force, 30 N on −X.** The lowest stresses of the three studies (peak 1.330 MPa) and a peak displacement of only 0.026 mm: the frame is very stiff against a pull on the harness points. | 100%@@

@@fig f-fusion3 | photos/fusion-study-3.jpg | **Study 3 — impact force, 100 N on −X.** The loaded panel bows (drawn magnified; the true peak displacement is 0.209 mm) and the stress spreads into the base and the neighbouring rails, peaking at 2.345 MPa, 4 % of the 54.4 MPa yield strength used in the study. The safety-factor plot is blue — above the study target — over the whole frame. | 100%@@

**How to read them.** In the stress plots the colour scale runs from blue (zero) to red (the peak) and the peak is a few megapascals against a yield strength of tens — so even the "red" regions are at a few per cent of yield. In the safety-factor plots Fusion colours only what falls in or below the target band the study was set up with (2 to 4): in studies 1 and 2 nothing does, so the frame is left uncoloured, and in study 3 the whole frame is shown blue, *above target*. In none of the three load cases does any part of the frame enter the band. The deformation plots show where the structure moves — the loaded panel and the free rails — and the numbers are fractions of a millimetre.
