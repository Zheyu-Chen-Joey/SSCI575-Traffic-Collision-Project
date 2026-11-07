import sys,json
sys.path.insert(0,'.runtime')
import requests
for id in ['d5tf-ez2w','s2yz-yg2p']:
 r=requests.get('https://data.lacity.org/resource/'+id+'.json',params={'$select':'date_extract_y(date_occ) as year,count(*) as n','$where':"date_occ between '2017-01-01T00:00:00' and '2022-01-01T00:00:00'",'$group':'year','$order':'year'},timeout=90);print(id,r.status_code,r.text[:2500])
for name,url in [('signals','https://services1.arcgis.com/tp9wqSVX1AitKgjd/arcgis/rest/services/Vision_Zero__Improvements/FeatureServer/2/query'),('landuse','https://maps.lacity.org/lahub/rest/services')]:
 r=requests.get(url,params={'f':'json','where':'1=1','outFields':'*','outSR':4326,'returnIdsOnly':'true'},timeout=90);open('01_data/raw/'+name+'_probe.json','w').write(r.text);print(name,r.text[:2000])
