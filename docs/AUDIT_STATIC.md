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

## Needed to proceed
1. Allow outbound access to `correlatesofwar.org`, `population.un.org`,
   `naturalearth.s3.amazonaws.com` (or supply those files), and supply
   `data/raw/pew_2010_2020.xlsx` (manual Pew login).
2. Supply the existing `data/processed`, `data/features`, `data/models` and
   `data/forecasts*` folders (or let Step 2-5 regenerate them), so earlier
   results can be backed up before anything is replaced.
