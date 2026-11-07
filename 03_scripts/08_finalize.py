import sys,json,pathlib
sys.path.insert(0,'.runtime')
import geopandas as gpd,pandas as pd,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path
traffic=gpd.read_file('01_data/processed/traffic_counts.gpkg');r=pd.read_csv('04_outputs/grid_search/scale_diagnostics.csv');coverage=[]
for s in r.scale_m:
 g=gpd.read_file(f'04_outputs/grid_search/grid_{s}.gpkg');pairs=g.sindex.query(traffic.geometry,predicate='intersects');rate=len(np.unique(pairs[1]))/len(g);coverage.append(rate)
r['traffic_location_coverage']=coverage;r['traffic_value_coverage']=np.nan;r.to_csv('04_outputs/grid_search/scale_diagnostics.csv',index=False)
g=gpd.read_file('04_outputs/grid_search/grid_1100.gpkg');fig,ax=plt.subplots(figsize=(8,10));g.plot(column='count',cmap='YlOrRd',legend=True,ax=ax);ax.set_axis_off();ax.set_title('1100 m candidate grid | LAPD records 2017–2021');fig.tight_layout();fig.savefig('04_outputs/figures/candidate_grid_1100.png',dpi=160);plt.close(fig)
sel=json.load(open('04_outputs/grid_search/selection.json'));sel.update({'status':'not_confirmed_no_robust_unique_minimum','working_candidate_m':1100,'final_scale_m':None,'origin_support_at_1100':'3 of 4 tested origins near candidate band','traffic_location_coverage_1100':float(r.loc[r.scale_m==1100,'traffic_location_coverage'].iloc[0]),'traffic_coverage_verified':False,'reason':'first main-model dip is shallow; shifts with lag/model/origin; traffic layer contains report links, not validated dated count values'});P('04_outputs/grid_search/selection.json').write_text(json.dumps(sel,indent=2));print(sel)
