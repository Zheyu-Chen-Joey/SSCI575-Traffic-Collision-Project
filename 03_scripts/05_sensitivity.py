import sys,json,pathlib
sys.path.insert(0,'.runtime')
import numpy as np,pandas as pd,geopandas as gpd
from scipy.spatial.distance import pdist
from scipy.optimize import least_squares
out=[]
for s in range(500,2451,150):
 g=gpd.read_file(f'04_outputs/grid_search/grid_{s}.gpkg');g=g[(~g.holdout)&(g.area_fraction>=.8)];z=g['count'].to_numpy(float);xy=g[['cx','cy']].to_numpy();
 if len(z)>2500:
  ix=np.random.default_rng(575).choice(len(z),2500,replace=False);z=z[ix];xy=xy[ix]
 d=pdist(xy);v=.5*pdist(z[:,None],'sqeuclidean');var=np.var(z)
 for lag in [15000,20000,25000,30000]:
  bi=np.digitize(d,np.linspace(0,lag,26))-1;bins=np.array([(d[bi==i].mean(),v[bi==i].mean(),(bi==i).sum()) for i in range(25) if (bi==i).sum()>=30]);h,y,w=bins.T
  for kind in ['spherical','exponential']:
   def model(p):
    c0,c1,a=p;t=h/a;return c0+c1*(np.where(t<1,1.5*t-.5*t**3,1) if kind=='spherical' else 1-np.exp(-3*t))
   fs=[least_squares(lambda p:(model(p)-y)*np.sqrt(w/w.max())/var,[var*.2,var*.8,a],bounds=([0,0,s/2],[var*5,var*5,50000])) for a in [3000,10000,20000]];f=min(fs,key=lambda f:sum(f.fun**2));c0,c1,a=f.x;out.append({'scale_m':s,'max_lag_m':lag,'model':kind,'nsr':c0/(c0+c1),'range_m':a})
pd.DataFrame(out).to_csv('04_outputs/grid_search/fit_sensitivity.csv',index=False)
r=pd.DataFrame(out)
for (lag,kind),g in r.groupby(['max_lag_m','model']):
 g=g.sort_values('scale_m');a=g.nsr.to_numpy();print(lag,kind,[(int(g.iloc[i].scale_m),round(a[i],4)) for i in range(1,len(a)-1) if a[i]<=a[i-1] and a[i]<a[i+1]])
