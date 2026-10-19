# Step 5C — Evidence-constrained sensitivity experiments

This package is an alternative **not** a replacement for previous Step 5 and Step 5B results. It is intended to avoid an automatic flow into unaffiliated identity while separating empirically observed 2010–2020 net movement from explicitly hypothetical group growth and migration mechanisms.

Run inside the folder containing the previous step scripts and `data/` directory:

```powershell
.\.venv\Scripts\python.exe step5c_evidence_sensitivity.py --runs 120 --seed 62
.\.venv\Scripts\python.exe verify_step5c.py
.\.venv\Scripts\python.exe step5c_make_maps.py
.\.venv\Scripts\python.exe step5c_make_scenario_maps.py
```

Outputs: `data/forecasts_step5c/` and `outputs/maps_step5c/`. All old outputs remain unchanged.

Scenario families (30 runs each):

1. `persistence_benchmark`: no change in national religious shares.
2. `pew_observed_momentum`: damped observed Pew 2010–2020 country share changes; no claim of causal switching.
3. `group_growth_sensitivity`: Pew observed momentum plus deliberately hypothetical religious demographic growth differences. Pew's global ordering cannot be applied to country-level subgroups without additional data. This is a sensitivity test.
4. `europe_migration_sensitivity`: Pew observed momentum plus hypothetical Muslim proportions among positive *net* migrants in Europe, between 25% and 50%. UN net migration is not a migrant-flow-by-religion dataset. This is a what-if stress test, not a forecast.

All runs use country population scenarios from the old Step 5 loader (UN WPP 2024 through 2100, rule-based beyond), and bounded residual draws. Monte Carlo run frequencies are NOT objective probabilities of religion becoming predominant in a country.

These experiments provide possible modeling behaviors; they do not establish that any country will become Muslim or unaffiliated, and especially not in 2200–3026.

Historical context: Pew Research Center, `How the Global Religious Landscape Changed From 2010 to 2020` (2025); `Factors Driving Religious Change 2010–2020` (2025); `Europe's Growing Muslim Population` (2017). Use official sources for citations.
