"""Checks for the shift-share decomposition: the two parts must add up to the change exactly."""
import numpy as np
import pandas as pd

from step5d_diagnostics import holders, shift_share

rng = np.random.default_rng(3)
cats = ["Christianity", "Unaffiliated"]
rows = []
for year in (2020, 2050):
    for c, pop in zip(["AAA", "BBB", "CCC"], [5e6, 2e6, 9e6]):
        s = rng.dirichlet([1, 1])
        rows.append(dict(country_id=c, year=year, mean_population=pop * (1.1 if year == 2050 and c == "AAA" else 1.0),
                         mean_Christianity=s[0], mean_Unaffiliated=s[1]))
cu = pd.DataFrame(rows)
table, contrib = shift_share(cu, cats, 2020, 2050)
for c in cats:
    g0 = np.average(cu[cu.year.eq(2020)][f"mean_{c}"], weights=cu[cu.year.eq(2020)].mean_population)
    g1 = np.average(cu[cu.year.eq(2050)][f"mean_{c}"], weights=cu[cu.year.eq(2050)].mean_population)
    row = table.set_index("religion").loc[c]
    assert abs(row.change_pp - 100 * (g1 - g0)) < 1e-9, c
    assert abs(row.within_country_pp + row.population_weighting_pp - row.change_pp) < 1e-9, c
    assert abs(contrib[c].sum() - row.population_weighting_pp) < 1e-9, c
h = holders(cu, 2020, "Unaffiliated")
assert abs(h.sum() - 1) < 1e-12 and h.is_monotonic_decreasing and len(h) == 3
print("PASS: shift-share decomposition adds up exactly; holders sum to one")
