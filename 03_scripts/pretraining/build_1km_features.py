"""Build exact 1 km target/features and fixed splits. Never fits an ML model."""
import sys,pathlib,json,hashlib,datetime,collections,re
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import numpy as np,pandas as pd,geopandas as gpd,shapely
from shapely.geometry import box,Point
from scipy.spatial.distance import pdist
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
P=ROOT/'01_data/processed/pretraining_1km';P.mkdir(exist_ok=True);Q=ROOT/'04_outputs/pretraining';Q.mkdir(exist_ok=True)
CRS=26911;S=1000;origin=np.array([345000.,3730000.]);qa={}
city=gpd.read_file(ROOT/'01_data/processed/city_boundary.gpkg').geometry.union_all();pts=gpd.read_file(ROOT/'01_data/processed/collisions_2017_2021.gpkg');assert len(pts)==230536
# Half-open grid assignment for all point datasets.
def ij(x,y):return np.floor((np.c_[x,y]-origin)/S).astype(int)
def keys(g):return [tuple(v) for v in ij(g.geometry.x,g.geometry.y)]
counts=collections.Counter(keys(pts));year=pd.to_datetime(pts.date_occ).dt.year;years={y:collections.Counter(keys(pts.loc[year==y])) for y in range(2017,2022)}
records=[];geoms=[];xmin,ymin,xmax,ymax=city.bounds
for i in range(int((xmax-origin[0])/S)+1):
 for j in range(int((ymax-origin[1])/S)+1):
  cell=box(origin[0]+i*S,origin[1]+j*S,origin[0]+(i+1)*S,origin[1]+(j+1)*S);geom=cell.intersection(city)
  if geom.area<=1:continue
  bx,by=i//5,j//5;test=(bx*73856093+by*19349663)%5==0;val=(bx*83492791+by*297121507)%5==1
  row={'grid_id':f'1000_{i}_{j}','i':i,'j':j,'block_id':f'{bx}_{by}','split':'test' if test else 'validation' if val else 'train','count_2017_2021':counts[(i,j)],'city_area_km2':geom.area/1e6,'city_area_fraction':geom.area/1e6,'cx':cell.centroid.x,'cy':cell.centroid.y}
  row.update({f'count_{y}':years[y][(i,j)] for y in years});records.append(row);geoms.append(geom)
