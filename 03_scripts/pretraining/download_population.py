import sys,pathlib,json,hashlib,datetime
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import requests
R=pathlib.Path('01_data/raw/pretraining_20261107')
u='https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/acsdt5y2021-b01003.dat'
p=R/'acsdt5y2021-b01003.dat'
if not p.exists():
 r=requests.get(u,timeout=180);r.raise_for_status();assert not r.content.lstrip().startswith(b'<');p.write_bytes(r.content)
print('ACS',p.stat().st_size,p.open().readline()[:300],flush=True)
for name,url in [('ladot_traffic21','https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/21'),('nav_home','https://navigatela.lacity.org/navigatela/'),('collision_current','https://data.lacity.org/api/views/d5tf-ez2w.json')]:
 try:
  r=requests.get(url,params={'f':'pjson'} if 'MapServer' in url else None,timeout=60);(R/(name+'.txt')).write_bytes(r.content)
  print(name,r.status_code,r.url,flush=True)
  if 'MapServer' in url:print([(f['name'],f.get('alias')) for f in r.json().get('fields',[])],flush=True)
 except Exception as e:print(name,str(e)[:150],flush=True)
