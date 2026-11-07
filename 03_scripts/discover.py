import sys,json
sys.path.insert(0,'.runtime')
import requests
for key,url in [('newcollision','https://data.lacity.org/resource/s2yz-yg2p.json?$limit=1'),('planning','https://maps.lacity.org/lahub/rest/services/City_Planning_Department/MapServer?f=json'),('traffic','https://maps.lacity.org/lahub/rest/services/LADOT/MapServer?f=json')]:
 r=requests.get(url,timeout=90);open('01_data/raw/'+key+'_metadata.json','w').write(r.text);d=r.json();print(key,str(d)[:3000] if isinstance(d,list) else d.get('layers',[]))
