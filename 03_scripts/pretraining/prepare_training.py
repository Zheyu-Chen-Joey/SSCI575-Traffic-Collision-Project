"""Prepare/check training inputs only. Intentionally provides no training command."""
import sys,pathlib,json,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd,numpy as np
from pipeline_definition import feature_names,make_pipeline

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true',help='Validate schema and pipelines; never fit');args=parser.parse_args()
 root=ROOT/'01_data/processed/pretraining_1km';df=pd.read_csv(root/'model_table_1000_final.csv');gate=json.loads((ROOT/'04_outputs/pretraining/readiness.json').read_text());out=ROOT/'05_models/pretraining';out.mkdir(exist_ok=True)
 assert df.grid_id.is_unique;assert df.count_2017_2021.sum()==230536;assert not(df.groupby('block_id').split.nunique()>1).any()
 eligible=df[df.eligible].copy();summaries={}
 for variant in ['baseline','enhanced']:
  cols=feature_names(variant);missing=set(cols)-set(df.columns);assert not missing,missing;pipeline=make_pipeline(variant)
  assert not hasattr(pipeline.named_steps['rf'],'estimators_'),'unexpected fitted model'
  assert not hasattr(pipeline.named_steps['preprocess'],'transformers_'),'unexpected fitted preprocessing'
  for split in ['train','validation','test']:
   subset=eligible[eligible.split==split];subset[['grid_id','block_id',*cols]].to_csv(out/f'{variant}_{split}_X.csv',index=False);subset[['grid_id','count_2017_2021']].to_csv(out/f'{variant}_{split}_y.csv',index=False)
  # Coverage checks inspect training covariates, not test performance or test target distribution.
  tr=eligible[eligible.split=='train'];summaries[variant]={'features':cols,'all_missing_train_features':[c for c in cols if tr[c].isna().all()],'train_rows':int((eligible.split=='train').sum()),'validation_rows':int((eligible.split=='validation').sum()),'test_rows':int((eligible.split=='test').sum()),'pipeline_fitted':False}
 report={'scope':'prepare_only','training_executed':False,'pipelines':summaries,'data_gate_status':gate['status'],'blocked_items':gate['blocking_items']};(out/'preparation_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return 0
if __name__=='__main__':sys.exit(main())
