import sys,pathlib,json,hashlib,datetime,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import requests,geopandas as gpd
R=ROOT/'01_data/raw/speed_audit_20261107';R.mkdir(exist_ok=True);U='https://geo.dot.gov/server/rest/services/Hosted/fhwa__2022_speed_limit_study_results__all_states/FeatureServer/0'
policy={'purpose':'Eligibility for enhanced citywide1km model; no fitting','minimum_city_motorized_road_corridor_coverage':.8,'minimum_training_cell_fraction_with_80pct_road_corridor_coverage':.8,'buffer_sensitivity_m':[10,20,30,50],'decision_buffer_m':30,'temporal_requirement':'Record year within2017–2021 AND speed observation/effective period documented as applicable to target period. Inventory linework year alone is insufficient.','threshold_basis':'Operational project screening rule, not universal statistical cutoff. Corridor buffers give potential spatial overlap, not verified road-link matching. Low upper-bound coverage is sufficient for rejection; a high score would still require link matching.'};(ROOT/'02_config/speed_admission_policy.json').write_text(json.dumps(policy,indent=2))
city=gpd.read_file(ROOT/'01_data/processed/city_boundary.gpkg').to_crs(4326);a,b,c,d=city.total_bounds;geometry=f'{a-.005},{b-.005},{c+.005},{d+.005}'
params={'f':'json','where':'state_code=6','geometry':geometry,'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','returnIdsOnly':'true'}
def fetch(url,data):
 for k in range(3):
  try:
   r=requests.post(url,data=data,timeout=120);r.raise_for_status();v=r.json();assert not isinstance(v,dict) or 'error' not in v,v;return v
  except Exception:
   if k==2:raise
p=R/'query_ids.json'
if p.exists():ids=json.loads(p.read_text())['objectIds']
else:
 result=fetch(U+'/query',params);ids=result['objectIds'];p.write_text(json.dumps(result));(R/'query_definition.json').write_text(json.dumps(params,indent=2))
assert len(ids)==len(set(ids));print('BBOX_OBJECTS',len(ids),flush=True)
def batch(i):
 oi=ids[i:i+200];p=R/f'speed_batch_{i:05d}.geojson'
 if p.exists():v=json.loads(p.read_text())
 else:
  v=fetch(U+'/query',{'f':'geojson','objectIds':','.join(map(str,oi)),'outFields':'*','outSR':4326});assert 'features' in v and not v.get('exceededTransferLimit',False);p.write_text(json.dumps(v))
 assert len(v['features'])==len(oi);return v['features']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:parts=list(ex.map(batch,range(0,len(ids),200)))
features=[f for group in parts for f in group];got=[int(f['properties']['objectid']) for f in features];assert set(got)==set(ids) and len(got)==len(ids)
manifest={'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'service_url':U,'requested_objects':len(ids),'received_unique_objects':len(got),'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in R.iterdir() if p.is_file()]};(ROOT/'00_admin/speed_download_manifest.json').write_text(json.dumps(manifest,indent=2));print('DOWNLOAD_COMPLETE',len(got),flush=True)
