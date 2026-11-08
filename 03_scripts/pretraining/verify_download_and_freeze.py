import json,pathlib,hashlib,sys
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import pandas as pd
R=pathlib.Path('01_data/raw/pretraining_20261107');ids=json.load(open(R/'caltrans_ids.json'))['objectIds'];got=[]
for f in R.glob('functional_class_*.json'):
 d=json.loads(f.read_text());assert not d.get('exceededTransferLimit',False);got.extend(int(v['properties']['OBJECTID']) for v in d['features'])
assert len(got)==len(set(got))==len(ids) and set(got)==set(ids)
p=pathlib.Path('04_outputs/pretraining/verification.json');q=json.loads(p.read_text());q['checks'].append('functional_layer_all_requested_unique_ids_received');q['functional_object_count_verified']=len(got);p.write_text(json.dumps(q,indent=2))
model=pathlib.Path('01_data/processed/pretraining_1km/model_table_1000_final.csv');d=pd.read_csv(model);split=d[['grid_id','block_id','split','eligible']].to_csv(index=False).encode();pathlib.Path('05_models/pretraining/input_receipt.json').write_text(json.dumps({'model_table_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'partition_canonical_csv_sha256':hashlib.sha256(split).hexdigest(),'no_training_performed':True,'rows':len(d),'columns':len(d.columns)},indent=2));print('All115738 functional classification objects verified. Table',d.shape)
