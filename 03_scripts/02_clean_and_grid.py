import sys,json,pathlib
sys.path.insert(0,'.runtime')
import numpy as np,pandas as pd,geopandas as gpd
from shapely.geometry import box
from scipy.spatial.distance import pdist
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path; CRS=26911
boundary=gpd.read_file('01_data/raw/city_boundary.json').to_crs(CRS);boundary.geometry=boundary.geometry.make_valid(); city=boundary.geometry.union_all();boundary.to_file('01_data/processed/city_boundary.gpkg',driver='GPKG')
rows=[]
for f in sorted(P('01_data/raw').glob('collisions_20*.json')):rows+=json.loads(f.read_text())
df=pd.DataFrame(rows);audit={'downloaded':len(df),'duplicate_ids':int(df.dr_no.duplicated().sum())};df=df.drop_duplicates('dr_no');df['date_occ']=pd.to_datetime(df.date_occ);df['lon']=df.location_1.map(lambda d:float(d.get('longitude',np.nan)) if isinstance(d,dict) else np.nan);df['lat']=df.location_1.map(lambda d:float(d.get('latitude',np.nan)) if isinstance(d,dict) else np.nan)
valid=df.lon.between(-119,-117)&df.lat.between(33,35);audit['invalid_coordinates']=int((~valid).sum()); pts=gpd.GeoDataFrame(df[valid].drop(columns='location_1'),geometry=gpd.points_from_xy(df[valid].lon,df[valid].lat),crs=4326).to_crs(CRS);inside=pts.geometry.intersects(city);audit['outside_city']=int((~inside).sum());pts=pts[inside].copy();audit['retained']=len(pts);pts.to_file('01_data/processed/collisions_2017_2021.gpkg',driver='GPKG');P('04_outputs/qa/collision_cleaning.json').write_text(json.dumps(audit,indent=2));print(audit,flush=True)
xy=np.c_[pts.geometry.x,pts.geometry.y];xmin,ymin,xmax,ymax=city.bounds;origin=np.floor(np.array([xmin,ymin])/5000)*5000
# Reserve geographic blocks before scale selection; held-out target counts never enter variograms.
bx=np.floor((xy[:,0]-origin[0])/5000).astype(int);by=np.floor((xy[:,1]-origin[1])/5000).astype(int);held=((bx*73856093+by*19349663)%5)==0
P('02_config/spatial_holdout.json').write_text(json.dumps({'block_m':5000,'origin':origin.tolist(),'rule':'(bx*73856093+by*19349663)%5 == 0','heldout_points':int(held.sum()),'seed':575},indent=2))
res=[];rng=np.random.default_rng(575)
def model(h,c0,c1,a):
 t=h/a;return c0+c1*np.where(t<1,1.5*t-.5*t**3,1)
