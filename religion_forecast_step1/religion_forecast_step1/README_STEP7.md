# Step 7: switching, migration and generations in one demographic model

Step 7 builds on the Step 5D cohort model. Each country's population is split by religion, generation (native, first and second generation of immigrants) and five-year age group. The population then changes through six recorded mechanisms:
- births and deaths;
- religious switching;
- emigration;
- immigration;
- a residual that is only used if history tests support it.

People who migrate leave one country and arrive in another. Every share change is broken down by the mechanism that caused it.

Earlier steps and their outputs are untouched. Step 7 writes only to `data/forecasts_step7/`, `data/validation_step7/`, `outputs/maps_step7/`, `outputs/maps_step7_svg/` and `outputs/step7_comparison_report.md`, all git-ignored. The one exception is `step7_report.py --export`, which writes small tracked copies to `results_step7/`.

Data sources, coverage, licences and manual downloads are in [`docs/STEP7_DATA_SOURCES.md`](../../docs/STEP7_DATA_SOURCES.md). The results of the build run are in [`docs/STEP7_COMPARISON_REPORT.md`](../../docs/STEP7_COMPARISON_REPORT.md).

## Run (Windows PowerShell, from this folder)

```powershell
cd C:\Users\conra\religion_world_map_predictor\religion_forecast_step1\religion_forecast_step1
git pull --no-edit
.\.venv\Scripts\python.exe step7_fetch_data.py      # optional inputs -> data\raw\step7 (once; needs internet, git for mirrors)
.\.venv\Scripts\python.exe test_step7.py            # unit + integration tests (about 30 s)
.\.venv\Scripts\python.exe step7_validate.py        # history tests, data ablations, foreign-born check (about 10 min)
.\.venv\Scripts\python.exe step7_forecast.py        # 8 scenarios x 40 runs (30-40 min); --quick for 8 runs
.\.venv\Scripts\python.exe verify_step7.py          # integrity checks; exit code 0 = all passed
.\.venv\Scripts\python.exe step7_make_maps.py       # PNG maps and charts in the Step 6 style
.\.venv\Scripts\python.exe step7_maps_svg.py        # the same maps + a world-shares chart as SVG, index.html (no matplotlib)
.\.venv\Scripts\python.exe step7_report.py          # outputs\step7_comparison_report.md from your run
.\.venv\Scripts\python.exe step7_sensitivity.py     # optional: who-migrates-where sensitivity (about 15 min)
explorer .\outputs\maps_step7
```

If `data\processed\pew_harmonized.csv` is missing, run Step 2 first (`.\.venv\Scripts\python.exe step2_clean_merge.py`, which reads `data\raw\pew_2010_2020.xlsx`). Step 7 then fits and tests the Pew 2010-2020 window, which the build environment could not do. No new Python packages are needed: numpy and pandas, plus matplotlib and geopandas for the PNG maps. `step7_fetch_data.py` uses `requests`, and `openpyxl` reads the UN workbook (both already used by Steps 1-2).

## Files

| File | Role |
|---|---|
| `step7_engine.py` | State `[country, religion, generation, age]`; life tables (e0 and under-5 mortality); births, survival, switching, residual; exact component accounting |
| `step7_switching.py` | Lifetime → age-specific transition matrices; hierarchical empirical-Bayes model; linear share effects |
| `step7_migration.py` | Gravity and network kernels; Sinkhorn flows to WPP margins; post-2100 rule; who migrates (selectivity); conserving realisation |
| `step7_data.py` | Every loader, with a record of what was found |
| `step7_model.py` | Context, run parameters, demography to and after 2100, fertility, switching and migration plans, initial state, `simulate`, `hindcast` |
| `step7_estimate.py` | Hindcast evidence for switching; switching fit; selectivity and survey-level calibrations |
| `step7_residual.py` | Ridge residual learner (zero-sum) |
| `step7_validate.py` | Forward-chaining history tests, data ablations, out-of-sample choices |
| `step7_forecast.py` | Scenario × Monte Carlo runs and all CSV/JSON outputs |
| `step7_map_data.py`, `step7_make_maps.py`, `step7_maps_svg.py` | Map definitions; PNG (matplotlib/geopandas, Step 6 helpers); SVG/HTML |
| `step7_report.py`, `verify_step7.py`, `test_step7.py` | Report, integrity checks, tests |
| `step7_sensitivity.py` | Same-seed reruns of the migration scenarios with three assumptions about the religion of migrants (calibrated, no destination affinity, mirror origin) |
| `step7_fetch_data.py` | Downloads, mirrors, converters, manifest with SHA-256 |
| `step7_assumptions.json` | Every non-data number, each tagged `observed`, `estimated`, `assumption` or `unverified` |
| `step7_inputs/` | Published figures with citations (tracked) |