g=gpd.GeoDataFrame(records,geometry=geoms,crs=CRS);g['eligible']=g.city_area_fraction>=.8;assert g.count_2017_2021.sum()==230536;assert g.geometry.is_valid.all();lookup={(int(r.i),int(r.j)):k for k,r in g.iterrows()}
# Raw targets for test cells are retained, but neither fit nor feature preprocessing reads them.
qa['grid']={'n_all':len(g),'n_eligible':int(g.eligible.sum()),'counts_conserved':int(g.count_2017_2021.sum()),'zero_rate_all':float((g.count_2017_2021==0).mean()),'split_cells_all':g.split.value_counts().to_dict(),'split_eligible':g[g.eligible].split.value_counts().to_dict(),'origin_m':origin.tolist()}
g.to_file(P/'grid_1000.gpkg',driver='GPKG');print('GRID',qa['grid'],flush=True)
# Population: original full BG area is the denominator, not its city-clipped area.
pop=pd.read_csv(ROOT/'01_data/interim/acs2021_la_blockgroup_population.csv',dtype={'GEOID':str});bg=gpd.read_file(ROOT/'01_data/processed/block_groups_2021.gpkg').merge(pop,on='GEOID',how='left',validate='one_to_one')
for c in ['population','population_moe90']:bg[c]=pd.to_numeric(bg[c],errors='coerce');bg.loc[bg[c]<0,c]=np.nan
assert bg.population.notna().all();bg['source_bg_area_m2']=bg.area;bg.to_file(P/'acs2021_population_bg.gpkg',driver='GPKG')
parts=gpd.overlay(g[['grid_id','geometry']],bg[['GEOID','population','population_moe90','source_bg_area_m2','geometry']],how='intersection',keep_geom_type=True);parts['area_m2']=parts.area;parts['weight']=parts.area_m2/parts.source_bg_area_m2;parts['pop_part']=parts.population*parts.weight;parts['moe2']=(parts.population_moe90*parts.weight)**2
agg=parts.groupby('grid_id').agg(population=('pop_part','sum'),moe2=('moe2','sum'),pop_area_m2=('area_m2','sum'));agg['population_moe90_approx']=np.sqrt(agg.pop('moe2'));g=g.merge(agg,on='grid_id',how='left',validate='one_to_one');g['population_density_km2']=g.population/g.city_area_km2;g['population_geometry_coverage']=g.pop_area_m2/(g.city_area_km2*1e6);qa['population']={'bg_matched':len(bg),'missing_population_bg':int(bg.population.isna().sum()),'population_allocated_city':float(g.population.sum()),'assumption':'Uniform population over each original BG total geometry, including water. MOE root-sum-square treats BG estimates as independent and is approximate.'};parts.drop(columns='geometry').to_csv(P/'population_crosswalk.csv',index=False);print('POP',qa['population'],flush=True)
# Motor vehicle roads. Preserve geometry-derived proxy and exact MTFCC class labels.
r=gpd.read_file(ROOT/'01_data/processed/roads_2021.gpkg');r=r[r.MTFCC.isin(['S1100','S1200','S1400','S1630','S1640'])].explode(index_parts=False,ignore_index=True);r['source_id']=np.arange(len(r));r['source_length']=r.length
parts=gpd.overlay(g[['grid_id','i','j','geometry']],r[['source_id','MTFCC','sinuosity','source_length','geometry']],how='intersection',keep_geom_type=False).explode(ignore_index=True)
# A line exactly on a grid edge belongs to its half-open midpoint cell, avoiding double length.
mid=parts.geometry.interpolate(.5,normalized=True);own=ij(mid.x,mid.y);parts=parts[(parts.i.to_numpy()==own[:,0])&(parts.j.to_numpy()==own[:,1])].copy();parts['part_length_m']=parts.length;parts=parts[parts.part_length_m>1e-6]
lengths=parts.groupby('grid_id').part_length_m.sum();g['road_length_m']=g.grid_id.map(lengths).fillna(0);g['road_density_km_per_km2']=g.road_length_m/1000/g.city_area_km2
classes=parts.pivot_table(index='grid_id',columns='MTFCC',values='part_length_m',aggfunc='sum',fill_value=0)
for c in ['S1100','S1200','S1400','S1630','S1640']:
 vals=g.grid_id.map(classes[c] if c in classes else pd.Series(dtype=float)).fillna(0);g[f'road_share_{c}']=np.where(g.road_length_m>0,vals/g.road_length_m,np.nan)
valid=parts.sinuosity.notna()&np.isfinite(parts.sinuosity)&(parts.sinuosity>=1-1e-6);weighted=(parts.loc[valid,'part_length_m']*parts.loc[valid,'sinuosity']).groupby(parts.loc[valid,'grid_id']).sum();covered=parts.loc[valid].groupby('grid_id').part_length_m.sum();g['road_sinuosity_length_weighted']=g.grid_id.map(weighted)/g.grid_id.map(covered);g['sinuosity_length_coverage']=g.grid_id.map(covered).fillna(0)/g.road_length_m.replace(0,np.nan)
qa['roads']={'motorized_segments':len(r),'original_city_length_m':float(r.length.sum()),'grid_length_m':float(g.road_length_m.sum()),'length_relative_difference':float(abs(g.road_length_m.sum()-r.length.sum())/r.length.sum()),'class_labels':'S1100 primary; S1200 secondary; S1400 local; S1630 ramp; S1640 service drive. S1200 is not assumed arterial.'}
print('LENGTH_CHECK',qa['roads'],flush=True);assert qa['roads']['length_relative_difference']<1e-6;parts[['grid_id','source_id','MTFCC','part_length_m','sinuosity']].to_csv(P/'road_crosswalk.csv',index=False);print('ROADS',qa['roads'],flush=True)
# Avoid artificial city-boundary intersections: use original TIGER endpoints before clipping.
full=gpd.read_file(ROOT/'01_data/raw/tiger_roads_2021.zip').to_crs(CRS);full=full[full.MTFCC.isin(['S1200','S1400','S1640'])];full=full[full.geometry.intersects(city.buffer(100))].explode(ignore_index=True)
node=collections.defaultdict(list)
for idx,row in full.iterrows():
 coords=list(row.geometry.coords)
 for end,other in [(coords[0],coords[1]),(coords[-1],coords[-2])]:
  key=tuple(np.round(np.array(end)/.1).astype(int));angle=float(np.arctan2(other[1]-end[1],other[0]-end[0]));node[key].append((idx,angle,str(row.FULLNAME)))
