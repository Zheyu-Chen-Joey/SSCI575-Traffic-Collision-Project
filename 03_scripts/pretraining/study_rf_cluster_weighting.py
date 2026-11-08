"""Nested training-only hard-cell and residual-cluster RF weighting study."""
import sys, pathlib, json, hashlib, datetime, copy, argparse
R=pathlib.Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'.runtime'),str(R/'03_scripts/pretraining')]
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from rf_local_weighted_model import LocalWeightedSpatialForest
from rf_rotated_local_model import RotatedLocalSpatialForest
from rf_coordinate_blend_model import CoordinateBlendForest
from rf_orientation_ensemble import OrientationEnsembleForest
from rf_cluster_weighted_model import ClusterWeightedOrientationForest,training_residual_diagnostics
from scipy.spatial import cKDTree

P=R/'04_outputs/rf_spatial_v5'; O=R/'06_reports/_qa/cluster_weighting_v8_run2'; O.mkdir(exist_ok=True,parents=True)
assert not (O/'protocol.json').exists(), 'Use a new audit directory for another run'
src=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv'
df=pd.read_csv(src); tr=df[df.eligible&(df.split=='train')].reset_index(drop=True); va=df[df.eligible&(df.split=='validation')].reset_index(drop=True); dev=pd.concat([tr,va],ignore_index=True)
decision=json.loads((P/'frozen_decision.json').read_text()); contract=json.loads((R/'05_models/rf_spatial_v5/input_contract.json').read_text()); cols=contract['features']; folds=json.loads((P/'cv_fold_ids.json').read_text())
modelpath=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib'
assert hashlib.sha256(modelpath.read_bytes()).hexdigest()=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357', 'Study requires frozen v8 champion'

def dump(v,n): (O/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def metrics(y,p):
 y=np.asarray(y); return dict(rmse=float(np.sqrt(mean_squared_error(y,p))),mae=float(mean_absolute_error(y,p)),r2=float(r2_score(y,p)),bias=float(np.mean(p-y)),p90_abs_error=float(np.quantile(abs(y-p),.9)),error_gt200_count=int((abs(y-p)>200).sum()))
def gap(a,b):
 dx=np.maximum(abs(a.cx.to_numpy()[:,None]-b.cx.to_numpy()[None,:])-1000,0);dy=np.maximum(abs(a.cy.to_numpy()[:,None]-b.cy.to_numpy()[None,:])-1000,0);return np.sqrt(dx*dx+dy*dy).min(axis=1)>1000
base={**decision['settings'],**decision['local_weighting_settings'],**decision['orientation_settings']}; configs=[{'name':'champion','params':copy.deepcopy(base)}]
changes=[('cluster025',.25,True),('cluster050',.5,True),('cluster100',1.,True),('hard050',.5,False)]
for name,strength,cluster in changes:
 p=copy.deepcopy(base);p.update(error_weight_strength=strength,cluster_emphasis=cluster);configs.append({'name':name,'params':p})
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':hashlib.sha256(modelpath.read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'seeds':[7,42,99],'configs':configs,'selection':'Train720 fixed5fold with1km-square-gap. Weight estimation NESTED inside each fit subset:3fold GroupKFold, same1km-gap, lightweight RF seed42 global200/local100. No outer eval labels used. Require CV meanRMSE+MAE lower, pooledp90 andnumberabsError>200 no worse, absoluteMoranI no worse. Shortlist3 byRMSE. Validation166 requiresRMSE+MAE lower,p90<=1.02ref,numberabsError>200 andabsMoran no worse. Freeze before geography.','geographic_gate':'North/east20pct of886development rows; >1km-square gap. Require each region RMSE andMAE ratio<=1.05 and meanratio<=1.01 for bothmetrics. These are reused development diagnostics, not independent tests.','legacy_gate':'Only aftergeography, fit886; once exploratory reused227 comparison. RequireRMSE+MAE lower,p90<=1.02ref,numberabsError>200 andabsoluteMoranI no worse. Not independent validation.','weight_method':'w=min(1+strength*hard_score*(.5+.5*same_sign_neighbor_fraction),3), normalized mean1; hardscore=clip(absinnerOOFresidual/q90,0,2); same-sign fraction within1500m amongtrainingOOF residuals, >=2neighbors. Hard-only variant omits cluster multiplier. Weight construction never used at inference.','features':'Same18 columns; no neighboring target inputs; no raw modifications; model type remains RF','retention':'One production champion, no unsuccessful candidate model files'}
dump(protocol,'protocol.json'); results=[]; predictions={i:np.full(len(tr),np.nan)for i in range(len(configs))}
weightcache={}
def moran(y,p,xy):
 z=np.asarray(y)-np.asarray(p);z=z-z.mean();ix=cKDTree(np.asarray(xy)).query(np.asarray(xy),k=9)[1][:,1:];return float((z[:,None]*z[ix]).sum()/8/(z@z))if z@z>0 else 0.
def fit(ci,a):
 if ci==0:return OrientationEnsembleForest(**configs[0]['params'],seeds=(7,42,99)).fit(a[cols],a.count_2017_2021)
 key=tuple(a.grid_id)
 if weightcache.get('key')!=key:
  weightcache.clear();weightcache['key']=key;weightcache['diagnostics']=training_residual_diagnostics(a[cols],a.count_2017_2021,{**base,'seeds':(7,42,99)});di=weightcache['diagnostics'];pd.DataFrame({'grid_id':a.grid_id,'oof_residual':di['residual'],'hard_score':di['hard_score'],'same_sign_neighbor_fraction':di['same_sign_neighbor_fraction']}).to_csv(O/f'inner_diagnostics_{len(a)}_{len(list(O.glob("inner_diagnostics_*.csv")))}.csv',index=False)
 return ClusterWeightedOrientationForest(**configs[ci]['params'],seeds=(7,42,99)).fit_with_diagnostics(a[cols],a.count_2017_2021,weightcache['diagnostics'])
for fi,f in enumerate(folds):
 a=tr[tr.grid_id.isin(f['buffered_fit_ids'])];b=tr[tr.grid_id.isin(f['eval_ids'])];assert gap(a,b).all()
 for ci,c in enumerate(configs):
  m=fit(ci,a);p=m.predict(b[cols]);predictions[ci][b.index]=p;results.append({'candidate':ci,'name':c['name'],'fold':fi,**metrics(b.count_2017_2021,p)});print('CV',fi,ci,c['name'],flush=True)
 pd.DataFrame(results).to_csv(O/'cv_fold_scores.csv',index=False)
f=pd.DataFrame(results);scores=[]
for ci,c in enumerate(configs):
 assert np.isfinite(predictions[ci]).all(); ff=f[f.candidate==ci];scores.append({'candidate':ci,'name':c['name'],**metrics(tr.count_2017_2021,predictions[ci]),'mean_fold_rmse':float(ff.rmse.mean()),'mean_fold_mae':float(ff.mae.mean()),'moran_i':moran(tr.count_2017_2021,predictions[ci],tr[['cx','cy']])})
s=pd.DataFrame(scores);s.to_csv(O/'cv_scores.csv',index=False);a=s.iloc[0];short=s[(s.candidate!=0)&(s.mean_fold_rmse<a.mean_fold_rmse)&(s.mean_fold_mae<a.mean_fold_mae)&(s.p90_abs_error<=a.p90_abs_error)&(s.error_gt200_count<=a.error_gt200_count)&(s.moran_i.abs()<=abs(a.moran_i))].sort_values(['mean_fold_rmse','mean_fold_mae']).head(3).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True)
v=[]
for ci in [0]+short:
 m=fit(ci,tr);p=m.predict(va[cols]);v.append({'candidate':ci,'name':configs[ci]['name'],**metrics(va.count_2017_2021,p),'moran_i':moran(va.count_2017_2021,p,va[['cx','cy']])})
