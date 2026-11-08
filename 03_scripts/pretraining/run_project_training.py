"""Predeclared training-only optimization followed by a frozen, one-pass test batch."""
import sys,pathlib,json,hashlib,datetime,time,os
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.model_selection import ParameterSampler,GroupKFold,GroupShuffleSplit
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from sklearn.inspection import permutation_importance
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from pipeline_definition import make_pipeline,feature_names
O=ROOT/'04_outputs/rf_project_v1';M=ROOT/'05_models/rf_project_v1';O.mkdir(exist_ok=True);M.mkdir(exist_ok=True)
def dump(v,p):p.write_text(json.dumps(v,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
def metric(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias_pred_minus_obs':float(np.mean(p-y))}
def moran(x,xy,k=8,perms=999,seed=575):
 n=len(x);k=min(k,n-1);_,ix=cKDTree(xy).query(xy,k=k+1);nn=ix[:,1:];z=np.asarray(x)-np.mean(x);den=z@z
 if den<1e-12:return {'I':None,'p_two_sided':None,'k':k}
 I=float(np.sum(z[:,None]*z[nn])/k/den);rng=np.random.default_rng(seed);v=[];expected=-1/(n-1)
 for _ in range(perms):
  q=rng.permutation(z);v.append(float(np.sum(q[:,None]*q[nn])/k/den))
 return {'I':I,'p_two_sided':float((1+sum(abs(np.array(v)-expected)>=abs(I-expected)))/(perms+1)),'k':k,'permutations':perms,'weights':'directed kNN row-standardized within evaluation cells; no cross-split neighbors','expected':expected}
def pipe(v,params=None,seed=42):
 p=make_pipeline(v).set_params(rf__n_jobs=4,rf__random_state=seed)
 return p.set_params(**(params or {}))
assert not (M/'evaluation.json').exists(),'Evaluation already completed; do not retune using final test.'
gate=json.loads((ROOT/'04_outputs/pretraining/readiness.json').read_text());assert not gate['blocking_items'];design=json.loads((ROOT/'02_config/feature_design.json').read_text());assert design['training_authorized'];df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');e=df[df.eligible].copy();tr=e[e.split=='train'].copy();va=e[e.split=='validation'].copy();test=e[e.split=='test'].copy();dev=pd.concat([tr,va],ignore_index=True)
for a,b in [(tr,va),(tr,test),(va,test)]:assert not(set(a.block_id)&set(b.block_id))
assert df.count_2017_2021.sum()==230536 and len(tr)==720 and len(va)==166 and len(test)==227
initial={'rf__n_estimators':300,'rf__max_depth':12,'rf__min_samples_split':10,'rf__min_samples_leaf':5,'rf__max_features':'sqrt','rf__criterion':'squared_error'}
space={'rf__n_estimators':[300,500],'rf__max_depth':[8,12,None],'rf__min_samples_split':[10],'rf__min_samples_leaf':[1,3,5,10],'rf__max_features':['sqrt',0.7,1.0],'rf__criterion':['squared_error','poisson']}
candidates=[initial]+list(ParameterSampler(space,n_iter=24,random_state=575));candidates=[dict(t) for t in {json.dumps(x,sort_keys=True):x for x in candidates}.values()];cv=list(GroupKFold(5).split(tr,groups=tr.block_id))
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_sha256':hashlib.sha256((ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv').read_bytes()).hexdigest(),'algorithm':'RandomForestRegressor only','working_scale_m':1000,'candidates':candidates,'selection':'minimum mean training spatial5fold RMSE; MAE tie-break; no test selection','initial_parameters':initial,'groups':'fixed5km block_id','folds':[{ 'fold':j,'train_grid_ids':tr.iloc[a].grid_id.tolist(),'valid_grid_ids':tr.iloc[b].grid_id.tolist()}for j,(a,b)in enumerate(cv)],'test_batch':['baseline_initial','baseline_optimized','enhanced_initial','enhanced_optimized','selected_model_2017_2020_sensitivity'],'test_policy':'Freeze both variants and preferred model before one batch; no retuning after test. Diagnostic importance is validation-only.','split_sensitivity':'development only, GroupShuffleSplit seeds101,202,303; additional1000m nearest-evaluation exclusion using seed101. No external test rows.','uncertainty':'paired test-block bootstrap2000; conditional on fixed split and trained models','limitations':gate['review_items']}
dump(protocol,O/'training_protocol.json');rows=[];selection={};train_models={};print('START',len(candidates),'candidates per variant',flush=True)
for variant in ['baseline','enhanced']:
 cols=feature_names(variant);assert not tr[cols].isna().all().any();assert not any(c.startswith('count') for c in cols)
 for ci,params in enumerate(candidates):
  start=time.time()
  for fi,(a,b) in enumerate(cv):
   fit=pipe(variant,params);fit.fit(tr.iloc[a][cols],tr.iloc[a].count_2017_2021);pred=fit.predict(tr.iloc[b][cols]);row={'variant':variant,'candidate':ci,'fold':fi,**metric(tr.iloc[b].count_2017_2021.to_numpy(),pred)};rows.append(row)
  pd.DataFrame(rows).to_csv(O/'cv_fold_scores.csv',index=False);s=pd.DataFrame(rows);r=s[(s.variant==variant)&(s.candidate==ci)]
  print(variant,ci,'RMSE',round(r.rmse.mean(),3),'seconds',round(time.time()-start,1),flush=True)
 scores=pd.DataFrame(rows);scores=scores[scores.variant==variant].groupby('candidate')[['rmse','mae','r2']].mean().reset_index().sort_values(['rmse','mae']);best=int(scores.iloc[0].candidate);selection[variant]={'best_candidate':best,'best_parameters':candidates[best],'initial_cv':scores[scores.candidate==0].iloc[0].to_dict(),'optimized_cv':scores.iloc[0].to_dict(),'features':cols}
 for stage,params in [('initial',initial),('optimized',candidates[best])]:
  fit=pipe(variant,params);fit.fit(tr[cols],tr.count_2017_2021);train_models[variant+'_'+stage]=fit;pr=fit.predict(va[cols]);selection[variant][stage+'_train']=metric(tr.count_2017_2021.to_numpy(),fit.predict(tr[cols]));selection[variant][stage+'_validation']=metric(va.count_2017_2021.to_numpy(),pr);joblib.dump(fit,M/f'{variant}_{stage}_trainonly.joblib');pd.DataFrame({'grid_id':va.grid_id,'observed':va.count_2017_2021,'predicted':pr,'residual':va.count_2017_2021-pr}).to_csv(O/f'{variant}_{stage}_validation_predictions.csv',index=False)
  if stage=='optimized':
   imp=permutation_importance(fit,va[cols],va.count_2017_2021,n_repeats=20,random_state=575,scoring='neg_root_mean_squared_error',n_jobs=1);pd.DataFrame({'feature':cols,'delta_rmse_mean':imp.importances_mean,'delta_rmse_std':imp.importances_std}).sort_values('delta_rmse_mean',ascending=False).to_csv(O/f'{variant}_validation_permutation_importance.csv',index=False)
 dump(selection,O/'development_selection.json')
