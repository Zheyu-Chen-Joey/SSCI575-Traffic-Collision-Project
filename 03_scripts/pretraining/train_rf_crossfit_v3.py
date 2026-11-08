"""V3 experiment; fixed protocol, no legacy evaluation target in tuning."""
import sys,pathlib,json,hashlib,datetime,itertools
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from pipeline_definition import make_pipeline,feature_names
from rf_residual_model import CrossFittedResidualForest
O=ROOT/'04_outputs/rf_crossfit_v3';M=ROOT/'05_models/rf_crossfit_v3';O.mkdir(exist_ok=True);M.mkdir(exist_ok=True);assert not(O/'evaluation.json').exists(),'Existing run cannot be overwritten'
def write(v,name):(O/name).write_text(json.dumps(v,indent=2,default=lambda x:x.item()if hasattr(x,'item')else str(x)),encoding='utf-8')
def metric(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
def moran(r,xy,perms=0):
 z=np.asarray(r)-np.mean(r);n=len(z);k=min(8,n-1);nn=cKDTree(xy).query(xy,k=k+1)[1][:,1:];den=z@z;I=float((z[:,None]*z[nn]).sum()/k/den);v={'I':I,'k':k}
 if perms:
  rng=np.random.default_rng(575);qv=[]
  for _ in range(perms):
   q=rng.permutation(z);qv.append((q[:,None]*q[nn]).sum()/k/den)
  v['p_two_sided']=float((1+np.sum(np.abs(np.asarray(qv)+1/(n-1))>=abs(I+1/(n-1))))/(perms+1));v['permutations']=perms
 return v
src=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';df=pd.read_csv(src);eligible=df[df.eligible];tr=eligible[eligible.split=='train'].copy();va=eligible[eligible.split=='validation'].copy();dev=pd.concat([tr,va],ignore_index=True);cols=feature_names('enhanced');base=json.loads((ROOT/'04_outputs/rf_project_v1/frozen_selection.json').read_text())['enhanced']['best_parameters'];settings=[{'rf__max_depth':d,'rf__min_samples_leaf':l,'rf__max_features':f}for d,l,f in itertools.product([3,5,8],[8,15,30],[.7,1.0])];strengths=[.25,.5,.75,1.0];candidates=[{'setting':None,'strength':0}]+[{'setting':i,'strength':w}for i in range(len(settings))for w in strengths];outer=list(GroupKFold(5).split(tr,groups=tr.block_id));n=len(tr);preds=np.zeros((len(candidates),n));tr_y=tr.count_2017_2021.to_numpy();fold_details=[]
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'RF base plus shrunk RF correction trained on inner spatial-out-of-fold residuals; both use identical16covariates','algorithm_change':'two-stage RF composition, not an additional ML algorithm; exploratory extension to original single-forest model','feature_names':cols,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'base_params':base,'correction_settings':settings,'strengths':strengths,'candidate_count':len(candidates),'outer_folds':5,'inner_folds':3,'selection_rule':'CV pooled RMSE<=anchor, MAE<=anchor,abs(Moran)<=anchor; rank RMSE/anchor +0.25*abs(I)/anchor. Validate at most4 shortlisted candidates. Validation must improve RMSE and not worsen MAE orabs(I); choose min validation RMSE, Moran tie-break. If no pass keep anchor. Freeze before legacy region comparison.','legacy_test':'previously examined in v1/v2; all later comparisons exploratory; no legacy rows for fit or selection','no_leakage':'outer evaluation targets excluded even from inner residual labels. No spatial lag, neighbor target, coordinates or HIN features. No smoothing or removal of difficult cells.'};write(protocol,'protocol.json');print('START',len(candidates),'RF correction candidates',flush=True)
for fi,(a,b)in enumerate(outer):
 X=tr.iloc[a][cols];y=tr_y[a];groups=tr.iloc[a].block_id.to_numpy();oof=np.zeros(len(a));inner_details=[]
 for ia,ib in GroupKFold(3).split(X,groups=groups):
  assert not(set(groups[ia])&set(groups[ib]));m=make_pipeline('enhanced').set_params(rf__n_jobs=4,**base);m.fit(X.iloc[ia],y[ia]);oof[ib]=m.predict(X.iloc[ib]);inner_details.append({'fit_ids':tr.iloc[a].iloc[ia].grid_id.tolist(),'oof_ids':tr.iloc[a].iloc[ib].grid_id.tolist()})
 m=make_pipeline('enhanced').set_params(rf__n_jobs=4,**base);m.fit(X,y);pbase=m.predict(tr.iloc[b][cols]);preds[0,b]=pbase
 for si,params in enumerate(settings):
  m=make_pipeline('enhanced').set_params(rf__n_jobs=4,rf__n_estimators=300,rf__criterion='squared_error',**params);m.fit(X,y-oof);cor=m.predict(tr.iloc[b][cols])
  for wi,w in enumerate(strengths):preds[1+si*4+wi,b]=np.maximum(0,pbase+w*cor)
 fold_details.append({'outer':fi,'fit_ids':tr.iloc[a].grid_id.tolist(),'evaluation_ids':tr.iloc[b].grid_id.tolist(),'inner':inner_details});print('OUTER FOLD',fi,'complete',flush=True)
