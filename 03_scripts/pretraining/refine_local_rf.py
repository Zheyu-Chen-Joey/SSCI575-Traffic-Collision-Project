"""Refine local RF with buffered CV plus a fixed geographic-stability gate."""
import sys,pathlib,json,hashlib,datetime,itertools
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.model_selection import ParameterSampler
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from rf_spatial_model import SpatialCoverageForest
from rf_local_weighted_model import LocalWeightedSpatialForest
from rf_refined_local_model import RefinedLocalSpatialForest
P=ROOT/'04_outputs/rf_spatial_v5';M=ROOT/'05_models/rf_spatial_v5';O=ROOT/'06_reports/_qa/refined_local';O.mkdir(parents=True,exist_ok=True);assert not(O/'evaluation.json').exists();D=json.loads((P/'frozen_decision.json').read_text());cols=json.loads((M/'input_contract.json').read_text())['features'];base=D['settings'];seeds=(7,42,99);df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');tr=df[df.eligible&(df.split=='train')];va=df[df.eligible&(df.split=='validation')];dev=pd.concat([tr,va],ignore_index=True);folds=json.loads((P/'cv_fold_ids.json').read_text());champion=joblib.load(M/'spatial_frozen_rf.joblib');assert isinstance(champion,LocalWeightedSpatialForest)
def dump(v,n):(O/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item()if hasattr(x,'item')else str(x)),encoding='utf-8')
def met(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y)),'p90_abs_error':float(np.quantile(abs(y-p),.9))}
def moran(r,xy):
 z=np.asarray(r)-np.mean(r);nn=cKDTree(xy).query(xy,k=9)[1][:,1:];return float((z[:,None]*z[nn]).sum()/8/(z@z))
def keep_gap(a,b):
 dx=np.maximum(abs(a.cx.to_numpy()[:,None]-b.cx.to_numpy()[None,:])-1000,0);dy=np.maximum(abs(a.cy.to_numpy()[:,None]-b.cy.to_numpy()[None,:])-1000,0);return np.sqrt(dx*dx+dy*dy).min(axis=1)>1000
settings=[]
for h,spacing in [(5000,10000),(7500,10000),(10000,10000),(7500,15000),(10000,15000),(10000,20000)]:settings.append({'bandwidth_m':h,'anchor_spacing_m':spacing,'local_leaf':5,'local_depth':16,'local_features':.5,'support_attenuation':True})
for s in ParameterSampler({'bandwidth_m':[5000,7500,10000,15000],'anchor_spacing_m':[10000,15000,20000],'local_leaf':[3,5,8],'local_depth':[12,16,None],'local_features':[.5,.8,1.0],'support_attenuation':[True,False]},n_iter=6,random_state=708):
 if s not in settings:settings.append(s)
strengths=[.5,.75,1.0];candidates=[{'candidate':0,'setting':None,'strength':.75}]+[{'candidate':1+i*len(strengths)+j,'setting':i,'strength':w}for i in range(len(settings))for j,w in enumerate(strengths)];protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':hashlib.sha256((M/'spatial_frozen_rf.joblib').read_bytes()).hexdigest(),'input_sha256':hashlib.sha256((ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv').read_bytes()).hexdigest(),'global_settings':base,'settings':settings,'strengths':strengths,'selection':'5fold recorded1km-square-gap CV on train720. Qualify meanRMSE<=1.005champion,MAE<=1.02champion; shortlist4 lowestRMSE. Validation must lowerRMSE andMAE; choose minRMSE. Frozen winner must have mean normalized north/east dev-holdout RMSE andMAE<=1.01champion before legacy evaluation.','support':'attenuate local effect only beyond nearest training center5km, Gaussian decay5km; uses coordinates only, no observed neighbor outcome as prediction input','legacy_promotion':'exploratory reused region; frozen candidate must lowerRMSE andMAE and not worsen p90abs error by>2pct to replace champion','model_retention':'only champion production artifact retained; candidates temporary','no_plot_manipulation':'same legacy and full-city residual bounds; no labels removed, no residual smoothing'};dump(protocol,'protocol.json');pred={c['candidate']:np.zeros(len(tr))for c in candidates};y=tr.count_2017_2021.to_numpy();foldrows=[];print('START',len(candidates),'candidate combinations',flush=True)
for fi,fold in enumerate(folds):
 a=tr.grid_id.isin(fold['buffered_fit_ids']).to_numpy();b=tr.grid_id.isin(fold['eval_ids']).to_numpy();assert keep_gap(tr.loc[a],tr.loc[b]).all();glob=SpatialCoverageForest(**base,seeds=seeds).fit(tr.loc[a,cols],tr.loc[a,'count_2017_2021']);anchor=RefinedLocalSpatialForest(**base,seeds=seeds).fit_with_global(tr.loc[a,cols],tr.loc[a,'count_2017_2021'],glob);pc=anchor.predict(tr.loc[b,cols]);pred[0][b]=pc;foldrows.append({'candidate':0,'fold':fi,**met(y[b],pc)})
 for si,s in enumerate(settings):
  m=RefinedLocalSpatialForest(**base,seeds=seeds,**s).fit_with_global(tr.loc[a,cols],tr.loc[a,'count_2017_2021'],glob);g,l=m.predict_components(tr.loc[b,cols]);support=m.support_factor(tr.loc[b,cols])
  for wi,w in enumerate(strengths):
   ci=1+si*len(strengths)+wi;pp=g+w*support*(l-g);pred[ci][b]=pp;foldrows.append({'candidate':ci,'fold':fi,**met(y[b],pp)})
  print('CV',fi,'setting',si,'anchors',len(m.local_forests_),flush=True)
