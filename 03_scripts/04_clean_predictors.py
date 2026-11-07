import sys,json,pathlib
sys.path.insert(0,'.runtime')
import geopandas as gpd,pandas as pd,numpy as np
from shapely.geometry import Point
P=pathlib.Path;city=gpd.read_file('01_data/processed/city_boundary.gpkg').geometry.union_all();qa=[]
r=gpd.read_file('01_data/raw/tiger_roads_2021.zip').to_crs(26911);r=r[r.geometry.intersects(city)].copy();r.geometry=r.geometry.intersection(city);r=r[~r.geometry.is_empty & (r.geometry.length>0)].copy();r['length_m']=r.length
# Ratio on original TIGER segments is a geometry proxy, not physical turning curvature.
def sinu(g):
 if g.geom_type!='LineString':return np.nan
 d=Point(g.coords[0]).distance(Point(g.coords[-1]));return g.length/d if d>1 else np.nan
r['sinuosity']=r.geometry.map(sinu);r.to_file('01_data/processed/roads_2021.gpkg',driver='GPKG');qa.append({'dataset':'roads','retained':len(r),'status':'cleaned; MTFCC is not calibrated arterial classification'})
bg=gpd.read_file('01_data/raw/block_groups_2021.zip').to_crs(26911);bg=bg[bg.COUNTYFP=='037'];bg=bg[bg.geometry.intersects(city)];bg.to_file('01_data/processed/block_groups_2021.gpkg',driver='GPKG');qa.append({'dataset':'block_groups','retained':len(bg),'status':'geometry only; population API requires key'})
for name in ['traffic_counts','landuse','signal_locations']:
 files=list(P('01_data/raw').glob(name+'_batch_*.json'))
 if not files:continue
 fs=[]
 for f in files:fs.extend(json.loads(f.read_text()).get('features',[]))
 g=gpd.GeoDataFrame.from_features(fs,crs=4326).to_crs(26911);g=g[g.geometry.notna()].copy();g.geometry=g.geometry.make_valid();g=g[g.geometry.intersects(city)].copy();g.geometry=g.geometry.intersection(city);g.to_file(f'01_data/processed/{name}.gpkg',driver='GPKG');qa.append({'dataset':name,'downloaded':len(fs),'retained':len(g),'columns':list(g.columns),'status':'spatially cleaned; temporal audit required'})
P('04_outputs/qa/predictor_cleaning.json').write_text(json.dumps(qa,indent=2));print(qa)
