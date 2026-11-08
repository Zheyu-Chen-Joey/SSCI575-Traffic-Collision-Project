"""Reproduce the frozen selected spatial RF only; no parameter search or test-based tuning."""
import sys,pathlib,json,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-training',action='store_true');ap.add_argument('--output');a=ap.parse_args()
 if not a.execute_training:print('No training. To reproduce the frozen model, supply --execute-training --output NEW_MODEL.joblib');return
 if not a.output:raise ValueError('A new output path is required')
 out=pathlib.Path(a.output)
 if out.exists():raise FileExistsError('Existing model is never overwritten')
 import hashlib,pandas as pd,joblib
 from rf_spatial_model import SpatialCoverageForest
 M=ROOT/'05_models/rf_spatial_v5';O=ROOT/'04_outputs/rf_spatial_v5';contract=json.loads((M/'input_contract.json').read_text());decision=json.loads((O/'frozen_decision.json').read_text());protocol=json.loads((O/'protocol.json').read_text());src=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';assert hashlib.sha256(src.read_bytes()).hexdigest()==protocol['input_sha256'];df=pd.read_csv(src);tr=df[df.eligible&(df.split=='train')];va=df[df.eligible&(df.split=='validation')];dev=pd.concat([tr,va],ignore_index=True);assert len(dev)==886 and not(set(dev.block_id)&set(df.loc[df.split=='test','block_id']));seedlist=(7,42,99)if decision['seed_mode']=='ensemble'else(42,);model=SpatialCoverageForest(**decision['settings'],seeds=seedlist);model.fit(dev[contract['features']],dev.count_2017_2021);joblib.dump(model,out);print('Reproduced frozen settings on886development rows; no test evaluation or optimization performed',out)
if __name__=='__main__':main()
