<section class="cover">
<img class="art" src="figures/cover_art.png"/>
<div class="top"><span>Physics Club · SVNIT Surat</span><span>CanSat Competition 2026</span></div>
<div class="title">
<div class="kicker">Final Project Report</div>
<h1>Team <em>Singularity</em><br/>CAN-Team-25</h1>
<div class="sub">Design, simulation, flight software, verification and flight analysis of a LoRa-telemetry CanSat that is carried to 100&nbsp;ft by a drone, released, and brought back to the ground under a parachute — two flights flown on 30&nbsp;September 2026.</div>
</div>
<img class="render" src="figures/photos/cansat-d1-render-1.png"/>
<div class="tiles">
<div class="tile"><b>2<small>flights</small></b><span>flown and analysed</span></div>
<div class="tile"><b>1.9–2.3<small>m/s</small></b><span>steady descent rate, limit 5&nbsp;m/s</span></div>
<div class="tile"><b>3.09<small>Hz</small></b><span>telemetry rate in flight, 41 / 41 packets heard</span></div>
<div class="tile"><b>6,131<small>checks</small></b><span>automated tests, all passing</span></div>
</div>
<div class="foot"><span>github.com/KunjSorathiya/CanSat-Team-Singularity</span><span>October 2026</span></div>
</section>

<section class="frontpage" style="break-before: page" markdown="1">

## Contents

<!--TOC-->

</section>

<section class="frontpage" style="break-before: page" markdown="1">

## About this report

This is the complete record of the CanSat built by **Team Singularity** (packet identity **CAN-Team-25**) for the SVNIT Physics Club CanSat Competition 2026. It covers the vehicle from the first requirement to the last flight packet: what was built, why every important decision was taken the way it was, how the software thinks, what the simulations predicted, what was measured on the bench, and what the vehicle did on 30 September 2026.

<div class="kpis k3">
<div class="kpi tl"><b>Design</b><span>Requirements, architecture, components, electrical, mechanical, structural and descent simulation — each with the reasoning behind it.</span></div>
<div class="kpi gd"><b>Code</b><span>Flight loop, state machine, calibration, telemetry, logging and the ground station, with the logic drawn as flowcharts and the key routines quoted.</span></div>
<div class="kpi f1"><b>Flights</b><span>Two descents analysed packet by packet: altitude, temperature, pressure, acceleration, orientation, descent rate, radio link, correlations.</span></div>
</div>

### How to read it

* **Chapters 1–4** give the mission, the requirements and the shape of the whole system.
* **Chapters 5–9** are the hardware: components, electrical design, structure, simulation and the descent system.
* **Chapters 10–13** are the software and the radio link, ground station, logging and the testing that backs them.
* **Chapter 14** is the flight analysis — the results — and **Chapter 15** collects what was learned building the vehicle.
* **Chapter 16** is the decision register: one table listing every major design decision, the alternatives, the reason, and the evidence.
* The appendices hold the pin map, the flight constants, the repository map, the complete flight dataset, references and a glossary.

### Conventions

* **Times** in the flight chapter are IST (UTC + 5:30); the ground station logged UTC. **Mission time** is the vehicle's own clock, which restarts at every power-up.
* **Altitude** is the vehicle's transmitted `A-` field unless stated otherwise: pressure altitude relative to the ground baseline the vehicle sets itself at calibration. Where a corrected height is used (hypsometric, from the measured pressure and temperature) it is labelled.
* **Figures** with a blue frame and a title are drawn from the flight log by `analysis/flight-2026-09-30/launch_analysis.py`; every number in the flight chapter is in `results.json` beside it.
* The CanSat, its firmware, the ground station, the simulations, the CAD model and this report's source are all in one repository: **github.com/KunjSorathiya/CanSat-Team-Singularity**.

### Data sources for the flight chapter

| Source | What it is |
|---|---|
| `Team-25.xlsx` | The organizers' ground-station export: 180 rows, each a received LoRa packet with host timestamp, packet text, RSSI and SNR |
| Repository parser | Every row was parsed with the same `parse_packet()` the ground station uses — one packet format, one definition |
| `flight_data_clean.csv` | The 102 distinct packets that remain after the repeated exports are removed, with derived channels |
| `results.json` | Every statistic quoted in Chapter 14 |

</section>
