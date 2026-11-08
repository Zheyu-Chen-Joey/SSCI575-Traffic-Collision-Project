"""Buffered development selection of local RFs; retain at most one production artifact."""
import sys,pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from rf_local_weighted_model import LocalWeightedSpatialForest
O=ROOT/'04_outputs/local_rf_study';O.mkdir(exist_ok=True);TEMP=ROOT/'06_reports/_qa/local_rf';TEMP.mkdir(parents=True,exist_ok=True);assert not(O/'evaluation.json').exists(),'Run already completed; never silently overwrite'
P=ROOT/'04_outputs/rf_spatial_v5';M=ROOT/'05_models/rf_spatial_v5';contract=json.loads((M/'input_contract.json').read_text());cols=contract['features'];src=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';df=pd.read_csv(src);tr=df[df.eligible&(df.split=='train')];va=df[df.eligible&(df.split=='validation')];dev=pd.concat([tr,va],ignore_index=True);best=json.loads((P/'frozen_decision.json').read_text());assert hashlib.sha256((M/'spatial_frozen_rf.joblib').read_bytes()).hexdigest()=='e0d0cb8433001ad548ff7d068d0d6d64d57f872d5edca4c26733ecd6f26bf6d8','Historical search needs previous spatial champion; use train_best_spatial_rf.py for current fixed-model reproduction';settings=best['settings'];seeds=(7,42,99);bands=[10000.,20000.,35000.];strengths=[.1,.25,.5,.75,1.];folds=json.loads((P/'cv_fold_ids.json').read_text());y=tr.count_2017_2021.to_numpy()
def dump(v,name):(O/name).write_text(json.dumps(v,indent=2,default=lambda x:x.item()if hasattr(x,'item')else str(x)),encoding='utf-8')
def met(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
def moran(r,xy):
 z=np.asarray(r)-np.mean(r);nn=cKDTree(xy).query(xy,k=9)[1][:,1:];return float((z[:,None]*z[nn]).sum()/8/(z@z))
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'reduce actual absolute count residuals; color scale fixed, no residual smoothing','input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'features':cols,'reference_model_sha256':hashlib.sha256((M/'spatial_frozen_rf.joblib').read_bytes()).hexdigest(),'settings':settings,'seeds':seeds,'bandwidth_m':bands,'local_strength':strengths,'anchor_spacing_m':20000,'local_tree_count':200,'min_kernel_effective_sample_size':40,'prediction':'fixedGaussian gating of3nearest occupied training-derived anchors; weightedRF labels only insidefit; no observed neighbor labels as inputs','selection':'Original train720 only; reuse recorded5fold IDs with actual square gap>1000m. Qualify mean bufferedRMSE<=anchor andMAE<=1.02anchor. Shortlist4 lowestRMSE. Validation166must improveRMSE andMAE; choose minimumRMSE thenMAE. Freeze before legacy reuse. Moran diagnostic, not direct color objective.','legacy_status':'previously seen region; candidate direction and promotion adaptive, no independent confirmation','promotion_policy':'only replace production champion if development gate passes and frozen candidate also has lower legacy RMSE andMAE; this acceptance reuses old evaluation, explicitly exploratory','one_model_retention':'candidate persisted only under privateQA until verified; nonwinning models not retained'};dump(protocol,'protocol.json');cvpred={0:np.zeros(len(tr))};candidate=[{'candidate':0,'bandwidth_m':None,'strength':0}];
for h in bands:
 for a in strengths:
  ci=len(candidate);candidate.append({'candidate':ci,'bandwidth_m':h,'strength':a});cvpred[ci]=np.zeros(len(tr))
foldrows=[];print('START localRF',len(candidate)-1,'candidate combinations',flush=True)
for fi,fold in enumerate(folds):
 a=tr.grid_id.isin(fold['buffered_fit_ids']).to_numpy();b=tr.grid_id.isin(fold['eval_ids']).to_numpy();assert not(set(tr.loc[a].block_id)&set(tr.loc[b].block_id));dx=np.maximum(np.abs(tr.loc[a].cx.to_numpy()[:,None]-tr.loc[b].cx.to_numpy()[None,:])-1000,0);dy=np.maximum(np.abs(tr.loc[a].cy.to_numpy()[:,None]-tr.loc[b].cy.to_numpy()[None,:])-1000,0);assert np.sqrt(dx*dx+dy*dy).min()>1000
 for hi,h in enumerate(bands):
  m=LocalWeightedSpatialForest(**settings,seeds=seeds,bandwidth_m=h);m.fit(tr.loc[a,cols],tr.loc[a,'count_2017_2021']);g,l=m.predict_components(tr.loc[b,cols])
  if hi==0:cvpred[0][b]=g;foldrows.append({'candidate':0,'fold':fi,**met(y[b],g)})
  for si,s in enumerate(strengths):
   ci=1+hi*len(strengths)+si;p=(1-s)*g+s*l;cvpred[ci][b]=p;foldrows.append({'candidate':ci,'fold':fi,**met(y[b],p)})
  print('FOLD',fi,'band',h,'anchors',len(m.local_forests_),flush=True)
scores=[]
for c in candidate:
 ci=c['candidate'];f=pd.DataFrame(foldrows);f=f[f.candidate==ci];p=cvpred[ci];scores.append({**c,**met(y,p),'mean_fold_rmse':float(f.rmse.mean()),'mean_fold_mae':float(f.mae.mean()),'moran_i':moran(y-p,tr[['cx','cy']])})
s=pd.DataFrame(scores);s.to_csv(O/'buffered_cv_scores.csv',index=False);pd.DataFrame(foldrows).to_csv(O/'buffered_fold_scores.csv',index=False);a=s.iloc[0];q=s[(s.candidate!=0)&(s.mean_fold_rmse<=a.mean_fold_rmse)&(s.mean_fold_mae<=1.02*a.mean_fold_mae)];short=q.sort_values(['mean_fold_rmse','mean_fold_mae']).head(4).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True);yv=va.count_2017_2021.to_numpy();val=[];cache={};valpred=[]
from rf_spatial_model import SpatialCoverageForest
anchor=SpatialCoverageForest(**settings,seeds=seeds);anchor.fit(tr[cols],tr.count_2017_2021);p0=anchor.predict(va[cols]);val.append({'candidate':0,**met(yv,p0),'moran_i':moran(yv-p0,va[['cx','cy']])});valpred.append(pd.DataFrame({'candidate':0,'grid_id':va.grid_id,'observed':yv,'predicted':p0}))
for ci in short:
 c=candidate[ci];h=c['bandwidth_m']
 if h not in cache:cache[h]=LocalWeightedSpatialForest(**settings,seeds=seeds,bandwidth_m=h).fit(tr[cols],tr.count_2017_2021)
 m=cache[h];m.local_strength=c['strength'];p=m.predict(va[cols]);val.append({'candidate':ci,**met(yv,p),'moran_i':moran(yv-p,va[['cx','cy']])});valpred.append(pd.DataFrame({'candidate':ci,'grid_id':va.grid_id,'observed':yv,'predicted':p}))
