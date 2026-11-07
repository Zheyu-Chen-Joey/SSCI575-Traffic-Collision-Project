import sys
sys.path.insert(0,'.runtime')
import requests,json,pathlib,time,hashlib
R=pathlib.Path('01_data/raw'); log=[]
def get(name,url,params=None):
 p=R/name
 if p.exists(): return json.loads(p.read_text()) if p.suffix=='.json' else None
 r=requests.get(url,params=params,timeout=180);r.raise_for_status();
 if p.suffix=='.json':
  try: r.json()
  except ValueError:
   p.with_suffix('.failed.html').write_bytes(r.content);raise RuntimeError(f'{name}: expected JSON; API returned HTML, check authentication or service status')
 p.write_bytes(r.content);log.append({'file':str(p),'url':r.url,'sha256':hashlib.sha256(r.content).hexdigest()});print(name,len(r.content),flush=True);pathlib.Path('00_admin/download_manifest.json').write_text(json.dumps(log,indent=2))
 return r.json() if p.suffix=='.json' else None
for year in range(2017,2022):
 get(f'collisions_{year}.json','https://data.lacity.org/resource/d5tf-ez2w.json',{'$where':f"date_occ >= '{year}-01-01T00:00:00' AND date_occ < '{year+1}-01-01T00:00:00'",'$limit':100000,'$order':'dr_no','$select':'dr_no,date_occ,date_rptd,location_1'})
get('city_boundary.json','https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/7/query',{'where':'1=1','outFields':'*','outSR':4326,'f':'geojson'})
get('tiger_roads_2021.zip','https://www2.census.gov/geo/tiger/TIGER2021/ROADS/tl_2021_06037_roads.zip')
get('block_groups_2021.zip','https://www2.census.gov/geo/tiger/TIGER2021/BG/tl_2021_06_bg.zip')
get('acs2021_population.json','https://api.census.gov/data/2021/acs/acs5',{'get':'NAME,B01003_001E,B01003_001M','for':'block group:*','in':'state:06 county:037'})
url='https://services1.arcgis.com/tp9wqSVX1AitKgjd/arcgis/rest/services/Vision_Zero__Improvements/FeatureServer/2'
meta=get('signals_metadata.json',url,{'f':'json'});ids=get('signals_ids.json',url+'/query',{'f':'json','where':'1=1','returnIdsOnly':'true'})
if ids.get('objectIds'):
 for i in range(0,len(ids['objectIds']),500):get(f'signals_{i}.json',url+'/query',{'f':'geojson','objectIds':','.join(map(str,ids['objectIds'][i:i+500])),'outFields':'*','outSR':4326})
pathlib.Path('00_admin/download_manifest.json').write_text(json.dumps(log,indent=2))
