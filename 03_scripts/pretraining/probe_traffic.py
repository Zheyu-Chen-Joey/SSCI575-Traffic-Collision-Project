import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import requests
R=pathlib.Path('01_data/raw/pretraining_20261107');s=requests.Session();s.get('https://navigatela.lacity.org/navigatela/',timeout=60)
r=s.get('https://navigatela.lacity.org/reports/dot_hr_traffic_counts_report.cfm?pk=8469',timeout=60);(R/'nav_report_session.html').write_bytes(r.content);print('NAV',r.status_code,r.url,len(r.content),flush=True)
u='https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/CRS_Functional_Classification/FeatureServer/0'
params={'f':'json','where':"County_label = 'Los Angeles'",'returnIdsOnly':'true'}
r=requests.get(u+'/query',params=params,timeout=90);(R/'caltrans_ids.json').write_bytes(r.content);print('CALTRANS',r.text[:250],flush=True)
r=requests.get('https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/traffic_aadt/MapServer/0',params={'f':'json'},timeout=60);(R/'aadt_metadata.json').write_bytes(r.content);print('AADT_FIELDS',[(f['name'],f.get('alias')) for f in r.json().get('fields',[])],flush=True)
