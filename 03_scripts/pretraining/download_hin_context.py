"""Official HIN2024 download; context only, never a predictor or tuning target."""
import sys,pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import requests,geopandas as gpd
R=ROOT/'01_data/raw/hin_context_20261107';R.mkdir(exist_ok=True);U='https://maps.lacity.org/arcgis/rest/services/Mapping/NavigateLA/MapServer/172'
def get(params):
 r=requests.get(U+'/query',params=params,timeout=60);r.raise_for_status();v=r.json();assert 'error'not in v;assert not v.get('exceededTransferLimit',False);return v
p=R/'ids.json'
if not p.exists():p.write_text(json.dumps(get({'f':'json','where':'1=1','returnIdsOnly':'true'})),encoding='utf-8')
ids=json.loads(p.read_text())['objectIds'];assert len(ids)==len(set(ids));features=[]
for i in range(0,len(ids),500):
 p=R/f'batch_{i:05d}.geojson';batch=ids[i:i+500]
 if not p.exists():p.write_text(json.dumps(get({'f':'geojson','objectIds':','.join(map(str,batch)),'outFields':'*','outSR':4326})),encoding='utf-8')
 v=json.loads(p.read_text());assert len(v['features'])==len(batch);features.extend(v['features'])
assert len(features)==len(ids);actual=[f['properties']['AutoID']for f in features];assert len(set(actual))==len(ids)and set(actual)==set(ids)
g=gpd.GeoDataFrame.from_features(features,crs=4326).to_crs(26911);city=gpd.read_file(ROOT/'01_data/processed/city_boundary.gpkg').geometry.union_all();g=g[g.intersects(city)].copy();g.geometry=g.geometry.intersection(city);g=g[g.length>1e-6];g.to_file(ROOT/'01_data/processed/hin_2024_context.gpkg',driver='GPKG')
m={'source':U,'downloaded_objects':len(ids),'city_features':len(g),'city_source_length_km_summed':float(g.length.sum()/1000),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'role':'context only; same historic crash period makes it non-independent validation','files':[{'path':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}for f in R.glob('*')]};(ROOT/'00_admin/hin_manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in m.items()if k!='files'}))