nodes=[]
for (x,y),inc in node.items():
 ids={t[0] for t in inc};angles=sorted({round(t[1],2) for t in inc});names={t[2] for t in inc if t[2]!='None'}
 if len(ids)>=3 and len(angles)>=3:
  pt=Point(x*.1,y*.1)
  if city.covers(pt):nodes.append({'degree':len(ids),'street_name_count':len(names),'geometry':pt})
n=gpd.GeoDataFrame(nodes,crs=CRS);n.to_file(P/'intersection_endpoint_candidates.gpkg',driver='GPKG');nc=collections.Counter(keys(n));g['intersection_endpoint_candidate_count']=[nc[(int(i),int(j))] for i,j in zip(g.i,g.j)];g['intersection_density_candidate_km2']=g.intersection_endpoint_candidate_count/g.city_area_km2
qa['intersections']={'candidate_nodes':len(n),'definition':'Original TIGER endpoints rounded to 0.1 m, >=3 distinct incident segments and >=3 direction bins; excludes primary roads and ramps. Endpoint graph only, no geometric-crossing noding. Grade separation not fully encoded; remains a proxy requiring audit.'};print('NODES',len(n),flush=True)
# Land use: union within category prevents same-category duplicate area. Keep cross-category overlap explicit.
lu=gpd.read_file(ROOT/'01_data/processed/landuse.gpkg');catmap={re.sub('[^a-z0-9]+','_',c.lower()).strip('_'):c for c in lu.Category.unique()};catreverse={v:k for k,v in catmap.items()};idx=lu.sindex
from concurrent.futures import ThreadPoolExecutor

def local_landuse(k):
 geom=g.geometry.iloc[k];matches=idx.query(geom,predicate='intersects');sub=lu.iloc[matches];unions={}
 for cat,group in sub.groupby('Category'):
  pieces=shapely.intersection(group.geometry.to_numpy(),geom);unions[catreverse[cat]]=shapely.union_all(pieces)
 row={name:float(unions[name].area) if name in unions else 0.0 for name in catmap};row['coverage_m2']=float(shapely.union_all(list(unions.values())).area) if unions else 0.0
 return row
