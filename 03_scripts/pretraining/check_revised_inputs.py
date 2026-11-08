import json,pathlib,csv
R=pathlib.Path.cwd();p=R/'05_models/pretraining/input_receipt.json';d=json.loads(p.read_text());import hashlib
for name,path in [('feature_design','02_config/feature_design.json'),('pipeline_definition','03_scripts/pretraining/pipeline_definition.py')]:d[name+'_sha256']=hashlib.sha256((R/path).read_bytes()).hexdigest()
p.write_text(json.dumps(d,indent=2))
for variant in ['baseline','enhanced']:
 for split in ['train','validation','test']:
  p=R/f'05_models/pretraining/{variant}_{split}_X.csv';cols=next(csv.reader(p.open()));assert not any('traffic' in c.lower() for c in cols);print(variant,split,'feature_count',len(cols)-2)
r=json.loads((R/'04_outputs/pretraining/readiness.json').read_text());assert not r['blocking_items'];assert r['training_executed'] is False
assert not list((R/'05_models').rglob('*.joblib'));print('PASS: revised inputs ready; no fitted model files')
