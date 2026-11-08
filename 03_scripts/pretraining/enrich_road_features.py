import sys,pathlib,json,collections
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import numpy as np,pandas as pd,geopandas as gpd
from shapely.geometry import Point
R=ROOT/'01_data/raw/pretraining_20261107';P=ROOT/'01_data/processed/pretraining_1km';Q=ROOT/'04_outputs/pretraining';g=gpd.read_file(P/'grid_1000.gpkg');city=g.geometry.union_all();origin=np.array([345000.,3730000.])
# TIGER topology IDs avoid treating every polyline vertex or clipped endpoint as a junction.
e=gpd.read_file(R/'tl_2021_06037_edges.zip',columns=['TLID','TNIDF','TNIDT','MTFCC','FULLNAME','geometry'],where="MTFCC IN ('S1200','S1400','S1640')").to_crs(26911);e=e[e.geometry.intersects(city.buffer(100))];node=collections.defaultdict(list)
for row in e.itertuples():
 c=list(row.geometry.coords)
 node[str(row.TNIDF)].append((str(row.TLID),c[0]));node[str(row.TNIDT)].append((str(row.TLID),c[-1]))
rows=[]
for nid,inc in node.items():
 degree=len({v[0] for v in inc})
 if degree<3:continue
 coords=np.array([v[1][:2] for v in inc]);pt=Point(coords[0]);spread=float(np.max(np.linalg.norm(coords-coords[0],axis=1)))
 if city.covers(pt):rows.append({'node_id':nid,'degree':degree,'coordinate_spread_m':spread,'geometry':pt})
n=gpd.GeoDataFrame(rows,crs=26911);n.to_file(P/'intersection_tiger_topology.gpkg',driver='GPKG');keys=np.floor((np.c_[n.geometry.x,n.geometry.y]-origin)/1000).astype(int);counts=collections.Counter(map(tuple,keys));out=g[['grid_id','i','j','city_area_km2']].copy() if 'city_area_km2' in g else None
if out is None:out=g[['grid_id','i','j']].copy();out['city_area_km2']=g.area/1e6
out['intersection_count']=[counts[(int(i),int(j))] for i,j in zip(out.i,out.j)];out['intersection_density_km2']=out.intersection_count/out.city_area_km2;print('TOPOLOGY',len(e),len(n),flush=True)
# Functional class length proportions are from their own Caltrans network denominator.
features=[]
for f in sorted(R.glob('functional_class_*.json')):features.extend(json.loads(f.read_text())['features'])
cr=gpd.GeoDataFrame.from_features(features,crs=4326).to_crs(26911);cr=cr[cr.geometry.intersects(city)].copy();cr.geometry=cr.geometry.intersection(city);cr=cr.explode(ignore_index=True);cr=cr[cr.length>1e-6];cr['functional_class']=pd.to_numeric(cr.F_System,errors='coerce');assert cr.functional_class.between(1,7).all();cr.to_file(P/'caltrans_functional_class_snapshot.gpkg',driver='GPKG')
parts=gpd.overlay(g[['grid_id','i','j','geometry']],cr[['functional_class','geometry']],how='intersection',keep_geom_type=False).explode(ignore_index=True);parts=parts[parts.geom_type.isin(['LineString','MultiLineString'])].copy();mid=parts.geometry.interpolate(.5,normalized=True);ij=np.floor((np.c_[mid.x,mid.y]-origin)/1000).astype(int);parts=parts[(parts.i.to_numpy()==ij[:,0])&(parts.j.to_numpy()==ij[:,1])].copy();parts['length_m']=parts.length;den=parts.groupby('grid_id').length_m.sum();out['functional_network_length_m']=out.grid_id.map(den).fillna(0)
for name,cs in [('freeway_share_functional',[1,2]),('arterial_share_functional',[3,4]),('collector_share_functional',[5,6]),('local_share_functional',[7])]:
 v=parts[parts.functional_class.isin(cs)].groupby('grid_id').length_m.sum();out[name]=out.grid_id.map(v).fillna(0)/out.functional_network_length_m.replace(0,np.nan)
out.drop(columns=['i','j','city_area_km2']).to_csv(P/'road_enrichment_1000.csv',index=False)
qa={'tiger_topology_edges':len(e),'junctions_degree_ge3':len(n),'n_coordinate_spread_gt1m':int((n.coordinate_spread_m>1).sum()),'topology_definition':'Unique TLID degree >=3 at existing TNID nodes on S1200/S1400/S1640 roads. Primary roads and ramps excluded. Does not node geometric crossings. Physical grade separation is not independently field-verified.','functional_source_features_downloaded':len(features),'functional_city_features':len(cr),'functional_class':'1 interstate,2 other freeway,3 other principal arterial,4 minor arterial,5 major collector,6 minor collector,7 local','functional_temporal_status':'current service snapshot; historical equivalence unverified','functional_total_length_m':float(cr.length.sum()),'functional_grid_length_m':float(den.sum())};assert abs(den.sum()-cr.length.sum())/cr.length.sum()<1e-6;(Q/'road_enrichment_qa.json').write_text(json.dumps(qa,indent=2));print('ENRICHMENT',qa,flush=True)
