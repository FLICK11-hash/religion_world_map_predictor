# Step 5B — Explore dynamic religion scenarios

This is a **sensitivity experiment**, not a replacement forecast with demonstrated higher accuracy. It does not overwrite `data/forecasts` or `outputs/maps`.

Copy `step5b_dynamic_scenarios.py`, `verify_step5b.py`, and `step5b_make_maps.py` into the same project folder as `step5_forecast_scenarios.py` and `step6_make_maps.py`.

```powershell
.\.venv\Scripts\python.exe step5b_dynamic_scenarios.py --runs 120 --seed 52
.\.venv\Scripts\python.exe verify_step5b.py
.\.venv\Scripts\python.exe step5b_make_maps.py
explorer .\outputs\maps_step5b
```

Outputs in `data/forecasts_step5b` include the same `country_year_uncertainty.csv` and `global_share_uncertainty.csv` formats as Step 5, plus `scenario_change_summary.csv`, `scenario_country_maps.csv`, and parameter/report files. Maps save to `outputs/maps_step5b`.

### What changed

1. `conservative`: retains Step 5's existing weak-ML and secularization assumptions.
2. `recent_momentum`: uses capped Pew 2010–2020 country-specific religious-share changes, exponentially decayed so a 10-year trend isn't naively extended 1,000 years.
3. `differential_growth`: additionally tests hypothetical group-specific relative growth rates. These are **not measured religious fertility**, because national UN total fertility rates cannot identify group rates.
4. `structural_shocks`: additionally tests persistent regional and country-specific regime changes. These are stress-test assumptions; their shock sizes have **not** been historically calibrated.

All four scenarios use demographic population projections through 2100 and stylized demographic extrapolation afterward. No scenario is supported as a statistically likely projection to 3026. The 120-run scenario agreement map shows sensitivity to chosen assumptions, not real-world confidence.

The country map's religion label can remain unchanged even with large redistribution among shares; check `scenario_change_summary.csv` and individual group-share maps. Some 2020 Pew Folk/Other values are proxy-derived.

To draw **separate maps for each scenario**, run:

```powershell
.\.venv\Scripts\python.exe step5b_make_scenario_maps.py
explorer .\outputs\maps_step5b\by_scenario
```

This is the recommended way to visualize uncertainty in the year 3026. The pooled mode can appear stable even when the four individual scenario families disagree substantially.
