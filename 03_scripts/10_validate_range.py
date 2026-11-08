"""Validate variogram support without using reserved test cells or changing grids."""
import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'.runtime'))
import numpy as np,pandas as pd,geopandas as gpd
from scipy.spatial.distance import pdist
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=pathlib.Path('04_outputs/range_validation');OUT.mkdir(exist_ok=True)
base=np.array(json.load(open('02_config/spatial_holdout.json'))['origin'])
def empirical(g):
 xy=g[['cx','cy']].to_numpy();z=g['count'].to_numpy(float);d=pdist(xy);v=.5*pdist(z[:,None],'sqeuclidean');ix=np.floor(d/1000).astype(int);n=np.bincount(ix);ds=np.bincount(ix,weights=d);vs=np.bincount(ix,weights=v);ok=n>=30
 return pd.DataFrame({'lag_m':ds[ok]/n[ok],'semivariance':vs[ok]/n[ok],'pairs':n[ok],'bin_start_m':np.flatnonzero(ok)*1000}),np.var(z)
def fit(b,var,s,lag,kind='spherical'):
 b=b[b.bin_start_m<lag];h=b.lag_m.to_numpy();y=b.semivariance.to_numpy();w=np.sqrt(b.pairs.to_numpy()/b.pairs.max())
 def pred(p,h=h):
  c0,c1,a=p;t=h/a
  return c0+c1*(np.where(t<1,1.5*t-.5*t**3,1) if kind=='spherical' else 1-np.exp(-3*t))
 fs=[least_squares(lambda p:(pred(p)-y)*w/max(var,1),[var*.15,var*.85,a],bounds=([0,0,s/2],[var*20,var*20,150000]),max_nfev=1000) for a in [10000,25000,50000,100000]];f=min(fs,key=lambda f:sum(f.fun**2));c0,c1,a=f.x
 return {'nugget':c0,'sill':c0+c1,'range_m':a,'nsr':c0/(c0+c1),'n_bins':len(b),'nrmse':float(np.sqrt(np.mean((pred(f.x)-y)**2))/max(var,1)),'range_within_observed_lags':bool(a<=h.max()),'range_upper_bound':bool(a>=149000),'nugget_lower_bound':bool(c0/(c0+c1)<1e-6)},pred
rows=[];bins={};grids={}
for s in range(500,2451,150):
 g=gpd.read_file(f'04_outputs/grid_search/grid_{s}.gpkg');g=g[(~g.holdout)&(g.area_fraction>=.8)].copy()
 if len(g)>2500:g=g.iloc[np.random.default_rng(575).choice(len(g),2500,replace=False)]
 grids[s]=g;b,var=empirical(g);bins[s]=b;b.to_csv(OUT/f'empirical_{s}.csv',index=False)
 for lag in [25000,35000,45000,55000,65000]:
  for kind in ['spherical','exponential']:
   r,_=fit(b,var,s,lag,kind);rows.append({'scale_m':s,'max_lag_m':lag,'model':kind,'n_cells':len(g),**r})
 print('validated',s,flush=True)
r=pd.DataFrame(rows);r.to_csv(OUT/'extended_lag_fits.csv',index=False)
# Leave one geographical 5km block out; influence diagnostic, not an independent-pair bootstrap or CI.
jk=[]
for s in [950,1100,1250,1400,1550]:
 g=grids[s].copy();ij=np.floor((g[['cx','cy']].to_numpy()-base)/5000).astype(int);g['block']=[f'{i}_{j}' for i,j in ij]
 for block in sorted(g.block.unique()):
  sub=g[g.block!=block];b,var=empirical(sub)
  for lag in [25000,45000,55000]:
   rr,_=fit(b,var,s,lag);jk.append({'scale_m':s,'max_lag_m':lag,'omitted_block':block,**rr})
 print('block influence',s,flush=True)
j=pd.DataFrame(jk);j.to_csv(OUT/'leave_one_block_out.csv',index=False)
b=bins[1100];g=grids[1100];var=np.var(g['count']);fig,(ax,ax2)=plt.subplots(2,1,figsize=(10,9),gridspec_kw={'height_ratios':[3,1]},sharex=True);ax.scatter(b.lag_m/1000,b.semivariance,s=np.clip(b.pairs/120,8,70),color='black',label='Empirical (1 km bins; marker size = pair count)')
for lag in [25000,35000,45000,55000,65000]:
 rr,pred=fit(b,var,1100,lag);xx=np.linspace(1100,min(75000,b.lag_m.max()),300);ax.plot(xx/1000,pred([rr['nugget'],rr['sill']-rr['nugget'],rr['range_m']],xx),label=f"Fit <= {lag//1000} km: range {rr['range_m']/1000:.1f} km; NSR {rr['nsr']:.3f}")
ax.axvline(25,color='gray',ls='--');ax.set(ylabel='Semivariance (collision count squared)',title='1100 m grid: empirical support and extended-distance fits');ax.legend(fontsize=8);ax.grid(alpha=.2);ax2.bar(b.lag_m/1000,b.pairs,width=.8);ax2.set(xlabel='Distance between grid centers (km)',ylabel='Pairs');fig.tight_layout();fig.savefig('04_outputs/figures/range_validation_1100.png',dpi=180)
summary=[]
for (lag,kind),q in r.groupby(['max_lag_m','model']):
 q=q.sort_values('scale_m');a=q.nsr.to_numpy();mins=[int(q.iloc[k].scale_m) for k in range(1,len(q)-1) if a[k]<a[k-1] and a[k]<a[k+1]];summary.append({'max_lag_m':int(lag),'model':kind,'local_minima_m':mins})
(OUT/'local_minima.json').write_text(json.dumps(summary,indent=2));print(r[(r.scale_m==1100)&(r.model=='spherical')].to_string(index=False));print('DONE')
