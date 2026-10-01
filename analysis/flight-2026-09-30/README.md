# Launch-day analysis — 30 September 2026

The organizers' ground station exported what it heard of CAN-Team-25 as `data/Team-25-ground-station-log.xlsx`
(180 rows, 10 exported files, repeated and out of order). This directory turns it into the analysis in
Chapter 14 of the final project report.

| File | What it is |
|---|---|
| `launch_analysis.py` | Parses every row with the ground station's own `parse_packet()`, removes repeated exports, splits at each restart of the mission clock, re-derives height with the hypsometric equation, and computes every statistic |
| `launch_figures.py` | Draws the 24 figures in `figures/` from the cleaned data and `results.json` |
| `make_chapter.py` | Writes Chapter 14 of the report from `results.json`, so no number is typed by hand |
| `flight_data_clean.csv` | The 102 distinct packets with derived channels |
| `results.json` | Every number the report quotes |

```bash
python analysis/flight-2026-09-30/launch_analysis.py analysis/flight-2026-09-30/data/Team-25-ground-station-log.xlsx --out analysis/flight-2026-09-30
python analysis/flight-2026-09-30/make_chapter.py
```

Requires numpy, pandas, scipy, matplotlib, openpyxl.