## The model

**State.** `P[c, r, g, a]` holds persons by country *c* (200), religion *r* (8), generation *g* and age group *a* (17 five-year groups, 80+ open). The generations are: 0 = natives (third generation or later), 1 = foreign-born, 2 = native-born children of foreign-born mothers. The step is five years, from 2020 to 3030; 3026 is interpolated as 0.8·3025 + 0.2·3030.

**1. Survival.** `P[a+1](t+5) = s_a · P[a](t)`, with `s_a = 5L(a+1) / 5L(a)` from a life table. The table is fitted to WPP life expectancy and under-5 mortality. Its hazard is `0.0004 + c·exp(-0.9x) + b·exp(0.09x)`, with *c* set by under-5 mortality and *b* by life expectancy. The open 80+ group survives at `T85/T80`. Mortality is the same for all religions (no data say otherwise).

**2. Births.** Births over the step to mothers of group (r, g) are `TFR_c · k_c · rel[c,r,g] · Σ_a f_c(a) · W[c,r,g,a]`.
- `W` is women-years: the female share by age (WPP) × the mean of the start and end populations.
- `f_c` is a fertility age pattern centred on the WPP mean age at childbearing.
- `k_c` makes the national total reproduce the WPP TFR exactly.

`rel` is the group's relative fertility:
- Without country data it is `1 + φ·(Pew global ratio − 1)` plus country noise, blended additive/multiplicative by `w_add`. Gaps converge with half-life `Hf`, except in `persistent_fertility_gaps`.
- First- and second-generation mothers get multipliers (ranges in `step7_assumptions.json`).
- Verified rows in `religion_fertility_observed.csv` replace `rel` for that country.

The child takes the mother's religion. Generation maps g0→g0, g1→g2, g2→g0.

**Calibration (to 2100 only).** After births, each country is scaled uniformly so its natural growth over the step equals WPP's: `(P_WPP(t+5) − N_WPP) / P_WPP(t)`. This acts like a common correction to fertility and mortality. It does not change shares, never touches migrants, and lets migration scenarios move totals away from WPP.

**3. Switching.** A survey's lifetime matrix `L[r,s]` (share of those raised in *r* now in *s*) is not an annual rate. Step 7 parameterises it by three lifetime probabilities:
- `d_r`: raised in *r*, now unaffiliated;
- `v_r`: raised in *r*, now another religion, with destinations in proportion to local prevalence;
- `a`: raised unaffiliated, now any religion.

It spreads switching over ages 15-49 with weights `(0.20, 0.27, 0.22, 0.14, 0.09, 0.05, 0.03)`. The five-year matrices `T_a = I + w_a·(L* − I)` are solved (Newton plus a fixed-point refinement) so that their product over ages reproduces `L`. At realistic rates the →unaffiliated column is reproduced within 0.3 points and the diagonal within 1 point. Generation intensities scale switching for the foreign-born (0.3-0.6) and the second generation (0.4-0.8).

Rates come from a hierarchical model:
- `logit d[c,r] = μ_d[r] + δ + β_d·z_c(t) + τ_u·ξ_c + τ_e·ξ_{c,r}`
- `logit a[c] = μ_a + β_a·z_c + τ_a·ξ'_c`

Here `z` is a development index (standardised WPP life expectancy and −log TFR, capped at the most developed observed level). The hyperparameters `δ`, `β_d` and `τ_u` are chosen by maximising the marginal likelihood over a grid (empirical Bayes). Country effects are then posterior draws, by importance weighting.

The evidence comes from two sources:
- **Net change.** Demographic hindcasts of each historical decade, run without switching, leave a residual `y = observed − hindcast`. Its link to the rates is the first-order effect of switching on shares (exposure of each religion to switching ages); it matches exact simulation within 0.05 points. The likelihood is Student-t, robust to source breaks. Because the hindcast already contains births, deaths, ageing and migration, only the unexplained part is attributed to switching, so nothing is counted twice.
- **Surveys.** Verified cells enter a binomial likelihood.

Pew's 2025 survey of 117 countries (adults 18-54) then fixes a second, "survey" level per religion through a logit shift. Each run draws a weight between 0 (fitted level) and 1 (survey level), because the two disagree for Christians and Buddhists.

Scenarios can add a time trend, shift retention or affiliation, link rates to development after 2100, and add a slow random drift (logit random walk) after 2100.