v=pd.DataFrame(v);v.to_csv(O/'validation_scores.csv',index=False);a=v.iloc[0];passing=v[(v.candidate!=0)&(v.rmse<a.rmse)&(v.mae<a.mae)&(v.p90_abs_error<=1.02*a.p90_abs_error)&(v.error_gt200_count<=a.error_gt200_count)&(v.moran_i.abs()<=abs(a.moran_i))];ci=int(passing.sort_values(['rmse','mae']).iloc[0].candidate)if len(passing)else 0
frozen={'candidate':ci,'config':configs[ci],'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'development_validation_pass':bool(ci)};dump(frozen,'frozen_decision.json');print('FROZEN',ci,flush=True)
geo=[];gate=False
if ci:
 for name,col in [('north20pct','cy'),('east20pct','cx')]:
  cutoff=dev[col].quantile(.8);b=dev[dev[col]>=cutoff];a=dev[dev[col]<cutoff];a=a.loc[gap(a,b)]
  for k in [0,ci]:
   m=fit(k,a);p=m.predict(b[cols]);geo.append({'region':name,'candidate':k,'n_fit':len(a),'n_eval':len(b),**metrics(b.count_2017_2021,p)});print('GEO',name,k,flush=True)
 g=pd.DataFrame(geo);g.to_csv(O/'geographic_gate.csv',index=False);old=g[g.candidate==0].set_index('region');new=g[g.candidate==ci].set_index('region');ratios=new[['rmse','mae']]/old[['rmse','mae']];gate=bool((ratios<=1.05).all().all()and(ratios.mean()<=1.01).all());dump(ratios.to_dict(),'geographic_ratios.json')
out={'decision':frozen,'geographic_gate_pass':gate,'promote':False,'legacy_evaluated':False}
if ci and gate:
 champion=joblib.load(modelpath);m=fit(ci,dev);test=df[df.eligible&(df.split=='test')];before=champion.predict(test[cols]);after=m.predict(test[cols]);bm=metrics(test.count_2017_2021,before);am=metrics(test.count_2017_2021,after);bm['moran_i']=moran(test.count_2017_2021,before,test[['cx','cy']]);am['moran_i']=moran(test.count_2017_2021,after,test[['cx','cy']]);out.update({'legacy_evaluated':True,'before':bm,'after':am,'promote':am['rmse']<bm['rmse']and am['mae']<bm['mae']and am['p90_abs_error']<=1.02*bm['p90_abs_error']and am['error_gt200_count']<=bm['error_gt200_count']and abs(am['moran_i'])<=abs(bm['moran_i'])});pd.DataFrame({'grid_id':test.grid_id,'observed':test.count_2017_2021,'before':before,'after':after}).to_csv(O/'legacy_comparison.csv',index=False)
 if out['promote']:joblib.dump(m,O/'candidate.joblib')
assert hashlib.sha256(modelpath.read_bytes()).hexdigest()==protocol['reference_sha256'];dump(out,'evaluation.json');print('COMPLETE',json.dumps(out),flush=True)
