import sys,json,pathlib
sys.path.insert(0,'.runtime')
import geopandas as gpd,numpy as np,pandas as pd
from shapely.geometry import box
from scipy.spatial.distance import pdist
from scipy.optimize import least_squares
city=gpd.read_file('01_data/processed/city_boundary.gpkg').geometry.union_all();pts=gpd.read_file('01_data/processed/collisions_2017_2021.gpkg');xy=np.c_[pts.geometry.x,pts.geometry.y];base=np.array(json.load(open('02_config/spatial_holdout.json'))['origin']);xmin,ymin,xmax,ymax=city.bounds;out=[]
for ox,oy in [(0,0),(.5,0),(0,.5),(.5,.5)]:
 for s in range(800,1851,150):
  origin=base+np.array([ox,oy])*s;ij=np.floor((xy-origin)/s).astype(int);counts=pd.Series(list(map(tuple,ij))).value_counts();coords=[];z=[]
  for i in range(-1,int((xmax-origin[0])/s)+1):
   for j in range(-1,int((ymax-origin[1])/s)+1):
    x,y=origin+np.array([i,j])*s;cell=box(x,y,x+s,y+s)
    if cell.intersection(city).area/s**2<.8:continue
    if any((a*73856093+b*19349663)%5==0 for a in range(int(np.floor((x-base[0])/5000)),int(np.floor((x+s-base[0]-1e-6)/5000))+1) for b in range(int(np.floor((y-base[1])/5000)),int(np.floor((y+s-base[1]-1e-6)/5000))+1)):continue
    coords.append((x+s/2,y+s/2));z.append(counts.get((i,j),0))
  z=np.array(z,float);d=pdist(coords);v=.5*pdist(z[:,None],'sqeuclidean');bi=np.digitize(d,np.linspace(0,25000,26))-1;bins=np.array([(d[bi==k].mean(),v[bi==k].mean(),(bi==k).sum()) for k in range(25) if (bi==k).sum()>=30]);h,y,w=bins.T;var=np.var(z)
  def fun(p):
   c0,c1,a=p;t=h/a;return (c0+c1*np.where(t<1,1.5*t-.5*t**3,1)-y)*np.sqrt(w/w.max())/var
  fs=[least_squares(fun,[var*.2,var*.8,a],bounds=([0,0,s/2],[var*5,var*5,50000])) for a in [2000,5000,10000,20000]];f=min(fs,key=lambda f:sum(f.fun**2));c0,c1,a=f.x;out.append({'offset_x_fraction':ox,'offset_y_fraction':oy,'scale_m':s,'n_fit':len(z),'nsr':c0/(c0+c1),'range_m':a})
 print('origin',ox,oy,'done',flush=True)
pd.DataFrame(out).to_csv('04_outputs/grid_search/origin_sensitivity.csv',index=False)
