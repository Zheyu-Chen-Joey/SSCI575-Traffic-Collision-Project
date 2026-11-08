import sys,pathlib,json,concurrent.futures
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import requests
R=pathlib.Path('01_data/raw/pretraining_20261107');base='https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/CRS_Functional_Classification/FeatureServer/0';ids=json.load(open(R/'caltrans_ids.json'))['objectIds'];print('CALTRANS',len(ids),flush=True)
def batch(k):
 p=R/f'functional_class_{k}.json';oi=ids[k:k+500]
 if p.exists():return
 r=requests.post(base+'/query',data={'f':'geojson','objectIds':','.join(map(str,oi)),'outFields':'*','outSR':4326},timeout=120);r.raise_for_status();d=r.json();assert 'features' in d and len(d['features'])==len(oi) and not d.get('exceededTransferLimit',False);p.write_text(json.dumps(d))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(batch,range(0,len(ids),500)))
u='https://www2.census.gov/geo/tiger/TIGER2021/EDGES/tl_2021_06037_edges.zip';p=R/'tl_2021_06037_edges.zip'
if not p.exists():
 r=requests.get(u,timeout=180);r.raise_for_status();assert r.content[:2]==b'PK';p.write_bytes(r.content)
print('EDGES',p.stat().st_size,flush=True)
