import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import requests
R=pathlib.Path('01_data/raw/pretraining_20261107')
urls={
'acs_dir':'https://www2.census.gov/programs-surveys/acs/summary_file/2021/',
'acs_tables':'https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/',
'acs_seq':'https://www2.census.gov/programs-surveys/acs/summary_file/2021/sequence-based-SF/data/5_year_seq_by_state/California/Tracts_Block_Groups_Only/',
'nav_report':'https://navigatela.lacity.org/reports/dot_hr_traffic_counts_report.cfm?pk=8469',
'nav_report_http':'http://navigatela.lacity.org/reports/dot_hr_traffic_counts_report.cfm?pk=8469',
'caltrans':'https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/CRS_Functional_Classification/FeatureServer/0?f=pjson'
}
for name,url in urls.items():
 try:
  r=requests.get(url,timeout=60);(R/(name+'.txt')).write_bytes(r.content);print(name,r.status_code,r.url,r.headers.get('Content-Type'),r.text[:80],flush=True)
 except Exception as e:print(name,type(e).__name__,str(e)[:150],flush=True)
