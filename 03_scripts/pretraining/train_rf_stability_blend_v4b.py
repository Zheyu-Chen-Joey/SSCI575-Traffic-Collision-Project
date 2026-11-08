"""Conservative RF ensemble, with at least half weight on the original model."""
import sys,pathlib,json,datetime,hashlib,itertools
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from scipy.spatial import cKDTree
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from pipeline_definition import feature_names
from rf_fixed_blend import FixedForestBlend
from rf_coverage_scaled_model import CoverageScaledForest
O=ROOT/'04_outputs/rf_stability_blend_v4b';M=ROOT/'05_models/rf_stability_blend_v4b';O.mkdir(exist_ok=True);M.mkdir(exist_ok=True);assert not(O/'evaluation.json').exists()
def write(v,n):(O/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item()if hasattr(x,'item')else str(x)),encoding='utf-8')
def met(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
def moran(r,xy):
 z=np.asarray(r)-np.mean(r);nn=cKDTree(xy).query(xy,k=9)[1][:,1:];return float((z[:,None]*z[nn]).sum()/8/(z@z))
df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');tr=df[df.eligible&(df.split=='train')];va=df[df.eligible&(df.split=='validation')];t=df[df.eligible&(df.split=='test')];cols=feature_names('enhanced');cv4=pd.read_csv(ROOT/'04_outputs/rf_coverage_v4/training_oof_predictions.csv');cv2=pd.read_csv(ROOT/'04_outputs/rf_residual_refinement_v2/training_oof_predictions.csv');preds=[]
for frame,ci in [(cv4,0),(cv2,2),(cv4,30)]:
 sub=frame[frame.candidate==ci];joined=tr[['grid_id','count_2017_2021']].merge(sub[['grid_id','observed','predicted']],on='grid_id',validate='one_to_one');assert np.array_equal(joined.count_2017_2021,joined.observed);preds.append(joined.predicted.to_numpy())
weights=[(1,0,0)]+[(a,b,1-a-b)for a in [.5,.75]for b in [0,.25,.5]if a+b<=1];weights=list(dict.fromkeys(weights));write({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Conservative RF-only blend after negative-transfer experiments, exploratory','prior_results_seen':True,'test_for_weight_fitting':False,'members':['v1','v2candidate2','v4candidate30'],'candidate_weights':weights,'v1_minimum_weight':.5,'reason':'Preserve at least half of pre-existing reference, limit correction magnitude and variance; weights not optimized on legacy errors','selection':'Cached train-only5fold OOF RMSE and MAE <= anchor and absMoran<=anchor; shortlist3 smallestRMSE. Validation jointly improvesRMSE/MAE/absMoran. MinRMSE among passing; freeze before legacy region reuse.','limitations':'OOF from previously selected configurations and validation reused; development diagnostics, not unbiased confirmation'},'protocol.json');scores=[];y=tr.count_2017_2021.to_numpy()
for ci,w in enumerate(weights):
 p=sum(wi*pi for wi,pi in zip(w,preds));scores.append({'candidate':ci,**met(y,p),'moran_i':moran(y-p,tr[['cx','cy']]),'weights':w})
s=pd.DataFrame(scores);s.to_csv(O/'cv_scores.csv',index=False);a=s.iloc[0];q=s[(s.candidate!=0)&(s.rmse<=a.rmse)&(s.mae<=a.mae)&(s.moran_i.abs()<=abs(a.moran_i))];short=q.sort_values('rmse').head(3).candidate.astype(int).tolist();trainfiles=[ROOT/'05_models/rf_project_v1/enhanced_optimized_trainonly.joblib',ROOT/'05_models/rf_residual_refinement_v2/candidate_2_trainonly.joblib',ROOT/'05_models/rf_coverage_v4/30_single_trainonly.joblib'];members=[joblib.load(f)for f in trainfiles];yv=va.count_2017_2021.to_numpy();val=[]
for ci in [0]+short:
 model=FixedForestBlend(members,weights[ci],cols);p=model.predict(va[cols]);val.append({'candidate':ci,**met(yv,p),'moran_i':moran(yv-p,va[['cx','cy']])})
v=pd.DataFrame(val);v.to_csv(O/'validation_scores.csv',index=False);a=v.iloc[0];passing=v[(v.candidate!=0)&(v.rmse<a.rmse)&(v.mae<=a.mae)&(v.moran_i.abs()<=abs(a.moran_i))];ci=int(passing.sort_values('rmse').iloc[0].candidate)if len(passing)else 0;dec={'selected_candidate':ci,'weights':weights[ci],'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'development_gate_pass':ci!=0};write(dec,'frozen_decision.json');print('FROZEN',dec,flush=True)
files=[ROOT/'05_models/rf_project_v1/enhanced_optimized_rf.joblib',ROOT/'05_models/rf_residual_refinement_v2/v2_frozen_rf.joblib',ROOT/'05_models/rf_coverage_v4/v4_frozen_rf.joblib'];members=[joblib.load(f)for f in files];model=FixedForestBlend(members,weights[ci],cols);joblib.dump(model,M/'blend_frozen.joblib');out=[];ev={'decision':dec,'legacy_reuse_exploratory':True};yt=t.count_2017_2021.to_numpy()
for key,m in [('v1',members[0]),('blend',model)]:
 p=m.predict(t[cols]);ev[key]={'legacy_evaluation':met(yt,p),'moran_i':moran(yt-p,t[['cx','cy']])};z=df[['grid_id','split','eligible','count_2017_2021','cx','cy']].copy();z['model']=key;z['predicted']=m.predict(df[cols]);z['residual']=z.count_2017_2021-z.predicted;out.append(z)
write(ev,'evaluation.json');pd.concat(out,ignore_index=True).to_csv(O/'all_predictions.csv',index=False);print(json.dumps(ev),flush=True)
