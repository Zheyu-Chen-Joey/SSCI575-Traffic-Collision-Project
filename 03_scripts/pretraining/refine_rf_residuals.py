"""Exploratory RF refinement: train-only CV, residual-autocorrelation objective, validation gate."""
import sys,pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.model_selection import GroupKFold,ParameterSampler
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from pipeline_definition import make_pipeline,feature_names
O=ROOT/'04_outputs/rf_residual_refinement_v2';M=ROOT/'05_models/rf_residual_refinement_v2';O.mkdir(exist_ok=True);M.mkdir(exist_ok=True)
assert not (O/'evaluation.json').exists(),'Completed run is immutable; create a new version for additional study.'
def write(v,name): (O/name).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if hasattr(x,'item')else str(x)),encoding='utf-8')
def metrics(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
def moran(res,xy,perm=0):
 z=np.asarray(res)-np.mean(res);n=len(z);k=min(8,n-1);ix=cKDTree(xy).query(xy,k=k+1)[1][:,1:];den=z@z;I=float((z[:,None]*z[ix]).sum()/k/den);result={'I':I,'n':n,'k':k}
 if perm:
  rng=np.random.default_rng(575);v=[]
  for _ in range(perm):
   q=rng.permutation(z);v.append(float((q[:,None]*q[ix]).sum()/k/den))
  result['p_two_sided']=float((1+sum(np.abs(np.array(v)+1/(n-1))>=abs(I+1/(n-1))))/(perm+1));result['permutations']=perm
 return result
src=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';df=pd.read_csv(src);e=df[df.eligible];tr=e[e.split=='train'].copy();va=e[e.split=='validation'].copy();dev=pd.concat([tr,va],ignore_index=True);cols=feature_names('enhanced');v1=json.loads((ROOT/'04_outputs/rf_project_v1/frozen_selection.json').read_text());anchor=v1['enhanced']['best_parameters'];candidates=[anchor]+list(ParameterSampler({'rf__n_estimators':[500,800],'rf__max_depth':[6,8,10,12,16,None],'rf__min_samples_leaf':[2,3,5,8,12],'rf__min_samples_split':[10],'rf__max_features':[.5,.7,1.0],'rf__criterion':['squared_error','poisson']},n_iter=24,random_state=20261107));folds=list(GroupKFold(5).split(tr,groups=tr.block_id))
def pipe(params):return make_pipeline('enhanced').set_params(rf__n_jobs=4,**params)
protocol={'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'exploratory follow-up after v1 test results were seen; NOT a fresh independent test','input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'features':cols,'test_for_selection':False,'same_algorithm_and_features':True,'candidates':candidates,'selection_rule':'Training5fold OOF RMSE <=1.02*anchor OOF RMSE, abs(pooled OOF Moran I) lower than anchor. Sort abs(I), then RMSE; validate at most3 candidates. Validation must have RMSE <= anchor and abs(Moran I) < anchor. Passing candidate with minimum abs(validation I) chosen; RMSE tie-break. Else retain v1. No legacy-test-driven selection.','moran_weights':'within-set directed row-standardized8NN, cell centers, same weights per comparison','OOF_limit':'pooled out-of-fold residuals come from five models; diagnostic tuning proxy, not independent validation','spatial_groups':'same fixed5km block_id; all five CV assessment folds train-only; no coordinates or target-derived spatial lag as feature'};write(protocol,'protocol.json');scores=[];foldrows=[];oofall=[]
for ci,params in enumerate(candidates):
 pred=np.zeros(len(tr))
 for fi,(a,b)in enumerate(folds):
  assert not(set(tr.iloc[a].block_id)&set(tr.iloc[b].block_id));fit=pipe(params);fit.fit(tr.iloc[a][cols],tr.iloc[a].count_2017_2021);p=fit.predict(tr.iloc[b][cols]);pred[b]=p;foldrows.append({'candidate':ci,'fold':fi,**metrics(tr.iloc[b].count_2017_2021.to_numpy(),p)})
 y=tr.count_2017_2021.to_numpy();r={'candidate':ci,**metrics(y,pred),'moran_i':moran(y-pred,tr[['cx','cy']])['I']};scores.append(r);oofall.append(pd.DataFrame({'candidate':ci,'grid_id':tr.grid_id,'observed':y,'predicted':pred,'residual':y-pred}));pd.DataFrame(scores).to_csv(O/'cv_candidate_scores.csv',index=False);print(ci,'RMSE',round(r['rmse'],3),'Moran',round(r['moran_i'],4),flush=True)
pd.concat(oofall,ignore_index=True).to_csv(O/'training_oof_predictions.csv',index=False);pd.DataFrame(foldrows).to_csv(O/'cv_fold_scores.csv',index=False);scores=pd.DataFrame(scores);a=scores.iloc[0];qual=scores[(scores.candidate!=0)&(scores.rmse<=1.02*a.rmse)&(scores.moran_i.abs()<abs(a.moran_i))].copy();qual['abs_moran']=qual.moran_i.abs();short=qual.sort_values(['abs_moran','rmse']).head(3).candidate.astype(int).tolist();valrows=[];valpreds=[]
for ci in [0]+short:
 fit=pipe(candidates[ci]);fit.fit(tr[cols],tr.count_2017_2021);p=fit.predict(va[cols]);y=va.count_2017_2021.to_numpy();r={'candidate':ci,**metrics(y,p),'moran_i':moran(y-p,va[['cx','cy']])['I']};valrows.append(r);valpreds.append(pd.DataFrame({'candidate':ci,'grid_id':va.grid_id,'observed':y,'predicted':p,'residual':y-p}));joblib.dump(fit,M/f'candidate_{ci}_trainonly.joblib')
vs=pd.DataFrame(valrows);vs.to_csv(O/'validation_scores.csv',index=False);pd.concat(valpreds,ignore_index=True).to_csv(O/'validation_predictions.csv',index=False);a=vs[vs.candidate==0].iloc[0];passed=vs[(vs.candidate!=0)&(vs.rmse<=a.rmse)&(vs.moran_i.abs()<abs(a.moran_i))].copy();passed['abs_moran']=passed.moran_i.abs();selected=int(passed.sort_values(['abs_moran','rmse']).iloc[0].candidate)if len(passed)else 0;decision={'selected_candidate':selected,'parameters':candidates[selected],'cv_shortlist':short,'development_joint_improvement':bool(selected!=0),'selection_frozen_before_legacy_test':True,'legacy_test_previously_seen':True,'reason':'Passed both development RMSE and residual-autocorrelation gates'if selected else'No shortlisted candidate improved both validation RMSE and residual autocorrelation; retain v1'};write(decision,'frozen_decision.json');print('FROZEN',decision,flush=True)
# No further optimization after freezing; legacy test is descriptive re-use only.
test=e[e.split=='test'];y=test.count_2017_2021.to_numpy();ev={};allrows=[]
for label,ci in [('v1_anchor',0),('v2_frozen',selected)]:
 fit=pipe(candidates[ci]);fit.fit(dev[cols],dev.count_2017_2021);p=fit.predict(test[cols]);ev[label]={'legacy_test':metrics(y,p),'moran':moran(y-p,test[['cx','cy']],9999),'candidate':ci};joblib.dump(fit,M/f'{label}_rf.joblib');out=df[['grid_id','split','eligible','count_2017_2021','cx','cy']].copy();out['model']=label;out['predicted']=fit.predict(df[cols]);out['residual']=out.count_2017_2021-out.predicted;out['prediction_role']=np.where(~out.eligible,'boundary_extrapolation_not_evaluated',np.where(out.split=='test','legacy_test_reuse','development_in_sample'));allrows.append(out)
ev['decision']=decision;ev['interpretation']='Exploratory legacy-test comparison; prior test performance influenced the decision to start follow-up. It cannot re-establish untouched-test generalization.';write(ev,'evaluation.json');pd.concat(allrows,ignore_index=True).to_csv(O/'all_predictions.csv',index=False);print('COMPLETE',json.dumps(ev),flush=True)
