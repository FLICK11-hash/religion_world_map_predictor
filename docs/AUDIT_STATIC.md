# Static audit of Steps 5 / 5B / 5C (code reading only)

**Status:** nothing was executed. `data/` and `outputs/` are git-ignored and the
raw-data hosts were blocked in the audit environment, so every statement below
comes from reading `step5_forecast_scenarios.py`, `step5b_dynamic_scenarios.py`
and `step5c_evidence_sensitivity.py`. Claims about data (country matching,
Muslim-plurality outcomes, validation numbers) are **not yet checked**.

## Confirmed by the code

1. **Why changes freeze after ~2100-2200 (5C).** Each 5-year step adds
   `strength * movement5 * 2**(-(year-2020)/H)`, H~U(25,65). That decays the
   *rate*, so shares converge to a fixed limit: the cumulative shift is
   `strength*movement5*sum_k 2**(-5k/H)`, i.e. roughly 1.5-8 times the observed
   2010-2020 decade change, then zero. By 2200 the factor is 0.007 (H=25) to
   0.15 (H=65). Residual noise is also multiplied by `exp(-(year-2100)/80)`, so
   Monte Carlo spread *shrinks* with horizon, the opposite of real uncertainty.
   Steps 5/5B do the same: LightGBM weight is 0 from 2200 (`model_weight`),
   secularization decays (`exp(-(year-2100)/25)` in 5, `/100` in 5B), noise
   decays (`/130`).
2. **Population never feeds back into shares.** `state.step()` updates TFR, age
   and population, but shares are updated independently of them. Demography
   enters only through (a) a national-TFR multiplier on an arbitrary logit tilt
   and (b) Europe/continent mixing weights up to 2100. There is no
   births/deaths/age structure by religion. Post-2100 demography is cosmetic
   for shares.
3. **LightGBM is only loaded in 5C.** `load_sources()` requires the joblib, but
   `simulate()` in 5C never calls `get_lgbm_prediction`. In 5B it is blended
   with alpha~U(.04,.13) to 2100 and fades to 0 by 2200. It is WRP-trained but
   applied to Pew-defined states (definition mismatch). Persistence beat it in
   validation (per README_STEP4), so low weight is defensible, but 5C's
   "models" are really just damped Pew momentum plus assumptions.
4. **Double counting.** Pew 2010-2020 net change already contains differential
   fertility, switching and migration. 5C then adds a group-growth tilt
   (`group_growth_sensitivity`) or Europe migration mixing
   (`europe_migration_sensitivity`) on top of that momentum.
5. **Arbitrary group-growth coefficients (5C).** Offsets
   `{Christianity .3, Islam .7, Buddhism -.8, Unaffiliated -.7}`, others 0,
   scaled by `national_scale = clip(TFR/2.1,.7,1.4)`. National TFR is used as
   a proxy for group fertility, so high-TFR countries (e.g. Africa) get a bigger
   Islam/Christianity tilt irrespective of any Muslim-Christian fertility gap
   there. Hindus, Jews and Folk are fixed at 0.
6. **Random group advantages (5B).** `growth_adv ~ N(0,.0025)` per
   country x religion x run, applied as `exp(5*adv*tfr_factor*att)` each step
   with attenuation floor 0.28 after 2100. This is a persistent random drift
   (about +/-20% relative by 2100; about +/-90% over 1,000 years), with no
   evidence behind it. It acts as noise, not a mechanism.
7. **Uniform secularization (5/5B).** `transfer_to_unaffiliated` moves the same
   fraction of every non-Unaffiliated group in every country to Unaffiliated
   (Unaffiliated is column -1), one-way only. No religion- or country-specific
   rates, no return flow, even where Unaffiliated already dominates.
8. **Migration.** 5B: any country with positive inflow is mixed toward the
   *unweighted continental mean* (up to 6% per step). That is regression to the
   mean, not migration: a Gulf state is pulled toward the Asian average, and
   emigration is ignored (`max(flow,0)`). 5C: Europe only, to 2100, arrivals are
   assumed 25-50% Muslim plus the continental non-Muslim mix. Pure what-if,
   no origin-country data. Pew's 2017 Europe migration scenarios are the
   obvious external reference (citation to verify).