scores=[]
for c in candidates:
 ci=c['candidate'];pp=pred[ci];f=pd.DataFrame(foldrows);f=f[f.candidate==ci];scores.append({**c,**met(y,pp),'mean_fold_rmse':float(f.rmse.mean()),'mean_fold_mae':float(f.mae.mean()),'moran_i':moran(y-pp,tr[['cx','cy']])})
s=pd.DataFrame(scores);s.to_csv(O/'cv_scores.csv',index=False);pd.DataFrame(foldrows).to_csv(O/'cv_fold_scores.csv',index=False);a=s.iloc[0];q=s[(s.candidate!=0)&(s.mean_fold_rmse<=a.mean_fold_rmse*1.005)&(s.mean_fold_mae<=a.mean_fold_mae*1.02)];short=q.sort_values(['mean_fold_rmse','mean_fold_mae']).head(4).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True);glob=SpatialCoverageForest(**base,seeds=seeds).fit(tr[cols],tr.count_2017_2021);anchor=RefinedLocalSpatialForest(**base,seeds=seeds).fit_with_global(tr[cols],tr.count_2017_2021,glob);yv=va.count_2017_2021.to_numpy();p=anchor.predict(va[cols]);validation=[{'candidate':0,**met(yv,p),'moran_i':moran(yv-p,va[['cx','cy']])}];cache={}
for ci in short:
 c=candidates[ci];si=c['setting']
 if si not in cache:cache[si]=RefinedLocalSpatialForest(**base,seeds=seeds,**settings[si]).fit_with_global(tr[cols],tr.count_2017_2021,glob)
 m=cache[si];m.local_strength=c['strength'];p=m.predict(va[cols]);validation.append({'candidate':ci,**met(yv,p),'moran_i':moran(yv-p,va[['cx','cy']])})
v=pd.DataFrame(validation);v.to_csv(O/'validation_scores.csv',index=False);a=v.iloc[0];passing=v[(v.candidate!=0)&(v.rmse<a.rmse)&(v.mae<a.mae)];ci=int(passing.sort_values(['rmse','mae']).iloc[0].candidate)if len(passing)else 0;c=candidates[ci];selectedsettings=settings[c['setting']]if ci else{};decision={'candidate':c,'settings':selectedsettings,'development_validation_pass':bool(ci),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};dump(decision,'frozen_decision.json');print('FROZEN',decision,flush=True)
# Fixed development-region stability gate; no legacy targets used here.
geo=[]
if ci:
 for region,col in [('north20pct','cy'),('east20pct','cx')]:
  cutoff=dev[col].quantile(.8);b=np.flatnonzero(dev[col].to_numpy()>=cutoff);a=np.flatnonzero(dev[col].to_numpy()<cutoff);a=a[keep_gap(dev.iloc[a],dev.iloc[b])];glob=SpatialCoverageForest(**base,seeds=seeds).fit(dev.iloc[a][cols],dev.iloc[a].count_2017_2021)
  for name,kw,strength in [('champion',{},.75),('candidate',selectedsettings,c['strength'])]:
   m=RefinedLocalSpatialForest(**base,seeds=seeds,local_strength=strength,**kw).fit_with_global(dev.iloc[a][cols],dev.iloc[a].count_2017_2021,glob);pp=m.predict(dev.iloc[b][cols]);geo.append({'region':region,'model':name,'n_fit':len(a),'n_eval':len(b),**met(dev.iloc[b].count_2017_2021.to_numpy(),pp)})
 geodf=pd.DataFrame(geo);geodf.to_csv(O/'geographic_gate.csv',index=False);oldg=geodf[geodf.model=='champion'].set_index('region');newg=geodf[geodf.model=='candidate'].set_index('region');gate=float((newg.rmse/oldg.rmse).mean())<=1.01 and float((newg.mae/oldg.mae).mean())<=1.01
else:gate=False
result={'decision':decision,'geographic_gate_pass':bool(gate),'promote':False,'legacy_reuse_exploratory':True}
if ci and gate:
 m=RefinedLocalSpatialForest(**base,seeds=seeds,local_strength=c['strength'],**selectedsettings).fit(dev[cols],dev.count_2017_2021);assert np.allclose(RefinedLocalSpatialForest(**base,seeds=seeds).fit(dev[cols],dev.count_2017_2021).predict(dev[cols]),champion.predict(dev[cols]));t=df[df.eligible&(df.split=='test')];yt=t.count_2017_2021.to_numpy();p0=champion.predict(t[cols]);p1=m.predict(t[cols]);old=met(yt,p0);new=met(yt,p1);result.update({'champion':old,'candidate_metrics':new,'champion_moran':moran(yt-p0,t[['cx','cy']]),'candidate_moran':moran(yt-p1,t[['cx','cy']]),'promote':new['rmse']<old['rmse']and new['mae']<old['mae']and new['p90_abs_error']<=1.02*old['p90_abs_error']});joblib.dump(m,O/'candidate.joblib');pd.DataFrame({'grid_id':t.grid_id,'observed':yt,'before':p0,'after':p1}).to_csv(O/'legacy_comparison.csv',index=False)
dump(result,'evaluation.json');print('COMPLETE',json.dumps(result),flush=True)