**4-5. Migration.** `F[o,d]` holds persons moving over the step.
- **Margins to 2100:** emigrants `E_c = 5·turnover·m_c·pop_c + max(−N_c, 0)` and immigrants `I_c = 5·turnover·m_c·pop_c + max(N_c, 0)`, where N is WPP net migration × the scenario multiplier.
  - `turnover` (0-0.0004 per year) is calibrated on migrant stocks. Simulations from the UN 1990 foreign-born stocks to 2020 match the UN 2020 stocks best in this range; the population-weighted error of foreign-born shares is 0.91 points at 0.0002, against 1.76 for persistence. Higher rates, such as the 0.0016 implied by gross flow estimates, overshoot. The model counts a returning emigrant as foreign-born, so gross churn is understated while foreign-born stocks stay right.
  - `m_c` is the country's observed mobility: UN immigrant plus emigrant stock per person, normalised to a population-weighted mean of 1 and clipped to 0.05-10. The forecast uses the 2020 table; history tests use the table of their start year. Without it, India and China (low mobility, 0.23 and 0.14) would generate the world's largest flows just from their size.
  - A country cannot receive more than all others send. If one country were most of the world, its circulation would be cut in both directions, leaving its net unchanged. With real 2020-2100 margins this never binds; the largest is the USA at 26% of all flows.
- **Pattern:** the kernel `K = (1 − ω)·UN bilateral stock + ω·gravity`. Gravity is distance^−1.5 × (1 + 2·land border) × (1 + 0.5·same continent).
- **Flows:** Sinkhorn scaling fits `F = a·K·b` to E (rows) and I (columns) with softness ρ: `a = (E / K b)^ρ`, `b = (I / Kᵀa)^ρ`.
  - ρ = 1 enforces WPP's margins exactly. WPP's projected margins are partly inconsistent with the migrant network. For example, Pakistan keeps emigrating 0.5-1 million a year while Gulf net immigration falls to almost zero after 2030. Exact margins then force those emigrants into whichever countries have positive net immigration: Pakistan would supply 46% of the UK's immigrants in 2020-2050, against 8% of its 2020 foreign-born.
  - With ρ < 1, both margins give way, and national populations drift a little from WPP (median 2-4% by 2100). Each run draws ρ from 0.5-1.
  - The 1990-2020 corridor test in `step7_validate.py` fits destinations' origin mixes best near 0.75.
- **After 2100:** `E_c = rate_c(2095-2100) × multiplier × pop_c`. Destinations keep their 2100 attraction, which falls with their own growth (congestion θ) and, in `changing_migration`, rises with population ageing.
- **Who moves where:** each corridor (o, d) has its own religious mix, `m[o,d,r] ∝ avail[o,r] · share_o,r^(−λ) · (share_d,r + 0.01)^κ`. Here `avail` is the persons who can move (age and generation propensity) and λ is the minority effect (minorities emigrate more). κ is destination affinity: Pew (2024) reports that migrants tend to move where their religion is common. κ and λ are fitted on a grid so that the UN 2020 bilateral stocks reproduce Pew's published religious composition of migrants (19 targets: world, Europe, MENA, India-born, US foreign-born). This fits far better than "migrants mirror their origin", and better than eight global religion propensities, which also pushed every country's composition the same way over centuries. The fitted values and errors are in `step7_report.json`.
- **κ decides what migration does to diversity.** `step7_sensitivity.py` reruns the migration scenarios with the same random draws under three assumptions: calibrated κ and λ, κ = 0, and migrants mirroring their origin. With the calibrated κ, rising and low migration end with almost the same within-country diversity. With κ = 0, more migration makes countries clearly more diverse. κ comes from 2020 migrant stocks (19 aggregate targets); whether migrants keep sorting toward co-religionists for centuries is an assumption, so this is the migration setting to watch.
- **Cap:** no cell (religion × generation × age) can lose more than half its people in five years. Full cells are capped and the remainder is redistributed to cells with room (water-filling).

Immigrants at d are `Σ_o F[o,d] · m[o,d,r]`, split by age like the emigrants they are, so the same persons leave and arrive. They arrive as first generation. Worldwide, migration changes no religion's numbers.

**6. Residual.** A ridge regression on start-of-decade conditions predicts what the mechanisms miss. It is used only with the weight chosen out of sample, and that weight is 0.

**After 2100.** National TFR converges to a long-run level (1.6-2.1) with a half-life of 50-150 years and a persistent country deviation. Life expectancy rises 0.02-0.06 years per year to a cap of 90-95. Under-5 mortality falls with life expectancy.

**Accounting.** Each step records persons by component (births, deaths, switch_in/out, emigration, immigration, residual, calibration) and share change by sequential sub-step, for each country and for the world. They add up exactly to the simulated change, and `verify_step7.py` checks this against the mean shares.

**Diversity.** The Gini-Simpson index `1 − Σ s_r²` is the chance that two residents differ in religion. It runs from 0 to 0.875 for eight groups. The effective number of religions is `1 / Σ s_r²`.

