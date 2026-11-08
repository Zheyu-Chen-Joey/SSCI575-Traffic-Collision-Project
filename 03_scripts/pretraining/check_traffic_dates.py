import json,collections
r=json.load(open('01_data/raw/pretraining_20261107/traffic_summary.json'));dates=[x.get('count_date','') for x in r];print('dates',min(dates),max(dates),'years',dict(sorted(collections.Counter(d[:4] for d in dates).items())))
