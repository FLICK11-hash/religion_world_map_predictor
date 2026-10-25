# Findings

From the run committed in `results/`: 200 countries, 8 scenarios × 40 Monte Carlo runs, seed 2026,
reference scenario `stabilising`. Every number is in a CSV in that folder. The generated
`results/comparison_report.md` has the full tables; this page is the reading of them.

Read `docs/LIMITATIONS.md` first if you intend to quote any of this. In particular the bands below
are the spread of model outputs under parameter uncertainty, which backtests show is several times
narrower than actual forecast error.

## 1. The projection

World shares, reference scenario, mean with the 5-95% spread of runs:

| Religion | 2020 | 2050 | 2100 | 2200 | 3026 |
|---|---|---|---|---|---|
| Christianity | 28.8 | 27.9 (27.4-28.5) | 26.6 (25.1-27.8) | 23.4 (20.1-26.2) | 19.0 (12.4-26.7) |
| Islam | 25.6 | 31.7 (31.4-32.0) | 39.1 (38.1-39.8) | 43.2 (41.2-44.9) | 41.9 (35.3-48.5) |
| Unaffiliated | 24.2 | 20.5 (19.9-21.1) | 18.4 (16.9-19.9) | 21.5 (19.1-25.0) | 31.6 (25.1-39.0) |
| Hinduism | 14.9 | 14.5 (14.4-14.6) | 12.1 (11.8-12.4) | 9.1 (8.5-9.8) | 4.9 (2.9-7.8) |
| Buddhism | 4.1 | 3.1 (3.0-3.2) | 1.8 (1.6-2.0) | 0.9 (0.8-1.1) | 0.4 (0.3-0.6) |
| Folk/Traditional | 1.4 | 1.3 | 1.2 | 1.0 | 1.3 |
| Judaism | 0.2 | 0.2 | 0.3 | 0.3 | 0.4 |
| Other | 0.8 | 0.7 | 0.6 | 0.4 | 0.5 |

The striking feature of the near term is that **the unaffiliated share falls** even though
disaffiliation is the strongest single mechanism in the model. Section 2 explains why.

## 2. Global religious change is mostly about where people live

Two independent decompositions agree, and this is the main substantive result.

**Shift-share**, which splits each religion's change in world share into countries' own shares
changing and country populations growing at different rates (exact, 2020-2100, percentage points):

| Religion | Total change | Countries' own shares | Population weighting |
|---|---|---|---|
| Islam | +13.4 | +3.0 | +10.4 |
| Christianity | −2.2 | −7.9 | +6.5 |
| Unaffiliated | −5.8 | +6.3 | −12.5 |
| Hinduism | −2.8 | −0.5 | −2.4 |
| Buddhism | −2.3 | −0.9 | −1.7 |

The unaffiliated gain 6.3 points *inside* countries and lose 12.5 points because the countries
they live in — China, Japan, Europe — shrink relative to the world. Christians lose 7.9 points
inside countries and recover 6.5 because they are concentrated in fast-growing sub-Saharan Africa.
Islam's growth is three-quarters a matter of where Muslims live.

**Mechanism ablations**, the full model minus the same run with one mechanism switched off, on
identical draws (2100, percentage points of world population):

| Mechanism | Christianity | Islam | Unaffiliated | Countries changing largest group | Within-country diversity |
|---|---|---|---|---|---|
| Religious switching | −7.2 | −0.4 | +8.1 | +29.4 | +0.084 |
| Fertility differences within countries | −0.6 | +2.0 | −0.8 | −0.5 | +0.001 |
| Migration | −0.1 | +0.2 | −0.2 | −0.9 | −0.001 |
| All three together | −8.1 | +1.8 | +7.4 | +32.0 | +0.087 |

Switching dominates the Christian and unaffiliated shares and almost every change of a country's
largest group. Fertility differences *between religions inside a country* move the Muslim share by
2.0 points — the remaining 11.4 points of Islam's growth come from national demography and from
where Muslims live. Migration contributes almost nothing at world level, which it must, because
the model conserves people exactly; its effect is on individual countries.

Interactions are small: the three mechanisms separately sum to −7.9 for Christianity against −8.1
measured together.

## 3. More migration does not make countries more religiously mixed — unless migrants stop sorting

Rising migration minus low migration, paired run by run, in population-weighted within-country
diversity (Gini-Simpson). Positive means more migration leaves countries more mixed:

| Assumption about where migrants go | 2100 | 2200 | 3026 | Runs more diverse (of 12, at 2100) |
|---|---|---|---|---|
| Calibrated to Pew (κ = 0.5, λ = 0.65) | −0.001 | +0.002 | +0.001 | 3 |
| No destination affinity (κ = 0) | +0.003 | +0.012 | +0.065 | 12 |
| Migrants mirror their origin | +0.013 | +0.042 | +0.095 | 12 |

With the destination affinity visible in today's migrant stocks — migrants move disproportionately
to countries where their religion is already common — doubling or halving migration changes
within-country diversity by almost nothing, and the sign is not even consistent across runs. Take
the affinity out and the familiar result appears: more migration, more mixing.

The model therefore does not build in rising diversity, and the question has a clear empirical
test: Pew's corridor-level data on the religion of migrants would pin κ down far better than the
19 aggregate figures it is currently fitted to.

## 4. Which countries change

Countries whose largest religious group changes, in a majority of runs:

| Scenario | 2050 | 2100 | 2200 | 3026 |
|---|---|---|---|---|
| stabilising (reference) | 6 | 24 | 62 | 118 |
| continued secularization | 6 | 26 | 113 | 189 |
| high retention | 3 | 12 | 27 | 65 |
| combined dispersal | 6 | 28 | 102 | 141 |
| the four migration variants | 6 | 24 | 59-64 | 112-123 |