## Scenarios

| Scenario | Switching | Migration | Fertility gaps |
|---|---|---|---|
| `stabilising` (reference) | development link to 2100, then held; small drift | WPP to 2100, then 2100 rates | converge |
| `continued_secularization` | development link throughout, +0.6 logit/century to 2300, less return | as reference | converge |
| `high_retention` | retention +, return +, −0.3 logit/century to 2300 | as reference | converge |
| `rising_migration` | as reference | ×2 by 2100, ×3 by 2200, ×4 by 3030 (net and circulation) | converge |
| `low_migration` | as reference | ×0.5 by 2100, ×0.25 by 3030 | converge |
| `changing_migration` | as reference | ×1.2-1.5; networks fade into geography by 2100; pull from population ageing | converge |
| `persistent_fertility_gaps` | as reference | as reference | persist |
| `combined_dispersal` | as continued secularization | as rising migration | persist |

The spread within a scenario is model and parameter uncertainty. Differences between scenarios are scenario uncertainty. Run *r* uses the same random draws in every scenario (common random numbers), so a difference between two scenarios comes from their assumptions, not from sampling noise. `uncertainty_model_vs_scenario.csv` separates the two. **2500 and 3026 are speculative scenarios, not predictions.**

## Estimated versus assumed

`data/forecasts_step7/parameter_provenance.csv` lists every parameter with its status. In short:
- **Observed:** start shares (Pew 2020); WPP demography to 2100; WRP history; UN migrant stocks; age structures; survey cells; Pew published figures.
- **Estimated from data:**
  - switching hyperparameters and country effects;
  - the survey-level shifts;
  - the religion of migrants (destination affinity κ and minority effect λ);
  - the circulation range, calibrated so that 1990-2020 simulations from the UN 1990 foreign-born stocks reproduce the UN 2020 stocks (`step7_validate.py`, `migration_foreign_born_check.csv`), and each country's mobility (UN stocks);
  - the centre of the margin softness ρ (0.75, best 1990-2020 corridor fit; the 0.5-1 range is an assumption);
  - the residual weight (history tests: 0, so the forecast has no residual).
- **Assumption:**
  - switching strength 1 (the fitted rates are used as they are). The history tests do not settle it. Over all four windows, no switching scores best, because the two earliest folds were fitted on only two or three noisy WRP decades. On 1990-2010, where the fit had four or five decades, full strength scores best, and surveys observe switching directly. How much switching there is stays uncertain; each run mixes the fitted and survey levels;
  - the within-country fertility gap fraction φ (history cannot identify it, as Step 5E showed);
  - age patterns of switching and migration;
  - generation intensities (informed by published retention);
  - all demography after 2100;
  - the scenario settings.
- **Unverified:** Pew global fertility by religion other than Muslims (3.1) and Christians (2.7); Pew global median ages by religion.

## Outputs (`data/forecasts_step7/`)

- `country_year_by_scenario.csv`: means and 5-95% bands of every religion's share; dominant group (modal and of means) with agreement; diversity; foreign-born and second-generation shares.
- `country_year_uncertainty.csv` and `global_share_uncertainty.csv`: the reference scenario, in the Step 6 format.
- `global_share_by_scenario.csv`; `world_population_by_scenario.csv`.
- `components_country_period.csv` and `components_world_period.csv`: persons by mechanism and share points by sub-step, per period (2020-50, 2050-2100, 2100-2200, 2200-2500, 2500-3030).
- `migration_country_period.csv`: immigrants and emigrants by religion. `migration_corridors_reference.csv`: largest corridors.
- `dominant_change.csv`: probability that the dominant religion changes by each target year.
- `switching_rates_2020.csv`; `switching_check_vs_pew.csv`; `uncertainty_model_vs_scenario.csv`.
- `parameter_provenance.csv`, `run_parameters.csv`, `step7_report.json`.
- `sensitivity_migrant_sorting.csv` (from `step7_sensitivity.py`): diversity, dominant changes and world shares per run under each migrant-religion assumption.

`data/validation_step7/`, from `step7_validate.py`:
- `validation_summary.csv` and `validation_by_window.csv`: history-test scores by model and window;
- `data_ablations_summary.csv`: what each dataset adds;
- `switching_fit_by_fold.csv` and `out_of_sample_choices.csv`;
- `migration_foreign_born_check.csv` and `migration_foreign_born_by_country.csv`: simulated vs UN foreign-born shares, 1990-2020;
- `step7_validation_report.json`: the best options, and what the forecast uses.

`step7_report.py --export` copies the small files and a trimmed country table to `results_step7/`, which is tracked in Git.
