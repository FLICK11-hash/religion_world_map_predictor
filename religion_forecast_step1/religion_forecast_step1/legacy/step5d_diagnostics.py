"""Diagnostics for Step 5D outputs: where a change in a world religion share comes from.

A world share is a population-weighted average of country shares. So its change splits exactly into
  within-country change   sum_c w1_c * (s1_c - s0_c)   (fertility, age, migration, switching inside countries)
  population weighting    sum_c (w1_c - w0_c) * s0_c   (which countries grow or shrink)
where w_c is the country's share of world population. The two parts add up to the change exactly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def shift_share(cu: pd.DataFrame, categories, y0: int, y1: int):
    """cu: country-year table with country_id, year, mean_population and mean_<category> columns.

    Returns (table, contributions). table has one row per category with the total change, the within-country
    part and the population-weighting part, all in percentage points. contributions[category] is the
    population-weighting term by country, in percentage points."""
    a = cu[cu.year.eq(y0)].set_index("country_id")
    b = cu[cu.year.eq(y1)].set_index("country_id")
    common = a.index.intersection(b.index)
    p0 = a.loc[common, "mean_population"].to_numpy(float)
    p1 = b.loc[common, "mean_population"].to_numpy(float)
    w0, w1 = p0 / p0.sum(), p1 / p1.sum()
    rows, contributions = [], {}
    for c in categories:
        s0 = a.loc[common, f"mean_{c}"].to_numpy(float)
        s1 = b.loc[common, f"mean_{c}"].to_numpy(float)
        within = w1 * (s1 - s0)
        weighting = (w1 - w0) * s0
        rows.append(dict(religion=c, change_pp=100 * (within.sum() + weighting.sum()),
                         within_country_pp=100 * within.sum(), population_weighting_pp=100 * weighting.sum()))
        contributions[c] = pd.Series(100 * weighting, index=common)
    return pd.DataFrame(rows), contributions


def holders(cu: pd.DataFrame, year: int, religion: str) -> pd.Series:
    """Each country's share of the world's people in one religion, in a given year (sums to 1)."""
    a = cu[cu.year.eq(year)].set_index("country_id")
    people = a["mean_population"] * a[f"mean_{religion}"]
    return (people / people.sum()).sort_values(ascending=False)