9. **Pooled ensembles include the persistence run (5C).**
   `prior.group_outputs(mem_sh, ..., labels, ...)` pools all 400 runs, 100 of
   which are persistence, so the country means, quantiles, "dominant agreement"
   and global bands in `country_year_uncertainty.csv` /
   `global_share_uncertainty.csv` are diluted 25% toward 2020. Persistence is
   also run 100 times although it is deterministic.
10. **Modal winner vs mean winner.** `summarize_scenarios` (5B, 5C) and
    `group_outputs` use the per-run `argmax` frequency (`np.bincount(...).argmax()`),
    so ties go to the lowest index (Christianity, then Islam). `step6_make_maps.py`
    line ~104 instead uses argmax of the mean share. The two definitions can
    disagree for close countries, so the "countries changed" table (5C, modal)
    and the Step 6 maps (mean) are not the same metric.
11. **Clipping non-conservation.** 5C `simplex()` clips negatives to 0 and
    renormalizes after adding additive pp momentum, so small groups can be
    zeroed and the remaining mass silently rescaled. Zero shares then make
    logit tilts inert (`log(1e-12)`).
12. **Silent defaults.** Countries missing from WPP get population 1e6 (then
    carried forward) and TFR 2.1; countries missing a Pew 2010 baseline get
    zero momentum. Both bias global population-weighted shares and the
    "changed dominant" counts. The number of affected countries is reported
    nowhere in 5C.
13. **Monte Carlo = parameters + iid noise.** Parameters are uniform draws over
    ranges with no justification, and noise is iid per country per step with no
    spatial or temporal correlation. Band widths therefore reflect the chosen
    ranges, not evidence.

## Checked and fine
- 3026 = `0.8*s3025 + 0.2*s3030` (log-interp for population) is the right
  1/5 interpolation of the 3025-3030 step.
- Lag bookkeeping in `GeographyState.step` is correct (lag10 <- lag5, lag5 <- current).
- `PEW_2050_PCT` matches Pew's 2015 projections (31.4/29.7/14.9/5.2/0.2/4.8/0.7/13.2; sums to 100.1).
- Folk/Other redistribution in `momentum_from_pew` preserves zero-sum change.

## Not yet verified (needs data)
Country matching (Kosovo `XKX` is user-assigned; Taiwan/Palestine/W. Sahara
WPP gaps), WPP units for `net_migrations`, the Muslim-plurality question (Sec. 6
of the task), validation tables, Pew 2050 comparison on the actual outputs.

## Data checks run (WRP, WPP2024, Natural Earth only)

Run read-only on the supplied raw files (checksums: WRP `ba1f3b73...`, WPP `286ac36b...`,
NE `5fed4333...`). geopandas was unavailable, so the Natural Earth `.dbf` attribute table was
read directly (no geometry). Pew, the COW->ISO crosswalk (needs network) and `data/processed|features|models|forecasts*`
were NOT available, so nothing downstream was re-run.

- **WPP units:** `NetMigrations` is in thousands (2020: `NetMigrations / (CNMR*pop/1000)` has median 1.000,
  range 0.993-1.077). `TPopulation1July` is also in thousands. Step 2's `*1000` conversions are correct.
- **WPP coverage:** 237 ISO3 country rows, 1950-2101, Medium only, no duplicates. Taiwan (TWN), Palestine (PSE),
  Western Sahara (ESH), Hong Kong, Macao and Kosovo (XKX) are all **present** in WPP2024 with full series, so
  the "Taiwan/Palestine/W. Sahara WPP gaps" worry above does not apply to this file. 2101 is empty for every country
  (TFR, population, net migration, median age are NaN); the forecast code must not read 2101.
- **WPP vs map:** 9 WPP codes have no Natural Earth polygon: BES, GIB, GLP, GUF, MTQ, MYT, REU, TKL, XKX
  (about 4.0M people in 2020 of 7.89B, 0.05%). Five are French overseas departments that NE 50m folds into France,
  so Step 5 would carry them as countries but they cannot be drawn.