preferred=min(selection,key=lambda v:selection[v]['optimized_validation']['rmse']);selection['preferred_variant_by_validation']=preferred;selection['test_not_yet_evaluated']=True;dump(selection,O/'frozen_selection.json');print('SELECTION FROZEN preferred',preferred,flush=True)
# Robustness on development rows only; selected parameters never changed by these checks.
sens=[]
for variant in ['baseline','enhanced']:
 cols=feature_names(variant);params=selection[variant]['best_parameters']
 for seed in [101,202,303]:
  a,b=next(GroupShuffleSplit(1,test_size=.2,random_state=seed).split(dev,groups=dev.block_id));fit=pipe(variant,params);fit.fit(dev.iloc[a][cols],dev.iloc[a].count_2017_2021);sens.append({'variant':variant,'check':'alternate_development_blocks','seed':seed,'n_train':len(a),'n_eval':len(b),**metric(dev.iloc[b].count_2017_2021.to_numpy(),fit.predict(dev.iloc[b][cols]))})
  if seed==101:
   dist,_=cKDTree(dev.iloc[b][['cx','cy']]).query(dev.iloc[a][['cx','cy']]);a=a[dist>1000];fit=pipe(variant,params);fit.fit(dev.iloc[a][cols],dev.iloc[a].count_2017_2021);sens.append({'variant':variant,'check':'1000m_center_separation','seed':seed,'n_train':len(a),'n_eval':len(b),**metric(dev.iloc[b].count_2017_2021.to_numpy(),fit.predict(dev.iloc[b][cols]))})
 # Random-seed stability on original train/validation, not selected by outcome.
 for seed in [7,99]:
  fit=pipe(variant,params,seed);fit.fit(tr[cols],tr.count_2017_2021);sens.append({'variant':variant,'check':'rf_seed_validation','seed':seed,'n_train':len(tr),'n_eval':len(va),**metric(va.count_2017_2021.to_numpy(),fit.predict(va[cols]))})
