"""Fixed matched coordinate ablation after development selection; never retunes."""
import sys,pathlib,json,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from rf_spatial_model import SpatialCoverageForest
from pipeline_definition import feature_names
O=ROOT/'04_outputs/rf_spatial_v5';M=ROOT/'05_models/rf_spatial_v5';dec=json.loads((O/'frozen_decision.json').read_text());s=dec['settings'];seeds=(7,42,99)if dec['seed_mode']=='ensemble'else(42,);df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');tr=df[df.eligible&(df.split=='train')];va=df[df.eligible&(df.split=='validation')];dev=pd.concat([tr,va],ignore_index=True);test=df[df.eligible&(df.split=='test')];cols=feature_names('enhanced')+['cx','cy'];ids=json.loads((O/'cv_fold_ids.json').read_text());metrics=[];allpred=[]
def met(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p))}
for position in [False,True]:
 settings={**s,'include_position':position};pred=np.zeros(len(tr));ordinary=np.zeros(len(tr))
 for fold in ids:
  b=tr.grid_id.isin(fold['eval_ids']).to_numpy();a=tr.grid_id.isin(fold['buffered_fit_ids']).to_numpy();m=SpatialCoverageForest(**settings,seeds=seeds);m.fit(tr.loc[a,cols],tr.loc[a,'count_2017_2021']);pred[b]=m.predict(tr.loc[b,cols])
 metrics.append({'position':position,'evaluation':'buffered_training_OOF',**met(tr.count_2017_2021.to_numpy(),pred)});allpred.append(pd.DataFrame({'position':position,'grid_id':tr.grid_id,'observed':tr.count_2017_2021,'predicted':pred}));m=SpatialCoverageForest(**settings,seeds=seeds);m.fit(tr[cols],tr.count_2017_2021);metrics.append({'position':position,'evaluation':'validation',**met(va.count_2017_2021.to_numpy(),m.predict(va[cols]))});joblib.dump(m,M/f'matched_position_{position}_trainonly.joblib');m.fit(dev[cols],dev.count_2017_2021);joblib.dump(m,M/f'matched_position_{position}_rf.joblib');p=m.predict(test[cols]);metrics.append({'position':position,'evaluation':'legacy_reuse',**met(test.count_2017_2021.to_numpy(),p)});print('matched position',position,'complete',flush=True)
pd.DataFrame(metrics).to_csv(O/'matched_coordinate_ablation.csv',index=False);pd.concat(allpred,ignore_index=True).to_csv(O/'matched_ablation_oof.csv',index=False);print(pd.DataFrame(metrics).to_string(index=False))
