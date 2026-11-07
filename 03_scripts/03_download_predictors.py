import sys,json,pathlib,hashlib,time,concurrent.futures,datetime
sys.path.insert(0,'.runtime')
import requests
R=pathlib.Path('01_data/raw')
def query(u,params,post=False):
 for attempt in range(4):
  try:
   rr=requests.post(u,data=params,timeout=180) if post else requests.get(u,params=params,timeout=180);rr.raise_for_status();d=rr.json();assert 'error' not in d,d;return d
  except Exception:
   if attempt==3:raise
   time.sleep(attempt+1)
for name,service in [('traffic_counts','LADOT/MapServer/22'),('signal_locations','LADOT/MapServer/30'),('landuse','City_Planning_Department/MapServer/7')]:
 u='https://maps.lacity.org/lahub/rest/services/'+service
 m=query(u,{'f':'pjson'});(R/(name+'_metadata.json')).write_text(json.dumps(m));ids=query(u+'/query',{'f':'pjson','where':'1=1','returnIdsOnly':'true'});(R/(name+'_ids.json')).write_text(json.dumps(ids));oi=ids.get('objectIds',[]);print(name,len(oi),flush=True)
 def batch(i):
  p=R/f'{name}_batch_{i}.json';subset=oi[i:i+500]
  if p.exists():
   d=json.loads(p.read_text())
   if len(d.get('features',[]))==len(subset):return len(subset)
  d=query(u+'/query',{'f':'geojson','objectIds':','.join(map(str,subset)),'outFields':'*','outSR':4326},True);assert 'features' in d and len(d['features'])==len(subset),(name,i,len(d.get('features',[])),len(subset));p.write_text(json.dumps(d));return len(subset)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  total=0
  for n in pool.map(batch,range(0,len(oi),500)):
   total+=n
   if total%5000==0:print(name,total,flush=True)
 assert total==len(oi)
manifest=[]
for p in R.iterdir():
 if p.is_file():manifest.append({'file':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
pathlib.Path('00_admin/file_manifest.json').write_text(json.dumps({'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':manifest},indent=2))