pd.DataFrame(sens).to_csv(O/'development_sensitivity.csv',index=False)
# Final test is now accessed in a single predeclared batch; no fitting to these targets.
evaluation={};prediction_rows=[];testpred={}
for variant in ['baseline','enhanced']:
 cols=feature_names(variant)
 for stage,params in [('initial',initial),('optimized',selection[variant]['best_parameters'])]:
  key=variant+'_'+stage;fit=pipe(variant,params);fit.fit(dev[cols],dev.count_2017_2021);joblib.dump(fit,M/f'{key}_rf.joblib');p=fit.predict(test[cols]);testpred[key]=p;res=test.count_2017_2021.to_numpy()-p;evaluation[key]={'test':metric(test.count_2017_2021.to_numpy(),p),'residual_moran':{str(k):moran(res,test[['cx','cy']].to_numpy(),k,9999)for k in [4,8,12]},'params':params,'development_train':metric(dev.count_2017_2021.to_numpy(),fit.predict(dev[cols]))};n=int(np.ceil(.1*len(test)));idx=np.argsort(p)[-n:];obsidx=np.argsort(test.count_2017_2021.to_numpy())[-n:];evaluation[key]['top10pct']={'cells':n,'overlap_fraction':len(set(idx)&set(obsidx))/n,'observed_burden_capture_fraction':float(test.iloc[idx].count_2017_2021.sum()/test.count_2017_2021.sum())}
  allpred=fit.predict(df[cols]);pr=df[['grid_id','split','eligible','count_2017_2021','cx','cy']].copy();pr['variant']=variant;pr['stage']=stage;pr['predicted']=allpred;pr['residual']=pr.count_2017_2021-pr.predicted;pr['prediction_role']=np.where(~pr.eligible,'boundary_extrapolation_not_evaluated',np.where(pr.split=='test','heldout_test','development_in_sample'));prediction_rows.append(pr)
# Historical reporting sensitivity using fixed chosen algorithm, parameters and spatial split.
cols=feature_names(preferred);params=selection[preferred]['best_parameters'];annual=[f'count_{y}'for y in range(2017,2021)];fit=pipe(preferred,params);fit.fit(dev[cols],dev[annual].sum(axis=1));py=fit.predict(test[cols]);yt=test[annual].sum(axis=1).to_numpy();evaluation['2017_2020_sensitivity']={'variant':preferred,'test':metric(yt,py),'target_total':int(df[annual].sum().sum()),'comparison':'different four-year count target; RMSE magnitudes not directly comparable to five-year target','residual_moran_knn8':moran(yt-py,test[['cx','cy']].to_numpy(),8,9999)};joblib.dump(fit,M/'selected_2017_2020_sensitivity_rf.joblib')
evaluation['training_mean_reference']=metric(test.count_2017_2021.to_numpy(),np.full(len(test),dev.count_2017_2021.mean()));evaluation['observed_target_moran_knn8']=moran(test.count_2017_2021.to_numpy(),test[['cx','cy']].to_numpy(),8,9999);evaluation['preferred_before_test']=preferred;evaluation['test_evaluation_batch_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();dump(evaluation,M/'evaluation.json');pd.concat(prediction_rows,ignore_index=True).to_csv(O/'all_predictions.csv',index=False)
# Paired spatial-block bootstrap uncertainty for fixed test models.
rng=np.random.default_rng(575);groups=test.block_id.unique();by={g:np.flatnonzero(test.block_id.to_numpy()==g)for g in groups};boot=[];y=test.count_2017_2021.to_numpy()
for _ in range(2000):
 ix=np.concatenate([by[g]for g in rng.choice(groups,len(groups),replace=True)]);a=metric(y[ix],testpred['baseline_optimized'][ix]);b=metric(y[ix],testpred['enhanced_optimized'][ix]);boot.append({**{f'baseline_{k}':a[k]for k in ['rmse','mae','r2']},**{f'enhanced_{k}':b[k]for k in ['rmse','mae','r2']},'enhanced_minus_baseline_rmse':b['rmse']-a['rmse'],'enhanced_minus_baseline_mae':b['mae']-a['mae'],'enhanced_minus_baseline_r2':b['r2']-a['r2']})
b=pd.DataFrame(boot);b.to_csv(O/'paired_block_bootstrap.csv',index=False);dump({c:{'lower_2.5':float(b[c].quantile(.025)),'upper_97.5':float(b[c].quantile(.975))}for c in b},O/'bootstrap_intervals.json')
dump({'status':'complete','trained':True,'test_used_for_tuning':False,'preferred_before_test':preferred,'models':[str(p.relative_to(ROOT))for p in M.glob('*.joblib')],'input_sha256':protocol['input_sha256'],'test_grid_ids':test.grid_id.tolist(),'seed':575,'python':sys.version,'source_code_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()},O/'run_receipt.json');print('COMPLETE',json.dumps({k:v['test']for k,v in evaluation.items()if isinstance(v,dict)and'test'in v}),flush=True)