v=pd.DataFrame(val);v.to_csv(O/'validation_scores.csv',index=False);pd.concat(valpred,ignore_index=True).to_csv(O/'validation_predictions.csv',index=False);a=v.iloc[0];passing=v[(v.candidate!=0)&(v.rmse<a.rmse)&(v.mae<a.mae)];ci=int(passing.sort_values(['rmse','mae']).iloc[0].candidate)if len(passing)else 0;decision={'candidate':candidate[ci],'development_gate_pass':bool(ci),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'legacy_parameters_fitted':False};dump(decision,'frozen_decision.json');print('FROZEN',decision,flush=True)
old=joblib.load(M/'spatial_frozen_rf.joblib');test=df[df.eligible&(df.split=='test')];yt=test.count_2017_2021.to_numpy()
if ci:
 c=candidate[ci];model=LocalWeightedSpatialForest(**settings,seeds=seeds,bandwidth_m=c['bandwidth_m'],local_strength=c['strength']).fit(dev[cols],dev.count_2017_2021);joblib.dump(model,TEMP/'candidate.joblib')
else:model=old
pold=old.predict(test[cols]);pnew=model.predict(test[cols]);before=met(yt,pold);after=met(yt,pnew);promote=bool(ci and after['rmse']<before['rmse']and after['mae']<before['mae']);ev={'decision':decision,'original':before,'candidate':after,'original_moran':moran(yt-pold,test[['cx','cy']]),'candidate_moran':moran(yt-pnew,test[['cx','cy']]),'eligible_for_exploratory_promotion':promote,'legacy_reuse_not_independent':True,'candidate_private_path':'06_reports/_qa/local_rf/candidate.joblib'if ci else None};dump(ev,'evaluation.json');pd.DataFrame({'grid_id':test.grid_id,'observed':yt,'champion_prediction':pold,'candidate_prediction':pnew}).to_csv(O/'legacy_comparison.csv',index=False);print('COMPLETE',json.dumps(ev),flush=True)
