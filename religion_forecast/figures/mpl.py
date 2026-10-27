"""Step 7 maps and charts in the Step 6 style (PNG, matplotlib + geopandas).

Run from this folder (Windows PowerShell), after run.py project:
    .\\.venv\\Scripts\\python.exe run.py figures --png
    explorer .\\outputs\\figures_png
Uses the same pandas, geopandas and matplotlib as Step 6 and reuses its boundary loading, axes,
colours and file saving, so the maps look like the earlier ones. Writes outputs/figures_png/; the
Step 5/6 map folders are not touched. Map values come from religion_forecast/figures/specs.py (shared with the
dependency-free run.py figures).
Options: --skip-shares (no per-religion share maps), --dpi N.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from religion_forecast import config
from religion_forecast.figures import specs as MD

OUT = config.FIGURES_PNG
FORECAST = MD.FORECAST
MISSING = MD.MISSING


# --- drawing helpers (kept here so the package does not depend on the legacy step 6 script) ---
def load_boundaries():
    """Natural Earth admin-0 polygons, one row per ISO3 map id, Antarctica dropped."""
    src = config.RAW / 'ne_50m_admin_0_countries.zip'
    if not src.exists():
        raise FileNotFoundError(f'Natural Earth file not found: {src}')
    borders = gpd.read_file('zip://' + str(src.resolve())).to_crs('EPSG:4326')
    if 'CONTINENT' in borders:
        borders = borders.loc[borders['CONTINENT'].ne('Antarctica')].copy()
    iso = borders['ISO_A3'].fillna('').astype(str).str.upper()
    adm = borders['ADM0_A3'].fillna('').astype(str).str.upper()
    borders['map_id'] = iso.where(iso.str.fullmatch('[A-Z]{3}'), adm)
    borders = borders.loc[borders.map_id.str.fullmatch('[A-Z]{3}')]
    return borders[['map_id', 'geometry']].dissolve(by='map_id').reset_index()


def assign_ids(frame):
    """Add a `map_id` column (country_id, with the Natural Earth spelling of Kosovo)."""
    frame = frame.copy()
    frame['country_id'] = frame['country_id'].astype(str).str.upper()
    frame['map_id'] = frame.country_id.replace(MD.MAP_CODE_FIXES)
    return frame


def prepare_axes(title, subtitle, figsize=(14, 7.2)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#F5F8FB')
    fig.suptitle(title, y=.982, fontsize=17, fontweight='bold')
    ax.set_title(subtitle, fontsize=9.6, color='#45545E', pad=14)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-59, 85)
    ax.set_aspect('equal', adjustable='box')
    ax.set_axis_off()
    return fig, ax


def footnote(fig, line):
    fig.text(.5, .016, line, fontsize=8.3, ha='center', va='bottom', color='#58646F')


def save_png(fig, path, dpi):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, facecolor='white', bbox_inches='tight', pad_inches=.16)
    plt.close(fig)
SHOW_COUNTRIES = ['USA', 'BRA', 'GBR', 'DEU', 'FRA', 'SWE', 'NGA', 'ETH', 'EGY', 'SAU', 'IND', 'CHN', 'JPN', 'KOR', 'IDN', 'AUS']
MECH = [('share_pp_survival', 'Deaths and ageing', '#8C6D5A'), ('share_pp_births', 'Births', '#E58D36'),
        ('share_pp_switching', 'Religious switching', '#C94F68'), ('share_pp_emigration', 'Emigration', '#7FA7CF'),
        ('share_pp_immigration', 'Immigration', '#3974A9'), ('share_pp_residual', 'Residual', '#999999')]


def join(borders, values):
    t = pd.DataFrame({'country_id': pd.Series(values).index.astype(str), 'value': pd.Series(values).values})
    t = assign_ids(t)
    t = t.drop_duplicates('map_id')
    m = borders.merge(t[['map_id', 'value']], how='left', on='map_id', validate='one_to_one')
    return gpd.GeoDataFrame(m, geometry='geometry', crs=borders.crs)


def draw(spec, borders, path, dpi):
    mapped = join(borders, spec['values'])
    fig, ax = prepare_axes(spec['title'], spec['subtitle'])
    if spec['kind'] == 'categorical':
        cols = spec['colors']
        mapped.plot(ax=ax, color=mapped.value.map(cols).fillna(MISSING).tolist(), edgecolor='#F3F4F5', linewidth=.29)
        present = [c for c in cols if c in set(mapped.value.dropna().astype(str))]
        handles = [Patch(facecolor=cols[c], edgecolor='#777', label=MD.label(c)) for c in present]
        handles.append(Patch(facecolor=MISSING, edgecolor='#999', label='No matched estimate'))
        ax.legend(handles=handles, ncol=min(5, len(handles)), loc='lower center', bbox_to_anchor=(.5, -.115),
                  fontsize=8.2, frameon=False, handlelength=1.6, columnspacing=1.6)
    else:
        mapped['value'] = pd.to_numeric(mapped.value, errors='coerce')
        mapped.plot(column='value', ax=ax, cmap=spec['cmap'], vmin=spec['vmin'], vmax=spec['vmax'],
                    edgecolor='#F0F2F4', linewidth=.24, missing_kwds={'color': MISSING})
        sm = ScalarMappable(norm=Normalize(spec['vmin'], spec['vmax']), cmap=spec['cmap'])
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=.66, fraction=.025, pad=.015)
        cbar.set_label(spec.get('colorbar', ''), fontsize=10)
        ticks = np.linspace(spec['vmin'], spec['vmax'], 6)
        cbar.set_ticks(ticks)
        if spec.get('percent'):
            cbar.set_ticklabels([f'{100 * t:.0f}' for t in ticks])
    footnote(fig, spec.get('footnote', ''))
    save_png(fig, path, dpi)


def chart_global(path, dpi):
    wt = pd.read_csv(FORECAST / 'global_share_by_scenario.csv')
    ref = json.loads((FORECAST / 'projection_report.json').read_text())['reference_scenario']
    scen = list(dict.fromkeys(wt.scenario))
    cmap = plt.get_cmap('tab10')
    fig, axes = plt.subplots(4, 2, figsize=(14, 13), sharex=True)
    for ax, g in zip(axes.flat, MD.GROUPS):
        for i, s in enumerate(scen):
            sub = wt[wt.scenario.eq(s) & wt.religion.eq(g)].sort_values('year')
            x, y = sub.year.to_numpy(), 100 * sub['mean'].to_numpy()
            ax.plot(x, y, color=cmap(i % 10), linewidth=2.4 if s == ref else 1.2, label=s)
            if s == ref:
                ax.fill_between(x, 100 * sub.q05, 100 * sub.q95, color=cmap(i % 10), alpha=.18)
        ax.axvline(2100, color='#8C959E', linestyle='--', linewidth=1)
        ax.set_title(MD.label(g), fontsize=12, loc='left')
        ax.set_ylabel('World population (%)')
        ax.grid(True, alpha=.18)
        ax.set_xlim(2020, 3030)
        ax.set_ylim(bottom=0)
    for ax in axes[-1]:
        ax.set_xlabel('Year')
    axes[0, 0].legend(fontsize=8, ncol=2, frameon=False)
    fig.suptitle('World religion shares by scenario (2020-3030)', fontsize=17, fontweight='bold', y=.993)
    fig.text(.5, .01, f'Bold line and band: reference scenario ({ref}) mean and 5-95% of runs. After 2100 = assumptions; '
                      '2500-3026 are speculative.', ha='center', fontsize=9, color='#52616F')
    fig.tight_layout(rect=(0, .03, 1, .965))
    save_png(fig, path, dpi)


def chart_diversity(path, dpi):
    ct = pd.read_csv(FORECAST / 'country_year_by_scenario.csv')
    fig, ax = plt.subplots(figsize=(12, 6))
    for s, sub in ct.groupby('scenario', sort=False):
        wsum = (sub.diversity_gini_simpson_mean * sub.mean_population).groupby(sub.year).sum()
        g = wsum / sub.mean_population.groupby(sub.year).sum()
        ax.plot(g.index, g.values, linewidth=2, label=s)
    ax.axvline(2100, color='#8C959E', linestyle='--', linewidth=1)
    ax.set_title('Religious diversity within countries (population-weighted mean Gini-Simpson index)', loc='left')
    ax.set_xlabel('Year')
    ax.set_ylabel('Chance two residents of a country differ in religion')
    ax.grid(True, alpha=.2)
    ax.legend(frameon=False, fontsize=9, ncol=2)
    save_png(fig, path, dpi)


def chart_world_components(path, dpi):
    wc = pd.read_csv(FORECAST / 'components_world_period.csv')
    ref = json.loads((FORECAST / 'projection_report.json').read_text())['reference_scenario']
    sub = wc[wc.scenario.eq(ref) & wc.period.isin(['2020-2050', '2050-2100'])].groupby('religion').sum(numeric_only=True)
    sub = sub.reindex(MD.GROUPS)
    fig, ax = plt.subplots(figsize=(12, 6))
    y = np.arange(len(sub))
    left_pos, left_neg = np.zeros(len(sub)), np.zeros(len(sub))
    for col, name, colr in MECH:
        c = 'world_' + col
        v = sub[c].to_numpy() if c in sub else np.zeros(len(sub))
        base = np.where(v >= 0, left_pos, left_neg)
        ax.barh(y, v, left=base, color=colr, label=name, height=.6)
        left_pos += np.maximum(v, 0)
        left_neg += np.minimum(v, 0)
    tot = sub['world_share_pp_total'].to_numpy()
    ax.scatter(tot, y, color='black', zorder=3, s=18, label='Total change')
    ax.set_yticks(y, [MD.label(g) for g in sub.index])
    ax.axvline(0, color='#555', linewidth=.8)
    ax.set_xlabel('Change in world share, 2020-2100 (percentage points)')
    ax.set_title(f'What changes each religion\'s world share, 2020-2100 ({ref})', loc='left')
    ax.legend(frameon=False, fontsize=9, ncol=4, loc='lower right')
    ax.grid(True, axis='x', alpha=.2)
    fig.text(.5, .005, 'Migration moves people between countries but cancels out worldwide; it changes country shares, not world shares.',
             ha='center', fontsize=9, color='#52616F')
    save_png(fig, path, dpi)


def chart_country_components(path, dpi):
    comp = pd.read_csv(FORECAST / 'components_country_period.csv')
    ref = json.loads((FORECAST / 'projection_report.json').read_text())['reference_scenario']
    c = comp[comp.scenario.eq(ref) & comp.period.isin(['2020-2050', '2050-2100'])]
    ids = [x for x in SHOW_COUNTRIES if x in set(c.country_id)]
    fig, axes = plt.subplots(4, 4, figsize=(18, 15), sharex=False)
    for ax, cid in zip(axes.flat, ids):
        sub = c[c.country_id.eq(cid)].groupby('religion').sum(numeric_only=True).reindex(MD.GROUPS)
        keep = sub['share_pp_total'].abs() + sum(sub[m].abs() for m, _, _ in MECH) > 0.3
        sub = sub[keep]
        y = np.arange(len(sub))
        lp, ln = np.zeros(len(sub)), np.zeros(len(sub))
        for col, name, colr in MECH:
            v = sub[col].to_numpy()
            ax.barh(y, v, left=np.where(v >= 0, lp, ln), color=colr, height=.6, label=name)
            lp += np.maximum(v, 0)
            ln += np.minimum(v, 0)
        ax.scatter(sub['share_pp_total'], y, color='black', s=12, zorder=3)
        ax.set_yticks(y, [MD.label(g) for g in sub.index], fontsize=8)
        ax.axvline(0, color='#555', linewidth=.7)
        ax.set_title(cid, loc='left', fontsize=11)
        ax.grid(True, axis='x', alpha=.2)
    for ax in axes.flat[len(ids):]:
        ax.axis('off')
    h, l = axes.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=6, frameon=False)
    fig.suptitle(f'Where each country\'s religious change comes from, 2020-2100 ({ref}); share points, dot = total',
                 fontsize=15, fontweight='bold')
    fig.tight_layout(rect=(0, .04, 1, .96))
    save_png(fig, path, dpi)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dpi', type=int, default=130)
    ap.add_argument('--skip-shares', action='store_true')
    args = ap.parse_args(argv)
    borders = load_boundaries()
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for spec in MD.specs():
        if args.skip_shares and spec['name'].startswith('shares/'):
            continue
        path = OUT / f'{spec["name"]}.png'
        draw(spec, borders, path, args.dpi)
        made.append(str(path.relative_to(config.PROJECT)))
    for fn, name in ((chart_global, 'global_shares_by_scenario.png'), (chart_diversity, 'diversity_by_scenario.png'),
                     (chart_world_components, 'world_components_2020_2100.png'),
                     (chart_country_components, 'country_components_2020_2100.png')):
        fn(OUT / name, args.dpi)
        made.append(str((OUT / name).relative_to(config.PROJECT)))
    (OUT / 'figures_report.json').write_text(json.dumps({'figures': made, 'cautions': [
        'Values are means over Monte Carlo runs under researcher-chosen scenarios, not calibrated probabilities.',
        '2200 and later rest on stated long-run assumptions; 2500 and 3026 are speculative scenarios.',
        'Present-day Natural Earth boundaries; unmatched territories stay grey.']}, indent=2))
    print(f'SUCCESS: {len(made)} figures in {OUT}')


if __name__ == '__main__':
    main()
