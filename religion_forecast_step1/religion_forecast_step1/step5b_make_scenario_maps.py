"""Make one map per Step 5B scenario at selected years, side-by-side comparable."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Patch
import step6_make_maps as viz
from step5b_dynamic_scenarios import OUT, SCENARIOS

YEARS = (2050,2100,2200,2500,3026)
ROOT = Path(__file__).resolve().parent
DEST = ROOT/'outputs'/'maps_step5b'/'by_scenario'

def main():
    data=pd.read_csv(OUT/'scenario_country_maps.csv',low_memory=False)
    borders=viz.load_boundaries()
    DEST.mkdir(exist_ok=True,parents=True)
    rows=[]
    for sc in SCENARIOS:
        for year in YEARS:
            df=viz.assign_ids(data.loc[(data.scenario==sc)&(data.year==year)].copy())
            merged=viz.joined_geo(borders,df,year,sc)
            fig,ax=viz.prepare_axes(f'{sc.replace("_", " ").title()} — dominant religion, {year}',
                 'Modal dominant group among runs in THIS scenario (not a statistically validated forecast)')
            merged.plot(ax=ax,color=merged.most_likely_dominant.map(viz.COLORS).fillna(viz.MISSING).tolist(),
                edgecolor='#F3F4F5',linewidth=.29)
            handles=[Patch(facecolor=viz.COLORS[g],edgecolor='#777',label=g.replace('_','/')) for g in viz.GROUPS]
            handles.append(Patch(facecolor=viz.MISSING,edgecolor='#999',label='No matched estimate'))
            ax.legend(handles=handles,ncol=5,loc='lower center',bbox_to_anchor=(.5,-.115),
                fontsize=8.2,frameon=False,handlelength=1.6,columnspacing=1.6)
            viz.footnote(fig,'Sensitivity experiment; 2200–3026 is assumption-driven, not validated prediction')
            path=DEST/f'{sc}_{year}.png'
            viz.save_png(fig,path,110)
            rows.append({'scenario':sc,'year':year,'file':str(path.relative_to(ROOT))})
    pd.DataFrame(rows).to_csv(DEST/'scenario_maps_index.csv',index=False)
    print(f'SUCCESS: {len(rows)} separate scenario maps written to {DEST}')

if __name__=='__main__':main()
