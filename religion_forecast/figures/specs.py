"""Step 7 map definitions: which maps exist and the value each country gets (pandas only).

Shared by run.py figures --png (matplotlib + geopandas PNGs in the Step 6 style) and run.py figures
(dependency-free SVG/HTML), so both draw exactly the same numbers. Every value comes from the
forecast outputs in data/projections/ (simulation means over runs); nothing is re-estimated here.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from religion_forecast import config

FORECAST = config.PROJECTIONS
MISSING = '#E5E8EB'                      # countries with no estimate
MAP_CODE_FIXES = {'XKX': 'KOS'}          # Kosovo: Natural Earth spelling
GROUPS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']
# Religion colours. Chosen by searching candidate steps of each conventional hue and scoring every
# pair with the perceptual and colour-vision-deficiency checks in the data-visualisation reference
# (scripts/validate_palette.js). The six groups that are ever a country's largest -- the ones a
# dominant-religion choropleth has to separate -- clear every all-pairs gate in light mode: worst
# pair CVD delta-E 8.3 (target >= 8), worst normal-vision delta-E 15.1 (floor >= 15).
#
# Folk/Traditional and Other are never the largest group anywhere, so they appear only in
# single-hue share maps (no categorical comparison) and in charts, where a legend and direct labels
# carry identity as well as colour. Adding them to the all-pairs test drops the worst CVD pair to
# 3.3 (olive against the Islam green), which is why the dominant maps and the charts are checked
# separately. Islam, Buddhism and Other sit below 3:1 contrast on the chart surface, so values are
# always written as text or available in the companion CSV rather than read off the colour alone.
COLORS = {'Christianity': '#2a78d6', 'Islam': '#1baf7a', 'Hinduism': '#eb6834', 'Buddhism': '#d8a93a',
          'Judaism': '#4a3aa7', 'Folk_Traditional': '#5c7d3a', 'Other': '#9a6fb0', 'Unaffiliated': '#a32a28'}
DOMINANT_GROUPS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Unaffiliated']
# Checked the same way; all three pairs clear every gate (worst CVD delta-E 20.1, normal 19.9).
DRIVER_COLORS = {'Births and deaths': '#eb6834', 'Religious switching': '#a32a28', 'Migration': '#2a78d6'}
MAP_YEARS = [2020, 2050, 2100, 2200, 2500, 3026]
SHARE_YEARS = [2050, 2100, 3026]


def label(g):
    return g.replace('_', '/')


def load():
    ct = pd.read_csv(FORECAST / 'country_year_by_scenario.csv')
    comp = pd.read_csv(FORECAST / 'components_country_period.csv')
    dch = pd.read_csv(FORECAST / 'dominant_change.csv')
    return ct, comp, dch


def _when(year, stat='mean of Monte Carlo runs'):
    if year == 2020:
        return 'Start state: Pew 2020 (Folk/Other split partly a WRP proxy)'
    if year >= 2500:
        return 'Highly speculative scenario, not a prediction'
    if year > 2100:
        return 'Long-run scenario: rests on stated assumptions after 2100'
    return f'Model projection ({stat})'


def specs(ref='stabilising'):
    """List of map specifications (dicts). kind: categorical | sequential | diverging."""
    ct, comp, dch = load()
    scen = sorted(ct.scenario.unique())
    ref = ref if ref in scen else scen[0]
    out = []
    r = ct[ct.scenario.eq(ref)]

    def series(frame, year, col):
        return frame[frame.year.eq(year)].set_index('country_id')[col]

    for y in MAP_YEARS:
        out.append(dict(name=f'dominant_{y}', kind='categorical', values=series(r, y, 'most_likely_dominant'),
                        colors=COLORS, title=f'Dominant religion by country - {y}',
                        subtitle=f"{_when(y, 'most frequent result across Monte Carlo runs')}; scenario: {ref}",
                        footnote='Most frequent dominant group across runs; prob_dominant_change maps show how many runs change'))
    for y in SHARE_YEARS:
        for g in GROUPS:
            out.append(dict(name=f'shares/{g.lower()}_{y}', kind='sequential', values=series(r, y, f'mean_{g}'),
                            vmin=0, vmax=1, cmap='YlGnBu', percent=True,
                            title=f'{label(g)} population share - {y}', subtitle=f'{_when(y)}; scenario: {ref}',
                            colorbar='Population share (%)', footnote='Country population share; mean of runs'))
    for y in (2020, 2100, 3026):
        out.append(dict(name=f'diversity_{y}', kind='sequential', values=series(r, y, 'diversity_gini_simpson_mean'),
                        vmin=0, vmax=0.8, cmap='magma_r', percent=False,
                        title=f'Religious diversity - {y}',
                        subtitle=f'Gini-Simpson index: chance two residents differ in religion. {_when(y)}',
                        colorbar='Diversity index (0 = one religion)', footnote='0 = everyone shares one religion; 0.875 = eight equal groups'))
    for y in (2100, 3026):
        d0 = series(r, 2020, 'diversity_gini_simpson_mean')
        d1 = series(r, y, 'diversity_gini_simpson_mean')
        out.append(dict(name=f'diversity_change_2020_{y}', kind='diverging', values=(d1 - d0), vmin=-0.4, vmax=0.4,
                        cmap='PuOr', percent=False, title=f'Change in religious diversity, 2020-{y}',
                        subtitle=f'Purple = more diverse, orange = less diverse. Scenario: {ref}',
                        colorbar='Change in Gini-Simpson index', footnote=_when(y)))
    dref = dch[dch.scenario.eq(ref)].set_index('country_id')
    for y in (2100, 3026):
        changed = dref[f'prob_changed_by_{y}'] > 0.5
        vals = dref[f'most_likely_{y}'].where(changed, 'Unchanged')
        cols = dict(COLORS, Unchanged='#D9DDE1')
        out.append(dict(name=f'dominant_changed_{y}', kind='categorical', values=vals, colors=cols,
                        title=f'Countries whose dominant religion changes by {y}',
                        subtitle=f'Coloured by the new dominant group where most runs change; grey = unchanged. Scenario: {ref}',
                        footnote=_when(y)))
        out.append(dict(name=f'prob_dominant_change_{y}', kind='sequential', values=dref[f'prob_changed_by_{y}'],
                        vmin=0, vmax=1, cmap='viridis', percent=True,
                        title=f'Share of runs in which the dominant religion changes by {y}',
                        subtitle=f'Model and parameter uncertainty within scenario {ref}; not a calibrated probability',
                        colorbar='Runs with a change (%)', footnote=_when(y)))
    c = comp[comp.scenario.eq(ref) & comp.period.isin(['2020-2050', '2050-2100'])]
    g = c.groupby(['country_id', 'religion'])[[col for col in c.columns if col.startswith('share_pp_')]].sum()
    mig = (g['share_pp_emigration'] + g['share_pp_immigration']).abs().groupby('country_id').sum() / 2
    swi = g['share_pp_switching'].abs().groupby('country_id').sum() / 2
    nat = (g['share_pp_survival'] + g['share_pp_births']).abs().groupby('country_id').sum() / 2
    out.append(dict(name='migration_effect_2020_2100', kind='sequential', values=mig, vmin=0, vmax=10, cmap='Blues',
                    percent=False, title='How much migration changes religious composition, 2020-2100',
                    subtitle='Share points moved by emigration and immigration (half the sum of absolute changes)',
                    colorbar='Percentage points', footnote='From the simulation\'s own sub-step accounting; mean of runs'))
    out.append(dict(name='switching_effect_2020_2100', kind='sequential', values=swi, vmin=0, vmax=20, cmap='RdPu',
                    percent=False, title='How much religious switching changes composition, 2020-2100',
                    subtitle='Share points moved by switching (half the sum of absolute changes)',
                    colorbar='Percentage points', footnote='Switching rates: survey and history evidence mixed per run'))
    unaff_sw = g.xs('Unaffiliated', level='religion')['share_pp_switching']
    out.append(dict(name='switching_unaffiliated_2020_2100', kind='diverging', values=unaff_sw, vmin=-20, vmax=20,
                    cmap='RdBu_r', percent=False, title='Switching effect on the unaffiliated share, 2020-2100',
                    subtitle='Red = net disaffiliation adds to the unaffiliated; blue = net return to religion',
                    colorbar='Percentage points', footnote='Net of flows in both directions; mean of runs'))
    drivers = pd.DataFrame({'Births and deaths': nat, 'Religious switching': swi, 'Migration': mig})
    main = drivers.idxmax(axis=1).where(drivers.max(axis=1) >= 2.0, 'Little change (under 2 pp)')
    out.append(dict(name='main_driver_2020_2100', kind='categorical', values=main,
                    colors=dict(DRIVER_COLORS, **{'Little change (under 2 pp)': '#D9DDE1'}),
                    title='Main driver of religious change, 2020-2100',
                    subtitle='Mechanism moving the most share points in each country (sequential sub-steps of the simulation)',
                    footnote='Births and deaths include ageing and differential fertility; migration includes both directions'))
    out.append(dict(name='foreign_born_share_2100', kind='sequential', values=series(r, 2100, 'foreign_born_share_mean'),
                    vmin=0, vmax=0.6, cmap='YlOrBr', percent=True, title='Foreign-born share of the population - 2100',
                    subtitle=f'First-generation immigrants; scenario {ref}', colorbar='Foreign-born (%)',
                    footnote='Second generation is tracked separately in the CSV outputs'))
    pairs = [('rising_migration', 'low_migration', 'diversity_gini_simpson_mean', 3026, 'Religious diversity', 0.3, False),
             ('rising_migration', 'low_migration', 'diversity_gini_simpson_mean', 2100, 'Religious diversity', 0.15, False),
             ('continued_secularization', 'high_retention', 'mean_Unaffiliated', 3026, 'Unaffiliated share', 0.6, True),
             ('persistent_fertility_gaps', ref, 'mean_Islam', 3026, 'Muslim share', 0.4, True)]
    for a, b, col, y, what, lim, pct in pairs:
        if a in scen and b in scen:
            va = series(ct[ct.scenario.eq(a)], y, col)
            vb = series(ct[ct.scenario.eq(b)], y, col)
            out.append(dict(name=f'scenario_diff_{col.replace("mean_", "")}_{a}_vs_{b}_{y}', kind='diverging',
                            values=va - vb, vmin=-lim, vmax=lim, cmap='RdBu_r', percent=pct,
                            title=f'{what}, {y}: {a} minus {b}',
                            subtitle='Scenario uncertainty: what the assumption alone changes (same random draws in both)',
                            colorbar='Difference' + (' (percentage points)' if pct else ''), footnote=_when(y)))
    return out