- **Kosovo:** NE `ISO_A3` is -99 and `ADM0_A3` is `KOS`; WPP and Step 2 use `XKX`. Step 6 fixes this with
  `MAP_CODE_FIXES`, but `step2_clean_merge.load_map()` yields `KOS`, so any Step 2 join of WPP/Pew to `map_iso3`
  would miss Kosovo. Not confirmed against actual Step 2 output.
- **Map polygons with no WPP data:** Somaliland (SOL), N. Cyprus (CYN), Kosovo (KOS, alias issue above), Åland (ALA),
  Pitcairn, Norfolk Is., plus uninhabited/ocean territories. Those draw as blank.
- **NE -99 ISO codes:** France and Norway have `ISO_A3 = -99`; the `ADM0_A3` fallback (FRA, NOR) is correct.
- **WRP 2010:** 194 states, no missing population. A crude check `sumrelig/pop` falls outside 0.99-1.01 for 60 of 194
  states (Japan 1.66, Haiti 1.37, Cuba 1.29 above; Barbados 0.86 to Paraguay 0.99 below). This is only a proxy,
  because Step 2 validates the sum of the share columns and `sumrelig` can include dual affiliation. The real number
  of WRP 2010 rows dropped by `quality_pass` still needs Step 2's output.

Still unverified: Pew country matching, the COW crosswalk, Muslim-plurality outcomes, validation tables and the
Pew 2050 comparison on actual outputs.

## How Step 5D relates to these findings

Step 5D (`step5d_cohort_forecast.py`, see `README_STEP5D.md`) is a new model, not a patch. Mapping:

| Audit item | In 5D |
|---|---|
| 2 population never feeds shares | Fixed: shares are computed from group populations (births, deaths, migration). |
| 4 double counting of Pew momentum | Reduced: demography is explicit, and only the part Pew 2020 shows beyond a no-switching hindcast is treated as switching. |
| 5 arbitrary group-growth offsets | Replaced by Pew global TFR ratios damped by `phi` (range is a judgement; `hindcast_phi_scan.csv` shows what the data prefer). |
| 6 random group advantages | Removed. Uncertainty is parameter ranges plus one persistent country x group draw per run. |
| 7 uniform one-way secularization | Replaced by country-specific net switching estimated from the hindcast, decaying over time. |
| 8 migration as regression to the mean | Replaced: leavers carry their origin's religious mix; arrivals use a bilateral origin-destination table when supplied (`data/raw/migrant_bilateral.csv`), otherwise neighbour/continent/world pools. Still no migrant-religion data beyond origin composition. |
| 10 modal vs mean winner | Both reported (`most_likely_dominant` and `mean_dominant`, plus both change counts). |
| 11 clipping non-conservation | Persons are conserved in switching and migration; verified in unit tests. |
| 12 silent defaults | Counts of WPP-default and no-Pew-2010 countries are written to `step5d_report.json`. |
| 1, 3, 9, 13 | Not changed: 5D has no LightGBM, no pooled persistence run, and post-2100 demography is still the stylised rule. |

Not yet verified on real data: country matching of the new loaders, the hindcast fit, and whether the cohort engine tracks WPP growth (reported as the rescale size).

## Step 5E history tests (WRP 1950-2010; see religion_forecast_step1/README_STEP5E.md)

Out of sample (chosen on 1960-1980, scored on 1990 and 2000), population-weighted error in points:
persistence 4.62; demographic fertility gaps 4.57 (small gain); pools 4.65; gravity migration 4.63;
momentum in switching 5.03 (worse). Consequences for the audit:
- Item 3 (LightGBM) and item 4 (double counting): the history supports demography only weakly, and it does not
  support extrapolating recent switching. The Step 5D headline is now demography-only, with switching a sensitivity.
- Item 5 (arbitrary group growth): within-country fertility gaps cannot be identified from history (flat on test).
- Item 12 (silent defaults): the history test drops 90 WRP country-years that fail the population check.

## Needed to proceed
1. Allow outbound access to `correlatesofwar.org`, `population.un.org`,
   `naturalearth.s3.amazonaws.com` (or supply those files), and supply
   `data/raw/pew_2010_2020.xlsx` (manual Pew login).
2. Supply the existing `data/processed`, `data/features`, `data/models` and
   `data/forecasts*` folders (or let Step 2-5 regenerate them), so earlier
   results can be backed up before anything is replaced.