with ThreadPoolExecutor(max_workers=6) as pool:landrows=list(pool.map(local_landuse,range(len(g))))
la=pd.DataFrame(landrows)
for name in catmap:g['landuse_share_'+name]=la[name].to_numpy()/(g.city_area_km2.to_numpy()*1e6)
g['landuse_coverage']=la.coverage_m2.to_numpy()/(g.city_area_km2.to_numpy()*1e6);cols=[c for c in g if c.startswith('landuse_share_')];g['landuse_overlap_fraction']=g[cols].sum(axis=1)-g.landuse_coverage;g['landuse_uncovered_fraction']=(1-g.landuse_coverage).clip(0,1);qa['landuse']={'categories':catmap,'max_cross_category_overlap_fraction':float(g.landuse_overlap_fraction.max()),'n_cells_overlap_gt_1pct':int((g.landuse_overlap_fraction>.01).sum()),'snapshot':'current General Plan Land Use; not proof of 2017–2021 conditions'};print('LANDUSE',qa['landuse'],flush=True)
# Signals and potential traffic coverage are explicitly separate from measured traffic volume.
sig=gpd.read_file(ROOT/'01_data/processed/signal_locations.gpkg');sig['xykey']=sig.geometry.map(lambda p:(round(p.x,1),round(p.y,1)));sig=sig.drop_duplicates('xykey');sc=collections.Counter(keys(sig));g['signal_point_count']=[sc[(int(i),int(j))] for i,j in zip(g.i,g.j)];g['signal_density_snapshot_km2']=g.signal_point_count/g.city_area_km2
traffic=gpd.read_file(ROOT/'01_data/processed/traffic_counts.gpkg');pairs=g.sindex.query(traffic.geometry,predicate='intersects');loc=pd.Series(pairs[1]).value_counts();g['traffic_report_location_count']=g.index.to_series().map(loc).fillna(0).astype(int);g['traffic_volume_2017_2021']=np.nan;g['traffic_volume_observed']=False;qa['signals']={'source_points':5506,'unique_coordinate_points':len(sig),'temporal_status':'snapshot; no installation/retirement history'};qa['traffic']={'location_coverage_all':float((g.traffic_report_location_count>0).mean()),'value_coverage_all':0.0,'values_obtained':False}
# Diagnostics fit all non-test eligible cells. Validation split reserved for future model tuning.
use=g[g.eligible & (g.split!='test')];z=use.count_2017_2021.to_numpy(float);xy=use[['cx','cy']].to_numpy();d=pdist(xy);v=.5*pdist(z[:,None],'sqeuclidean');b=np.floor(d/1000).astype(int);rec=[]
for k in range(25):
 m=b==k
 if m.sum()>=30:rec.append((d[m].mean(),v[m].mean(),int(m.sum())))
bins=np.array(rec);h,y,w=bins.T;var=np.var(z)
def model(p):
 c0,c1,a=p;t=h/a;return c0+c1*np.where(t<1,1.5*t-.5*t**3,1)
fits=[least_squares(lambda p:(model(p)-y)*np.sqrt(w/w.max())/var,[var*.2,var*.8,a],bounds=([0,0,500],[var*5,var*5,50000])) for a in [2000,5000,10000,20000]];f=min(fits,key=lambda f:sum(f.fun**2));c0,c1,a=f.x;_,nn=cKDTree(xy).query(xy,k=9);nn=nn[:,1:];zz=z-z.mean();I=float(np.sum(zz[:,None]*zz[nn])/8/np.sum(zz*zz));rng=np.random.default_rng(575);perm=[]
for _ in range(199):
 q=rng.permutation(zz);perm.append(np.sum(q[:,None]*q[nn])/8/np.sum(q*q))
pval=(1+sum(abs(np.array(perm)+1/(len(z)-1))>=abs(I+1/(len(z)-1))))/200
qa['grid_diagnostics']={'scale_m':1000,'n_fit':len(z),'max_lag_m':25000,'model':'spherical','nugget':float(c0),'partial_sill':float(c1),'sill':float(c0+c1),'nsr':float(c0/(c0+c1)),'range_m':float(a),'range_extrapolated':bool(a>h.max()),'moran_i_knn8':I,'moran_permutations':199,'moran_p':float(pval),'claim':'practical 1 km scale; not NSR-selected optimum'};pd.DataFrame(bins,columns=['lag_m','semivariance','pairs']).to_csv(Q/'variogram_1000.csv',index=False)
# Save complete all-cell table and geometries. Missing traffic values remain null.
g.to_file(P/'grid_features_1000.gpkg',driver='GPKG');g.drop(columns='geometry').to_csv(P/'model_table_1000.csv',index=False)
g[['grid_id','block_id','split','eligible']].to_csv(P/'spatial_split_1000.csv',index=False);assert not(g.groupby('block_id').split.nunique()>1).any();qa['no_block_split_leakage']=True
miss=g.drop(columns='geometry').isna().sum().rename('missing').to_frame();miss['fraction']=miss['missing']/len(g);miss.to_csv(Q/'missingness.csv');(Q/'feature_build_qa.json').write_text(json.dumps(qa,indent=2));print('DIAGNOSTICS',qa['grid_diagnostics'],flush=True);print('FEATURE TABLE',g.shape,flush=True)