Migration scenarios barely move this count; switching assumptions move it by a factor of two to
three. By 2100 the 24 changes in the reference scenario are almost all Christian-majority
countries becoming unaffiliated-majority: Australia, Austria, Belgium, Canada, Germany, the United
Kingdom, France, Spain, Sweden, Finland, Switzerland, Estonia, Slovenia, Norway, Italy, Chile,
El Salvador, Nicaragua, Belize and the United States, plus Singapore and Mongolia (from Buddhism),
Taiwan (from folk religion) and North Macedonia (to Islam).

Two of these deserve a flag. **The United States** changes in 62% of runs — close enough to the
boundary that the result turns on the fertility and switching inputs rather than on anything
robust. **Taiwan and China** inherit the folk-religion classification problem described in
`docs/LIMITATIONS.md`.

## 5. Against an independent published projection

Pew Research Center's 2015 report projected the same quantity to 2050. Change in world share,
2020-2050, as each projects it:

| Religion | This model | Pew 2015 | Difference |
|---|---|---|---|
| Islam | +6.1 | +4.8 | +1.3 |
| Unaffiliated | −3.7 | −2.4 | −1.3 |
| Christianity | −0.9 | +0.2 | −1.1 |
| Buddhism | −1.0 | −1.4 | +0.4 |
| Hinduism | −0.4 | −0.3 | −0.1 |

Two independently built models agree on the direction for every group, and on magnitude within
1.3 points over thirty years. The differences are in the expected direction: this model has an
explicitly estimated switching mechanism and projects faster Christian decline and faster
unaffiliated decline (the latter because it weights China's shrinking population more).

Regionally the agreement is closer for sub-Saharan Africa and North America than for Latin
America, where this model projects Christianity down 8.0 points against Pew's 0.8. That gap is
entirely the switching model, which is fitted to recent disaffiliation in Brazil, Mexico and
Chile that Pew's 2015 vintage did not have. Whether that is an improvement or an overshoot is an
open question the next decade of data will settle.

## 6. Forecast skill, and what it costs to be honest about uncertainty

On the WRP decades, population-weighted total-variation error in percentage points:

| Model | 1990-2010 | all 1970-2010 |
|---|---|---|
| Persistence | 4.623 | 4.406 |
| Births and deaths only | 4.579 | 4.378 |
| + migration | 4.580 | 4.381 |
| + switching, full strength | 4.487 | 4.797 |
| Extrapolate the last decade | 6.829 | 5.854 |

The mechanistic model beats "nothing changes" by about 3% of the error, and extrapolation is far
worse than either. Of the datasets added, only the UN bilateral migrant stocks measurably improved
the migration component (1990-2010: −0.062 against persistence, the best of any variant).

The interval calibration is the uncomfortable result: nominal 90% intervals contain the observed
share 13-19% of the time, and would need to be 2.7 to 19 times wider to cover the error actually
made. Section 1 of `docs/LIMITATIONS.md` has the detail. The honest near-term statement the model
can support is the out-of-sample one: at a ten-year horizon the 90th percentile of absolute error
is 7.3 points for a country's Christian share and 5.4 for its unaffiliated share.

## 7. Diversity

Population-weighted within-country diversity (Gini-Simpson, the chance two residents differ in
religion) rises from 0.288 in 2020 to 0.33-0.36 in 2100 in every scenario. The ablations attribute
essentially all of that rise to religious switching creating large unaffiliated minorities inside
Christian-majority countries, not to migration.

After 2200 the scenarios separate sharply, and `persistent_fertility_gaps` collapses to 0.17 by
3026 as the highest-fertility group becomes dominant nearly everywhere. That is the point of the
scenario rather than a prediction: it shows what never-converging fertility differences would
imply, and it is the clearest illustration of why the long horizons are labelled exploratory.

## 8. What the results turn on

The global sensitivity analysis regresses each outcome on all 23 drawn parameters at once, on a
120-run Monte Carlo design of the reference scenario, separate from the projection runs. The
parameters are drawn independently and the largest correlation between any pair is 0.24, so the
coefficients can be read one at a time.

Standardised rank regression coefficients at 2100 (standard deviations of the outcome per standard
deviation of the parameter):

| Outcome | Strongest parameter | Coefficient | Next | R² |
|---|---|---|---|---|
| Christian world share | `survey_weight` | −0.89 | `tfr_dev_half_life` −0.17 | 0.77 |
| Unaffiliated world share | `survey_weight` | +0.72 | `tfr_dev_half_life` +0.19 | 0.63 |
| Muslim world share | `Hf` (fertility-gap half-life) | +0.57 | `survey_weight` +0.51 | 0.77 |
| Within-country diversity | `survey_weight` | +0.29 | `turnover` −0.26 | 0.29 |

**The single most influential assumption in the model is not demographic.** `survey_weight` decides
whether a run uses switching at the level fitted to historical net change (Christians leaving at
11.7 per 100 raised) or the higher level Pew's 117-country survey reports (17.1). That one choice
moves the 2100 Christian share nearly a full standard deviation, and it exists because the two
sources of evidence disagree. The clearest way to improve the model is therefore better switching
measurement — Pew's Spring 2024 microdata and ISSP 2018 would largely settle it — not better
demography.

For the Muslim share the leading parameter is `Hf`, how fast fertility differences between
religions inside a country converge, which is consistent with the ablation result that
within-country fertility differences are what the Muslim share is sensitive to.

R² falls with horizon — 0.85 for the Christian share at 2050, 0.77 at 2100, 0.40 at 3026. No single
assumption explains the long run; the parameters interact. That is a further reason to read 2500
and 3026 as illustrations rather than as projections.
