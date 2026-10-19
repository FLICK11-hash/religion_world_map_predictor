"""Step 6: 2-D country religion choropleths and global scenario charts.

Place beside Step 5 scripts; run with
    .\\.venv\\Scripts\\python.exe step6_make_maps.py

Cautions:
- Earlier WRP periods are shown against MODERN Natural Earth geography for surviving
  country IDs only; historical state boundaries are NOT reconstructed.
- Pew Folk/Other split is partly a proxy; do not call it Pew-observed.
- Model agreement across scenarios is NOT calibrated forecast probability.
- 2200–3026 is assumption-driven exploration, not validated prediction.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data' / 'raw'
PROCESSED = ROOT / 'data' / 'processed'
FORECAST = ROOT / 'data' / 'forecasts'
OUT = ROOT / 'outputs' / 'maps'

GROUPS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism',
          'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']
COLORS = {
    'Christianity': '#3974A9', 'Islam': '#29936C',
    'Hinduism': '#E58D36', 'Buddhism': '#D2AD3F',
    'Judaism': '#9065B1', 'Folk_Traditional': '#A17653',
    'Other': '#7B8794', 'Unaffiliated': '#C94F68'
}
MISSING = '#E5E8EB'
MAP_CODE_FIXES = {'XKX': 'KOS'}  # Kosovo: mapping alias, not a change of sovereignty


def parse_years(s):
    result = [int(x.strip()) for x in s.split(',') if x.strip()]
    if not result or len(set(result)) != len(result):
        raise ValueError('Years must be a nonempty comma-separated list without duplicates')
    return result


def load_boundaries():
    src = RAW / 'ne_50m_admin_0_countries.zip'
    if not src.exists():
        raise FileNotFoundError(f'Natural Earth file not found: {src}')
    borders = gpd.read_file('zip://' + str(src.resolve()))
    if borders.crs is None:
        raise ValueError('Natural Earth file lacks a coordinate reference system')
    borders = borders.to_crs('EPSG:4326')
    if 'CONTINENT' in borders:
        borders = borders.loc[borders['CONTINENT'].ne('Antarctica')].copy()
    iso = borders['ISO_A3'].fillna('').astype(str).str.upper()
    adm = borders['ADM0_A3'].fillna('').astype(str).str.upper()
    borders['map_id'] = iso.where(iso.str.fullmatch('[A-Z]{3}'), adm)
    borders = borders.loc[borders.map_id.str.fullmatch('[A-Z]{3}')].copy()
    # Dissolve repeated geographic features of same country (if present).
    borders = borders[['map_id', 'geometry']].dissolve(by='map_id').reset_index()
    if borders.map_id.duplicated().any():
        raise ValueError('Duplicate Natural Earth map IDs remain')
    return borders


def assign_ids(frame):
    frame = frame.copy()
    frame['country_id'] = frame['country_id'].astype(str).str.upper()
    frame['map_id'] = frame.country_id.replace(MAP_CODE_FIXES)
    return frame


def ensure_simplex(df, cols, context):
    if df.empty:
        raise ValueError(f'{context}: no records')
    values = df[cols].apply(pd.to_numeric, errors='raise').to_numpy(float)
    if not np.isfinite(values).all() or (values < -1e-7).any() or (values > 1 + 1e-7).any():
        raise ValueError(f'{context}: non-finite or invalid religion shares')
    if not np.allclose(values.sum(axis=1), 1, atol=2e-5):
        raise ValueError(f'{context}: religion shares do not add to one')


def load_observed(source, year):
    path = PROCESSED / ('pew_anchor_only_8groups.csv' if source == 'Pew' else 'wrp_training_only_8groups.csv')
    df = pd.read_csv(path, low_memory=False)
    df = df[df.year.eq(year)].copy()
    if df.empty:
        raise ValueError(f'{source} {year}: no rows')
    if df.country_id.duplicated().any():
        raise ValueError(f'{source} {year}: duplicate country IDs')
    cols = [f'share_{g}' for g in GROUPS]
    ensure_simplex(df, cols, f'{source} {year}')
    out = df[['country_id'] + cols].copy()
    out = out.rename(columns={f'share_{g}':f'mean_{g}' for g in GROUPS})
    out['most_likely_dominant'] = np.asarray(GROUPS)[out[[f'mean_{g}' for g in GROUPS]].to_numpy(float).argmax(axis=1)]
    out['dominant_agreement_fraction'] = np.nan
    out['year'] = year
    out['source'] = source
    return assign_ids(out)


def load_forecast():
    path = FORECAST / 'country_year_uncertainty.csv'
    if not path.exists():
        raise FileNotFoundError(f'Missing Step 5 output: {path}')
    df = pd.read_csv(path, low_memory=False)
    expected = ['country_id', 'year', 'most_likely_dominant', 'dominant_agreement_fraction']
    expected += [f'mean_{g}' for g in GROUPS]
    absent = set(expected) - set(df.columns)
    if absent:
        raise ValueError(f'Missing forecast fields: {sorted(absent)}')
    if df.duplicated(['country_id', 'year']).any():
        raise ValueError('Step 5 forecast has duplicate country-years')
    ensure_simplex(df, [f'mean_{g}' for g in GROUPS], 'Step 5')
    if not df.most_likely_dominant.isin(GROUPS).all():
        raise ValueError('Unknown dominant religion in forecast')
    if not df.dominant_agreement_fraction.between(0, 1).all():
        raise ValueError('Invalid agreement fraction')
    df['source'] = 'Step5_scenario_ensemble'
    return assign_ids(df)


def joined_geo(borders, table, year, source):
    # Left-joining to boundaries retains unknown/missing country polygons as grey.
    if table.map_id.duplicated().any():
        duplicate = table[table.map_id.duplicated(keep=False)].map_id.unique().tolist()
        raise ValueError(f'{source} {year}: alias collision among geographic IDs {duplicate}')
    mapped = borders.merge(table, how='left', on='map_id', validate='one_to_one')
    if not mapped.most_likely_dominant.notna().any():
        raise ValueError(f'No map polygons matched for {source} {year}')
    mapped = gpd.GeoDataFrame(mapped, geometry='geometry', crs=borders.crs)
    return mapped


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
    fig.text(.5,.016,line,fontsize=8.3,ha='center',va='bottom',color='#58646F')


def save_png(fig, path, dpi):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, facecolor='white', bbox_inches='tight', pad_inches=.16)
    plt.close(fig)


def draw_dominant(mapped, year, source, path, dpi):
    historic = source == 'WRP'
    is_future = source == 'Step5_scenario_ensemble'
    qualifier = ('WRP historical affiliations; modern borders are only a rough locator' if historic else
        'Modal dominant group across equally weighted scenarios; not a calibrated probability' if is_future else
        'Pew affiliated estimates; Folk/Other split partly proxy-derived')
    fig, ax = prepare_axes(f'Dominant religion by country — {year}', qualifier)
    display_color = mapped.most_likely_dominant.map(COLORS).fillna(MISSING)
    mapped.plot(ax=ax, color=display_color.tolist(), edgecolor='#F3F4F5', linewidth=.29)
    handles = [Patch(facecolor=COLORS[g], edgecolor='#777', label=g.replace('_','/')) for g in GROUPS]
    handles.append(Patch(facecolor=MISSING,edgecolor='#999',label='No matched estimate'))
    ax.legend(handles=handles, ncol=5, loc='lower center', bbox_to_anchor=(.5,-.115),
              fontsize=8.2, frameon=False, handlelength=1.6, columnspacing=1.6)
    caution = ('Historical entities without matching modern polygons are omitted' if historic else
               '2200+ scenarios reflect assumed demographic and secularization pathways' if year >= 2200 else
               'Present-day administrative borders are used for display')
    footnote(fig, caution)
    save_png(fig, path, dpi)


def draw_share(mapped, year, group, source, path, dpi):
    label = group.replace('_','/')
    fig, ax = prepare_axes(f'{label} population share — {year}',
                           'Country population share (0–100%); scenario average' if source.startswith('Step5') else
                           'Country population share (0–100%); historical estimates')
    field = f'mean_{group}'
    mapped.plot(column=field, ax=ax, cmap='YlGnBu', vmin=0, vmax=1,
                edgecolor='#F0F2F4', linewidth=.24,
                missing_kwds={'color':MISSING})
    sm = ScalarMappable(norm=Normalize(0,1), cmap='YlGnBu')
    sm.set_array([])
    cbar=fig.colorbar(sm, ax=ax, shrink=.66, fraction=.025, pad=.015)
    cbar.set_label('Population share (%)',fontsize=10)
    cbar.set_ticks([0,.2,.4,.6,.8,1.0])
    cbar.set_ticklabels(['0','20','40','60','80','100'])
    note = ('Earlier country estimates displayed on current boundaries; incomplete historical coverage' if source=='WRP' else
            'Long-run values reflect modeled assumptions, not verified religious outcomes' if year>=2200 else
            'The Folk/Traditional vs Other distinction is partly inferred from WRP when sourced from Pew')
    footnote(fig,note)
    save_png(fig,path,dpi)


def draw_agreement(mapped,year,path,dpi):
    fig, ax = prepare_axes(f'Scenario agreement on dominant religion — {year}',
        'Fraction of 120 simulations with the modal label, not statistical confidence')
    mapped.plot(column='dominant_agreement_fraction',ax=ax, cmap='viridis',
                vmin=0, vmax=1, edgecolor='#ECEFF1',linewidth=.26,
                missing_kwds={'color':MISSING})
    sm=ScalarMappable(norm=Normalize(0,1), cmap='viridis')
    sm.set_array([])
    cbar=fig.colorbar(sm,ax=ax,shrink=.66,fraction=.025,pad=.015)
    cbar.set_label('Fraction of scenario runs (%)',fontsize=10)
    cbar.set_ticks([0,.2,.4,.6,.8,1.0]);cbar.set_ticklabels(['0','20','40','60','80','100'])
    footnote(fig,'Scenario weights were chosen by the researcher; agreement is not a forecast success probability')
    save_png(fig,path,dpi)


def draw_global_bands(path,dpi):
    df=pd.read_csv(FORECAST/'global_share_uncertainty.csv')
    expected={'year','religion','mean','q05','q95'}
    if expected-set(df.columns):
        raise ValueError(f'Global data missing {sorted(expected-set(df.columns))}')
    fig,axes=plt.subplots(4,2,figsize=(14,13),sharex=True)
    for ax,group in zip(axes.flat,GROUPS):
        subset=df.loc[df.religion.eq(group)].sort_values('year')
        if subset.empty:
            raise ValueError(f'Missing global series for {group}')
        x=subset.year.to_numpy(int)
        y=100*subset['mean'].to_numpy(float)
        low=100*subset['q05'].to_numpy(float)
        high=100*subset['q95'].to_numpy(float)
        ax.plot(x,y,color=COLORS[group],linewidth=2,label='Scenario mean')
        ax.fill_between(x,low,high,color=COLORS[group],alpha=.21,label='5–95% of runs')
        ax.axvline(2100,color='#8C959E',linestyle='--',linewidth=1)
        ax.set_title(group.replace('_','/'),fontsize=12,loc='left')
        ax.set_ylabel('Global population (%)')
        ax.grid(True,alpha=.18)
        ax.set_xlim(2020,3030)
        ax.set_ylim(bottom=0)
    for ax in axes[-1]: ax.set_xlabel('Year')
    fig.suptitle('World religion shares across scenario runs (2020–3030)',fontsize=17,fontweight='bold',y=.993)
    fig.text(.5,.01,'Shaded bands reflect the four chosen scenarios and sampled model errors; not calibrated prediction intervals.',ha='center',fontsize=9,color='#52616F')
    fig.tight_layout(rect=(0,.03,1,.965))
    save_png(fig,path,dpi)


def audit_coverage(borders,source,year,table):
    known=set(borders.map_id)
    present=table.map_id.astype(str)
    n_matched=int(present.isin(known).sum())
    if not n_matched:
        raise ValueError(f'{source} {year}: zero matched geometries')
    missing=sorted(set(table.loc[~present.isin(known),'country_id'].astype(str)))
    return ({'source':source,'year':int(year),'n_country_records':int(len(table)),
              'n_country_ids_with_polygons':n_matched,
              'n_map_polygons_without_observation':int(len(known-set(present))),
              'n_country_ids_without_polygons':len(missing)},
            [{'source':source,'year':int(year),'country_id':cid} for cid in missing])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-years',default='1945,1970,1990',
                        help='WRP years for supplementary historical dominant maps, or none')
    parser.add_argument('--map-years',default='2010,2020,2050,2100,2200,2500,3026')
    parser.add_argument('--share-years',default='2010,2050,2100,2200,2500,3026')
    parser.add_argument('--share-groups',default='all',
                        help='all or comma-separated categories e.g. Christianity,Islam,Unaffiliated')
    parser.add_argument('--dpi',type=int,default=130)
    parser.add_argument('--skip-shares',action='store_true')
    args=parser.parse_args()
    history = [] if args.historical_years.lower() in ('none','') else parse_years(args.historical_years)
    map_years=parse_years(args.map_years)
    share_years=[] if args.skip_shares else parse_years(args.share_years)
    if not set(share_years).issubset(map_years):
        raise ValueError('--share-years must be a subset of --map-years')
    groups=GROUPS if args.share_groups=='all' else args.share_groups.split(',')
    if any(g not in GROUPS for g in groups):
        raise ValueError(f'Unknown --share-groups: {groups}; choices: {GROUPS}')
    borders=load_boundaries()
    forecast=load_forecast()
    OUT.mkdir(parents=True,exist_ok=True)
    coverage=[];unmatched=[];generated=[]
    # Pre-2010 maps: WRP has incomplete historical coverage. Modern polygons cannot
    # faithfully represent dissolved polities; those remain visibly uncolored.
    for year in history:
        obs=load_observed('WRP',year)
        cov,bad=audit_coverage(borders,'WRP',year,obs);coverage.append(cov);unmatched+=bad
        merged=joined_geo(borders,obs,year,'WRP')
        path=OUT/f'dominant_WRP_historical_{year}.png'
        draw_dominant(merged,year,'WRP',path,args.dpi);generated.append(str(path.relative_to(ROOT)))
        print(f'[HISTORY] {year}: {cov["n_country_ids_with_polygons"]}/{cov["n_country_records"]} country IDs have modern polygons')
    for year in map_years:
        if year in (2010,2020):
            table=load_observed('Pew',year)
            source='Pew'
        else:
            table=forecast.loc[forecast.year.eq(year)].copy()
            source='Step5_scenario_ensemble'
            if table.empty:raise ValueError(f'No Step 5 forecast for {year}')
        cov,bad=audit_coverage(borders,source,year,table);coverage.append(cov);unmatched+=bad
        merged=joined_geo(borders,table,year,source)
        dom=OUT/f'dominant_{year}.png'
        draw_dominant(merged,year,source,dom,args.dpi);generated.append(str(dom.relative_to(ROOT)))
        if source=='Step5_scenario_ensemble':
            confidence=OUT/f'scenario_agreement_{year}.png'
            draw_agreement(merged,year,confidence,args.dpi);generated.append(str(confidence.relative_to(ROOT)))
        if year in share_years:
            for group in groups:
                path=OUT/'shares'/f'{group.lower()}_{year}.png'
                draw_share(merged,year,group,source,path,args.dpi)
                generated.append(str(path.relative_to(ROOT)))
        print(f'[MAP] {year}: {cov["n_country_ids_with_polygons"]}/{cov["n_country_records"]} IDs have modern polygons')
    bands=OUT/'global_shares_uncertainty.png'
    draw_global_bands(bands,args.dpi);generated.append(str(bands.relative_to(ROOT)))
    pd.DataFrame(coverage).to_csv(OUT/'map_coverage.csv',index=False)
    pd.DataFrame(unmatched,columns=['source','year','country_id']).to_csv(OUT/'unmapped_country_ids.csv',index=False)
    report={
        'generated_files':len(generated),'output_directory':str(OUT),
        'historical_years':history,'map_years':map_years,'share_years':share_years,
        'share_groups':groups,'figure_paths':generated,
        'cautions':[
            '2010/2020 are observed Pew estimates (not model forecasts), with estimated Folk/Other splits.',
            'Historical WRP country IDs are painted only where a modern country code matches. Historical borders are not reconstructed.',
            'All geographic outlines are contemporary Natural Earth boundaries.',
            'Scenario agreement is run frequency under researcher-chosen assumptions, not calibrated prediction probability.',
            'Post-2100 outcomes, particularly 2200–3026, are illustrative scenario explorations.',
            '3026 shares are interpolated from model states at 3025 and 3030.',
            'Unmapped or unobserved countries stay gray, not assigned a guessed religion.'
        ]}
    (OUT/'step6_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'\nSUCCESS: Created {len(generated)} figures in {OUT}')
    print('Wrote step6_report.json, map_coverage.csv, unmapped_country_ids.csv')

if __name__=='__main__': main()
