# Step 5E - testing the cohort model on religion history (WRP 1950-2010)

Step 5E checks the Step 5D mechanisms against what actually happened. It uses only local data
(WRP shares, WPP demography, Natural Earth geography), so it runs without Pew.

## Run (from this folder)
```powershell
.\.venv\Scripts\python.exe test_step5e.py              # checks on real data, about 30 s
.\.venv\Scripts\python.exe step5e_wrp_hindcast.py      # hindcast search, about 40 s
```
Outputs in `data\hindcast_step5e\`:
- `hindcast_summary.csv`: the table below.
- `hindcast_by_decade.csv`: every decade, model and setting, with per-religion errors and sign accuracy.
- `projection_2010_2050.csv`: WRP 2010 shares projected to 2050, with inflow, outflow and net by religion.
- `group_tfr_predicted.csv`: predicted fertility by religion for every WPP country (low/central/high gap).

## How it works
- Each test runs 10 years from WRP shares at year y (1950-1980 as TRAIN, 1990 and 2000 as TEST) and
  compares the result with WRP at y+10. Settings are chosen on TRAIN and scored on TEST.
- WRP shares replicate Step 2's category rules. The COW-to-ISO3 map is written out in `wrp_history.py`
  and checked against WPP population: the 2010 median WRP/WPP ratio is 0.99. Country-years that fail
  the population check (90 of 1,995) are dropped, not guessed.
- Score: population-weighted total-variation distance between predicted and WRP shares, in points.
  Lower is better.

## Results (population-weighted error, points; TEST = 1990 and 2000)
| model | chosen on TRAIN | TRAIN | TEST |
|---|---|---|---|
| persistence (no change) | - | 4.14 | 4.62 |
| demography: fertility gaps and age, no migration | phi 0.75, psi 0, multiplicative | 4.03 | **4.57** |
| + migration, neighbour/continent/world pools | same | 4.05 | 4.65 |
| + migration, gravity matrix | same | 4.04 | 4.63 |
| + momentum from the last decade's switching (lam 0.25) | gravity config | 3.71 | 5.03 |

What this says:
1. **Demography helps a little.** Fertility gaps and age structure beat persistence on the test decades,
   by about 1%. Most of the change in history is not demographic.
2. **Within-country fertility gaps are not identified.** Scores are flat from phi 0 to 1 on the test
   decades. Training prefers a non-zero gap, but the data cannot say how big it is. Treat the group-TFR
   table as a prior, not an estimate.
3. **Migration does not improve the hindcast**, whether pools or gravity. Its effect on shares is a few tenths of
   a point, which is within WRP noise.
4. **Momentum in past switching hurts recent history.** It helps in 1960-1970 and hurts from 1980 on
   (1990: 5.89 to 6.11; 2000: 3.37 to 3.95 at lam 0.25). The Step 5D switching scenario assumed recent
   switching would continue, so it is now a sensitivity only.
5. **Age-structure offsets (psi)** are preferred at 0 on TRAIN (4.08 vs 4.28 at psi 1) and flat on TEST.
   Step 5D's psi range is narrowed to 0-0.2 (and, on the unaffiliated share, larger offsets were
   consistently worse in the 1960-1980 decades).
6. **Signs of change are weak for the unaffiliated.** Demography predicts the direction of the unaffiliated share
   correctly in only 24% of countries that moved. Historical gains of the unaffiliated come from switching, which
   demography cannot produce.

## What the projection and group-TFR tables are, and are not
- They use the central settings (phi 0.5, psi 0, multiplicative gaps, gravity migration), not the fitted
  optimum, because the test cannot separate them.
- The migration table is only as good as the migration matrix. It is credible for South Asia to the Gulf.
  It is not credible for the USA (see the README_STEP5D limits), and it understates two-way corridors.
  A bilateral table (UN DESA International Migrant Stock 2020, origin by destination) is the most valuable
  input you could add.
- Group TFRs are model assumptions. Measured group fertility would come from DHS surveys by religion; I
  could not download them here. If you can export a country-by-religion fertility table, I can use it to
  replace the assumed multipliers.

## Limits
- WRP is noisy, and its population definitions differ from WPP in 90 country-years.
- 10-year hindcasts with 1950s-1960s data are weak (only about 60-90 countries).
- The test uses decades, not single years, so short shocks are averaged out.

## Sending results back, so they can be checked
From the step folder, after the runs:
```powershell
.\.venv\Scripts\python.exe export_results.py
```
This writes `results_step5\` (about 2 MB): the summary tables, the output of `verify_step5d.py`, the
headline shares by country, and `RESULTS_INDEX.md`, which records the git commit the results came from.
`data\` and `outputs\` stay out of git. Then push only that folder:
```powershell
git status
git add results_step5
git commit -m "Step 5 results from a local run"
git push -u origin audit/static-review
```
Check `git status` first: it should list only `results_step5/`. If `git push` says permission denied,
your Windows login may not have write access to the repository. In that case, zip the `results_step5`
folder and send it to the chat instead.