for s in range(500,5001,150):
 ix=np.floor((xy[:,0]-origin[0])/s).astype(int);iy=np.floor((xy[:,1]-origin[1])/s).astype(int);counts=pd.Series(list(zip(ix,iy))).value_counts();records=[];geoms=[]
 for i in range(int((xmax-origin[0])/s)+1):
  for j in range(int((ymax-origin[1])/s)+1):
   cell=box(origin[0]+i*s,origin[1]+j*s,origin[0]+(i+1)*s,origin[1]+(j+1)*s);clip=cell.intersection(city)
   if clip.area>1:
    # Exclude every cell intersecting a reserved block, preventing cross-boundary leakage.
    block_ids=[(a,b) for a in range(int(np.floor((cell.bounds[0]-origin[0])/5000)),int(np.floor((cell.bounds[2]-origin[0]-1e-6)/5000))+1) for b in range(int(np.floor((cell.bounds[1]-origin[1])/5000)),int(np.floor((cell.bounds[3]-origin[1]-1e-6)/5000))+1)]
    test=any((a*73856093+b*19349663)%5==0 for a,b in block_ids)
    records.append({'grid_id':f'{s}_{i}_{j}','i':i,'j':j,'count':int(counts.get((i,j),0)),'area_km2':clip.area/1e6,'area_fraction':clip.area/s**2,'holdout':test,'cx':cell.centroid.x,'cy':cell.centroid.y});geoms.append(clip)
 g=gpd.GeoDataFrame(records,geometry=geoms,crs=CRS);assert g['count'].sum()==len(pts);g.to_file(f'04_outputs/grid_search/grid_{s}.gpkg',driver='GPKG')
 # near-complete cells avoid unequal-area count artifacts; no zero-count cells are dropped.
 use=g[(~g.holdout)&(g.area_fraction>=.8)];coords=use[['cx','cy']].to_numpy();z=use['count'].to_numpy(float);n=len(z)
 if n<30:
  res.append({'scale_m':s,'n_fit':n,'status':'too_few_cells','nsr':float('nan')});pd.DataFrame(res).to_csv('04_outputs/grid_search/scale_diagnostics.csv',index=False);continue
 if n>2500:sel=rng.choice(n,2500,replace=False);coords=coords[sel];z=z[sel];n=len(z)
 d=pdist(coords);gamma=.5*pdist(z[:,None],metric='sqeuclidean');edges=np.linspace(0,25000,26);bi=np.digitize(d,edges)-1;bins=[]
 for b in range(25):
  ok=bi==b
  if ok.sum()>=30:bins.append((d[ok].mean(),gamma[ok].mean(),ok.sum()))
 bins=np.array(bins);h,v,w=bins.T;var=np.var(z);fits=[]
 for a in [2000,5000,10000,20000]:
  fit=least_squares(lambda p:(model(h,*p)-v)*np.sqrt(w/w.max())/max(var,1),[var*.2,var*.8,max(a,s)],bounds=([0,0,s/2],[var*5,var*5,50000]));fits.append(fit)
 fit=min(fits,key=lambda f:np.sum(f.fun**2));c0,c1,a=fit.x;nsr=c0/(c0+c1);rmse=np.sqrt(np.mean((model(h,*fit.x)-v)**2))/max(var,1)
 dist,nn=cKDTree(coords).query(coords,k=min(9,n));nn=nn[:,1:];zz=z-z.mean();I=float(np.sum(zz[:,None]*zz[nn])/nn.shape[1]/np.sum(zz**2)); sims=np.array([np.sum((q:=rng.permutation(zz))[:,None]*q[nn])/nn.shape[1]/np.sum(q*q) for _ in range(199)]);p=(1+np.sum(abs(sims+1/(n-1))>=abs(I+1/(n-1))))/200
 row={'scale_m':s,'n_all':len(g),'n_fit':len(use),'zero_rate':float((g['count']==0).mean()),'nugget':c0,'partial_sill':c1,'sill':c0+c1,'range_m':a,'nsr':nsr,'fit_nrmse':rmse,'moran_i_knn8':I,'moran_p_199':p,'traffic_coverage':None,'status':'ok' if a<49000 and rmse<.35 else 'unstable_fit'};res.append(row);pd.DataFrame(res).to_csv('04_outputs/grid_search/scale_diagnostics.csv',index=False);pd.DataFrame(bins,columns=['lag_m','semivariance','pairs']).to_csv(f'04_outputs/grid_search/variogram_{s}.csv',index=False);print(s,round(nsr,4),len(use),row['status'],flush=True)
r=pd.DataFrame(res);plt.figure(figsize=(10,5));plt.plot(r.scale_m,r.nsr,'o-');plt.xlabel('Grid side (m)');plt.ylabel('Nugget / total sill');plt.grid(alpha=.3);plt.tight_layout();plt.savefig('04_outputs/figures/nsr_scale.png',dpi=180)
local=[]
for k in range(1,len(r)-1):
 if r.iloc[k].nsr<=r.iloc[k-1].nsr and r.iloc[k].nsr<r.iloc[k+1].nsr and r.iloc[k].status=='ok' and r.iloc[k].n_fit>=100:local.append(int(r.iloc[k].scale_m))
P('04_outputs/grid_search/selection.json').write_text(json.dumps({'status':'candidate_requires_sensitivity_and_traffic_audit','local_minima_m':local,'first_candidate_m':local[0] if local else None,'traffic_coverage_verified':False,'fit_model':'spherical','max_lag_m':25000,'boundary_cell_min_fraction':.8},indent=2))

