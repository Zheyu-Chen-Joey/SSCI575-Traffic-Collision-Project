import json
for n in ['traffic_counts','signal_locations','landuse']:
 d=json.load(open('01_data/raw/'+n+'_metadata.json'));print(n,[(f['name'],f.get('alias')) for f in d['fields']])
