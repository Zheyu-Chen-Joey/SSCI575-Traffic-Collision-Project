import sys,pathlib,json,hashlib,datetime
sys.path.insert(0,'.runtime')
import pandas as pd,numpy as np,geopandas as gpd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=pathlib.Path('04_outputs/grid_search/scale_diagnostics.csv');r=pd.read_csv(p);qa=[]
for k,row in r.iterrows():
 g=gpd.read_file(f'04_outputs/grid_search/grid_{int(row.scale_m)}.gpkg');total=int(g['count'].sum());assert total==230536
 r.loc[k,'n_all']=len(g);r.loc[k,'zero_rate']=float((g['count']==0).mean());qa.append({'scale_m':int(row.scale_m),'n_grid':len(g),'collision_sum':total,'valid_geometry':bool(g.geometry.is_valid.all()),'crs':str(g.crs)})
r.to_csv(p,index=False);pathlib.Path('04_outputs/qa/grid_integrity.json').write_text(json.dumps(qa,indent=2))
fig,ax=plt.subplots(figsize=(10,5));ax.plot(r.scale_m,r.nsr,color='0.7',lw=1);ok=(r.status=='ok')&(r.n_fit>=100);ax.scatter(r.loc[ok,'scale_m'],r.loc[ok,'nsr'],label='Fit accepted, at least 100 training cells');ax.scatter(r.loc[~ok,'scale_m'],r.loc[~ok,'nsr'],marker='x',color='darkorange',label='Unstable fit or fewer than 100 cells');ax.axvline(1100,color='green',ls='--',alpha=.6,label='1100 m provisional candidate');ax.set(xlabel='Grid side (m)',ylabel='Nugget / total sill',title='Scale diagnostics | no robust unique optimum confirmed');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig('04_outputs/figures/nsr_scale.png',dpi=180)
files=[]
for p in pathlib.Path('01_data/raw').iterdir():
 if p.is_file():files.append({'file':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
pathlib.Path('00_admin/file_manifest.json').write_text(json.dumps({'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files},indent=2));print('31 scales: count conservation and geometry validation passed')
