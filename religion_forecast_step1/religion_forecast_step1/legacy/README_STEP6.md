# Step 6 — Country religion maps and scenario visualizations

These files work with the **existing** `religion_world_map_predictor/religion_forecast_step1/religion_forecast_step1` folder. **Do not delete or overwrite raw datasets.**

## Requirements
Uses existing `pandas`, `geopandas`, `numpy`, `matplotlib` from earlier steps. It reads:

- `data/raw/ne_50m_admin_0_countries.zip`
- `data/processed/wrp_training_only_8groups.csv`
- `data/processed/pew_anchor_only_8groups.csv`
- `data/forecasts/country_year_uncertainty.csv`
- `data/forecasts/global_share_uncertainty.csv`

## Windows PowerShell

```powershell
cd C:\Users\conra\religion_world_map_predictor\religion_forecast_step1\religion_forecast_step1
Expand-Archive "$env:USERPROFILE\Downloads\religion_forecast_step6.zip" -DestinationPath . -Force
.\.venv\Scripts\python.exe step6_make_maps.py
.\.venv\Scripts\python.exe verify_step6.py
explorer .\outputs\maps
```

Default generates maps for 2010 (Pew), 2020 (Pew), 2050, 2100, 2200, 2500, and 3026 (model scenarios); supplementary historical WRP dominant maps for 1945, 1970 and 1990; eight religious share maps for 2010, 2050, 2100, 2200, 2500 and 3026; five scenario-agreement maps; and a global-religion uncertainty figure. All are PNG.

**To try the workflow more quickly**, generate only three share-group maps for each date:

```powershell
.\.venv\Scripts\python.exe step6_make_maps.py --share-groups Christianity,Islam,Unaffiliated
```

To generate only dominant and scenario-agreement maps:

```powershell
.\.venv\Scripts\python.exe step6_make_maps.py --skip-shares
```

The program also saves `outputs/maps/step6_report.json`, `map_coverage.csv` and `unmapped_country_ids.csv`, so geographic coverage limitations are visible.

## Important analytical cautions

- All geometry comes from Natural Earth's **present-day** country outlines. The supplementary 1945/1970/1990 WRP maps show modern country geometries only where identifiers still match, and deliberately leave historical entities such as the USSR and Czechoslovakia uncolored rather than inventing borders.
- Pew's 2010/2020 **Folk/Traditional vs Other** split is proxy-derived for many countries. The more defensible published Pew categories often combine them.
- `scenario_agreement_*.png` shows the fraction of the 120 simulations assigning a country the same modal label; this is **not a validated probability that the prediction will happen**.
- Neither the historical country mapping nor the 2200–3026 religious projections are suitable as factual historical or future geopolitical maps. These are exploratory visualizations, not cartographic reconstructions or calibrated forecasts.
- The 3026 view is interpolated from modeled 3025 and 3030 states.
- Check `unmapped_country_ids.csv` before publishing: unmatched territories remain gray, and some Natural Earth geographic areas might not have religion data.

## Suggested figure credit

*Country boundaries: Natural Earth (public domain). Religious affiliation estimates: World Religion Project and Pew Research Center (2010 and 2020 dataset). Simulations and figures: author calculations. Folk/Other splitting and future scenarios use additional assumptions. See source datasets and methods.*

Cite WRP and Pew's original datasets as well as Natural Earth; observe Pew's current terms for data reuse and graphical reproduction. Do not treat citation alone as legal permission for proprietary source images (these PNGs are generated anew).
