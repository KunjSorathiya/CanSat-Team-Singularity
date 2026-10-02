# Simulations

Models that answer a question the hardware could not answer yet. As of 2026-10-02 the descent model has been compared with a real flight — see [model against flight](#model-against-flight-6-ft-canopy).

Everything here is executable, runs in the host test suite, and is pinned to a value that
can be checked by hand. A model whose numbers nobody can reproduce is a guess with a
decimal point on it.

| Model | Question it answers | Tests |
|---|---|---|
| [`descent.py`](descent.py) | How big must the parachute be, how long does the descent last, and how many telemetry packets does it produce? | `tests/test_descent.py` |

Related models that live elsewhere because they are tools rather than mission analysis:
[`tools/link_budget.py`](../tools/link_budget.py) computes LoRa time-on-air and the
telemetry rate the link can sustain — see
[link-budget.md](../documentation/design/link-budget.md).

---

## Running them

```bash
python simulations/descent.py                    # the mission case
python simulations/descent.py --sweep            # every canopy type compared
python simulations/descent.py --format markdown  # paste into a document
```

They also run as part of the ordinary host build, so a change that breaks the physics
fails the same build as a change that breaks the firmware:

```bash
bash tools/build_host.sh
```

---

## `descent.py` — canopy sizing and descent

**The question.** The rulebook caps the descent rate at **5 m/s** ([REC-005]) and releases
the vehicle from **100 ft / 30.48 m** ([MIS-001]) at a mass of **500 g ± 10 %**
([GEN-005]). Nothing in the repository turned those into a parachute.

**What it computes.**

- The constructed canopy area and flat diameter needed to hit a target descent rate, from
  `S = 2 m g / (ρ Cd v²)`.
- The descent rate a canopy you already have will actually produce.
- The descent *time*, from the closed-form solution of `m dv/dt = mg − ½ρCdSv²` rather
  than height ÷ rate — the vehicle starts at rest and accelerates into the terminal rate,
  and over a 30 m drop that transient is a third of a second.
- The number of telemetry packets the descent yields at a given period.
- Air density from the gas law, taking **pressure and temperature the vehicle itself
  measures**. A 35 °C launch day is ~6.5 % thinner than the ISA 15 °C reference, which is
  ~7 % more canopy for the same rate.

**What it does not compute.** Canopy opening dynamics, oscillation, the drag of the bare
vehicle before deployment, or wind drift. The deployment delay is modelled as free fall,
which is pessimistic on altitude and therefore safe.

### The answer, for the record

At 500 g, ISA sea level, a vented flat circular canopy (Cd 0.75 on constructed area):

| Quantity | Value |
|---|---|
| Constructed area | 0.4270 m² |
| **Flat diameter** | **73.7 cm** |
| Terminal rate | 5.00 m/s |
| Descent time from 30.48 m | 6.45 s |
| Packets during descent, at 1.43 Hz | **9** |

Sized instead at the **top of the mass tolerance** (550 g) and for a **hot day** (35 °C),
which is the combination that has to still pass:

| Quantity | Value |
|---|---|
| **Flat diameter** | **80.0 cm** |
| Terminal rate | 5.00 m/s |

Canopy type changes this by about ±10 % on diameter:

| Canopy | Cd | Diameter | Area |
|---|---:|---:|---:|
| cruciform | 0.85 | 69.3 cm | 0.3767 m² |
| flat-circular | 0.80 | 71.4 cm | 0.4003 m² |
| vented-flat | 0.75 | 73.7 cm | 0.4270 m² |
| hemispherical | 1.40 | 54.0 cm | 0.2287 m² |

### Three findings worth acting on

**1 · Size the canopy at 550 g, not 500 g.** Area is linear in mass, so the ±10 % mass
tolerance is ±10 % of area but only ~5 % of diameter. A canopy sized at the nominal mass
and flown at the top of the tolerance **exceeds the 5 m/s cap**; one sized at 550 g is
compliant across the whole band and costs 6 cm of cloth. `test_sizing_at_the_top_of_the_
tolerance_covers_the_whole_band` asserts exactly this.

**2 · The descent is the smallest part of the flight dataset.** 30.48 m at 5 m/s is
**6.45 seconds**, which at the flight profile's 1.43 Hz is **nine packets**. Every
descent-rate number the analysis reports comes from those nine. It is an argument for the
faster telemetry rate, for the SD log being the primary record, and against expecting a
smooth descent-rate curve out of the radio.

**3 · Cd is the dominant uncertainty, and it is not resolvable on paper.** The spread
between canopy types is larger than every other term in the model combined. The way to
close it is a drop test with a known mass and a stopwatch, which then feeds a measured Cd
back into this model — see [test-plan.md](../documentation/testing/test-plan.md).

### Model against flight, 6 ft canopy

*Added 2026-10-02.* The canopy that flew was **6 ft (1.83 m) in diameter**, not 80 cm: 80 cm
is the model's guaranteed minimum (550 g, 35 °C, vented flat, Cd 0.75), 6 ft is 2.3× the
diameter and 5.2× the area. The same model, run for the 6 ft canopy, against the descents
measured from the organizers' log ([analysis/flight-2026-09-30/](../analysis/flight-2026-09-30/README.md)):

| Quantity | Model (Cd 0.75) | Flight 1 | Flight 2 |
|---|---|---|---|
| Steady descent, 450–550 g | 1.97–2.18 m/s | **2.27 ± 0.05 m/s** | **1.88 ± 0.02 m/s** |
| At 500 g, flight-day air | 2.07 m/s | +9 % | −9 % |
| Descent time from 29.5 m | ≈ 14–15.6 s | — | 15.4 s (29.6 m) |
| Cd implied for 450–550 g | 0.75 (assumed) | 0.57–0.69 | 0.82–1.00 |

The model is within ±9 % of both flights, and the assumed Cd of 0.75 sits between their
implied values. Finding 3 ("Cd is the dominant uncertainty") is borne out: two flights of the
same canopy and vehicle differ by 19 % in rate. The descent was far slower than the 5 m/s
cap, so finding 2 also holds in a different form: the descents are 14–15 s long, with 41 and
18 packets received. The model was not re-fitted to the flights.

[REC-005]: ../documentation/requirements/requirements.md
[MIS-001]: ../documentation/requirements/requirements.md
[GEN-005]: ../documentation/requirements/requirements.md

---

## Rules for anything added here

The same rules the documentation runs under, applied to code:

1. **Every constant says where it came from.** Rulebook, datasheet, textbook or engineering
   choice — named in a comment, at the definition.
2. **Every model is pinned to something independent.** A closed-form limit, a published
   reference vector, or a value computable by hand. `test_descent.py` uses all three.
3. **A model that cannot be run is not a model.** Command line, tests, and a place in
   `tools/build_host.sh`.
4. **Predictions stay labelled as predictions** until a measurement replaces them. When one
   does, it goes in [bring-up-record.md](../documentation/testing/bring-up-record.md) and
   the prediction is compared against it rather than quietly deleted.
