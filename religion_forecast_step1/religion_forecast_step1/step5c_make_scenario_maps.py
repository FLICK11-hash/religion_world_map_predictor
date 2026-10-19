"""Scenario-specific maps for 2050, 2100, 2200, 2500 and 3026."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Patch
import step6_make_maps as viz
from step5c_evidence_sensitivity import OUT, SCENARIOS

YEARS=(2050,2100,2200,2500,3026)
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'outputs'/'maps_step5c'/'by_scenario'

def main():
    data=pd.read_csv(OUT/'scenario_country_maps.csv',low_memory=False)
    borders=viz.load_boundaries();DEST.mkdir(exist_ok=True,parents=True)
    rows=[]
    for sc in SCENARIOS:
        for year in YEARS:
            source=viz.assign_ids(data[(data.scenario==sc)&(data.year==year)].copy())
            geo=viz.joined_geo(borders,source,year,sc)
            fig,ax=viz.prepare_axes(f'{sc.replace("_"," ").title()} — {year}',
                'Scenario modal dominant religion; not calibrated real-world probabilities')
            geo.plot(ax=ax,color=geo.most_likely_dominant.map(viz.COLORS).fillna(viz.MISSING).tolist(),
                     edgecolor='#F3F4F5',linewidth=.29)
            legend=[Patch(facecolor=viz.COLORS[g],edgecolor='#777',label=g.replace('_','/')) for g in viz.GROUPS]
            legend.append(Patch(facecolor=viz.MISSING,edgecolor='#999',label='No matched estimate'))
            ax.legend(handles=legend,ncol=5,loc='lower center',bbox_to_anchor=(.5,-.115),
                fontsize=8.2,frameon=False,handlelength=1.6,columnspacing=1.6)
            viz.footnote(fig,'Sensitivity experiment; 2200–3026 outcomes depend mainly on model assumptions')
            path=DEST/f'{sc}_{year}.png'
            viz.save_png(fig,path,110)
            rows.append(dict(scenario=sc,year=year,file=str(path.relative_to(ROOT))))
    pd.DataFrame(rows).to_csv(DEST/'scenario_maps_index.csv',index=False)
    print(f'SUCCESS: {len(rows)} scenario maps written to {DEST}')

if __name__=='__main__':main()
