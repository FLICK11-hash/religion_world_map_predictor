"""Verify Step 6 delivered the requested visualizations and coverage audits."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'/'maps'
report=json.loads((OUT/'step6_report.json').read_text(encoding='utf-8'))
required_years=[2010,2050,2100,2200,2500,3026]
assert set(required_years).issubset(report['map_years'])
for year in required_years:
    assert (OUT/f'dominant_{year}.png').is_file(),f'Missing dominant map for {year}'
for year in [2050,2100,2200,2500,3026]:
    assert (OUT/f'scenario_agreement_{year}.png').is_file(), f'Missing agreement map for {year}'
assert (OUT/'global_shares_uncertainty.png').is_file()
for path in report['figure_paths']:
    file=ROOT/path
    assert file.exists() and file.stat().st_size>3000, f'Figure missing or empty: {file}'
coverage=pd.read_csv(OUT/'map_coverage.csv')
assert not coverage.empty
assert coverage.n_country_ids_with_polygons.gt(0).all()
assert coverage.n_country_ids_without_polygons.ge(0).all()
assert coverage.n_country_ids_with_polygons.le(coverage.n_country_records).all()
assert len(report['figure_paths'])==report['generated_files']
print(f"PASS: {report['generated_files']} maps/charts saved and nonempty.")
print('PASS: Required dominant maps, scenario-agreement maps and uncertainty chart exist.')
print('PASS: Geographic coverage audit available.')
print(coverage[['source','year','n_country_records','n_country_ids_with_polygons','n_country_ids_without_polygons']].to_string(index=False))
print('SUCCESS: Step 6 verified. Check map appearance before publishing.')