write(fold_details,'nested_fold_ids.json');scores=[]
for ci,p in enumerate(preds):scores.append({'candidate':ci,**metric(tr_y,p),'moran_i':moran(tr_y-p,tr[['cx','cy']])['I']})
scores=pd.DataFrame(scores);scores.to_csv(O/'cv_scores.csv',index=False);pd.DataFrame(preds.T,index=tr.grid_id,columns=[str(i)for i in range(len(candidates))]).to_csv(O/'training_oof_predictions.csv');a=scores.iloc[0];qualified=scores[(scores.candidate!=0)&(scores.rmse<=a.rmse)&(scores.mae<=a.mae)&(scores.moran_i.abs()<=abs(a.moran_i))].copy();qualified['objective']=qualified.rmse/a.rmse+.25*qualified.moran_i.abs()/abs(a.moran_i);short=qualified.sort_values(['objective','rmse']).head(4).candidate.astype(int).tolist();print('CV shortlist',short,flush=True)
val=[];saved={};all_val=[];anchor=joblib.load(ROOT/'05_models/rf_project_v1/enhanced_optimized_trainonly.joblib');p0=anchor.predict(va[cols]);yv=va.count_2017_2021.to_numpy();val.append({'candidate':0,**metric(yv,p0),'moran_i':moran(yv-p0,va[['cx','cy']])['I']});all_val.append(pd.DataFrame({'candidate':0,'grid_id':va.grid_id,'observed':yv,'predicted':p0}));cached={}
for ci in short:
 c=candidates[ci];si=c['setting']
 if si not in cached:cached[si]=CrossFittedResidualForest(base,settings[si],c['strength'],inner_splits=3).fit(tr[cols],tr_y,tr.block_id)
 fit=cached[si];fit.strength=c['strength'];p=fit.predict(va[cols]);val.append({'candidate':ci,**metric(yv,p),'moran_i':moran(yv-p,va[['cx','cy']])['I']});all_val.append(pd.DataFrame({'candidate':ci,'grid_id':va.grid_id,'observed':yv,'predicted':p}));joblib.dump(fit,M/f'candidate_{ci}_trainonly.joblib')
v=pd.DataFrame(val);v.to_csv(O/'validation_scores.csv',index=False);pd.concat(all_val,ignore_index=True).to_csv(O/'validation_predictions.csv',index=False);a=v.iloc[0];passed=v[(v.candidate!=0)&(v.rmse<a.rmse)&(v.mae<=a.mae)&(v.moran_i.abs()<=abs(a.moran_i))].copy();best=int(passed.sort_values(['rmse','moran_i']).iloc[0].candidate)if len(passed)else 0;decision={'selected_candidate':best,'candidate_spec':candidates[best],'correction_params':settings[candidates[best]['setting']]if best else None,'passes_joint_development_gate':bool(best),'original_model_retained_if_zero':best==0,'reason':'Nested CV and development-validation joint gate; no legacy target used','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};write(decision,'frozen_decision.json');print('FROZEN',decision,flush=True)
# Final descriptive evaluation of frozen choice only; old model evaluated exactly as saved.
test=eligible[eligible.split=='test'];yt=test.count_2017_2021.to_numpy();old=joblib.load(ROOT/'05_models/rf_project_v1/enhanced_optimized_rf.joblib')
if best:
 c=candidates[best];fit=CrossFittedResidualForest(base,settings[c['setting']],c['strength'],inner_splits=5).fit(dev[cols],dev.count_2017_2021.to_numpy(),dev.block_id)
else:fit=old
joblib.dump(fit,M/'v3_frozen_rf.joblib');ev={'decision':decision,'exploratory_legacy_reuse':True};allout=[]
for key,model in [('v1',old),('v3',fit)]:
 p=model.predict(test[cols]);ev[key]={'legacy_evaluation':metric(yt,p),'moran':moran(yt-p,test[['cx','cy']],9999)};out=df[['grid_id','split','eligible','count_2017_2021','cx','cy']].copy();out['model']=key;out['predicted']=model.predict(df[cols]);out['residual']=out.count_2017_2021-out.predicted;out['prediction_role']=np.where(~out.eligible,'boundary_extrapolation',np.where(out.split=='test','legacy_evaluation_reuse','development_fit'));allout.append(out)
write(ev,'evaluation.json');pd.concat(allout,ignore_index=True).to_csv(O/'all_predictions.csv',index=False);print('COMPLETE',json.dumps(ev),flush=True)
