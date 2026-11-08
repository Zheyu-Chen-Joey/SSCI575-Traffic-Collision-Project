import sys,pathlib,json,hashlib,datetime
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import requests
R=pathlib.Path('01_data/raw/pretraining_20261107');base='https://data.lacity.org'
for name,url,params in [('traffic_summary_metadata',base+'/api/views/94wu-3ps3.json',{}),('traffic_summary',base+'/resource/94wu-3ps3.json',{'$limit':50000}),('collision_counts_by_year',base+'/resource/d5tf-ez2w.json',{'$select':'date_extract_y(date_occ) as year,count(*) as n','$where':"date_occ >= '2017-01-01T00:00:00' AND date_occ < '2022-01-01T00:00:00'",'$group':'year','$order':'year'})]:
 p=R/(name+'.json')
 if p.exists():d=json.loads(p.read_text())
 else:
  r=requests.get(url,params=params,timeout=90);r.raise_for_status();d=r.json();assert not isinstance(d,dict) or 'error' not in d;p.write_text(json.dumps(d))
 if name.endswith('metadata'):print(name,[(c.get('fieldName'),c.get('name')) for c in d.get('columns',[])],d.get('description'),flush=True)
 else:print(name,len(d),str(d[:2])[:1000],flush=True)
