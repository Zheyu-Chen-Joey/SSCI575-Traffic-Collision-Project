import urllib.request,json
urls={ 'collision':'https://data.lacity.org/api/views/d5tf-ez2w.json', 'boundary':'https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer?f=pjson','signals':'https://services1.arcgis.com/tp9wqSVX1AitKgjd/arcgis/rest/services/Vision_Zero__Improvements/FeatureServer/2?f=pjson'}
for k,u in urls.items():
 try:
  d=json.load(urllib.request.urlopen(u,timeout=90)); open('01_data/raw/'+k+'_metadata.json','w').write(json.dumps(d)); print(k, str(d)[:100] if k=='signals' else [(x.get('fieldName',x.get('id')),x.get('name')) for x in d.get('columns',d.get('layers',[]))])
 except Exception as e: print(k,e)
