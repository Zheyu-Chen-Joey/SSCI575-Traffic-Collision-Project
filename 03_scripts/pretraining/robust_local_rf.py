"""Development-only RF objective/regularization study with frozen geographic gate."""
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

ap=argparse.ArgumentParser();ap.add_argument('--study',choices=['regularization','rotation','blend'],default='regularization');args=ap.parse_args()
P=R/'04_outputs/rf_spatial_v5'; O=R/'06_reports/_qa'/dict(regularization='robust_local',rotation='rotated_local',blend='coordinate_blend')[args.study]; O.mkdir(exist_ok=True,parents=True)
assert not (O/'protocol.json').exists(), 'Use a new audit directory for another run'
src=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv'
df=pd.read_csv(src); tr=df[df.eligible&(df.split=='train')].reset_index(drop=True); va=df[df.eligible&(df.split=='validation')].reset_index(drop=True); dev=pd.concat([tr,va],ignore_index=True)
decision=json.loads((P/'frozen_decision.json').read_text()); contract=json.loads((R/'05_models/rf_spatial_v5/input_contract.json').read_text()); cols=contract['features']; folds=json.loads((P/'cv_fold_ids.json').read_text())
modelpath=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib'
assert hashlib.sha256(modelpath.read_bytes()).hexdigest()=='06d3a830d589f96e4c37bacc52646424fb6f61d97c8460172edfc461f3b81ea1', 'Historical experiment requires the prior local-RF champion from Git ff6bfb6; use train_best_spatial_rf.py to reproduce the current champion.'
def dump(v,n): (O/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def metrics(y,p):
 y=np.asarray(y); return dict(rmse=float(np.sqrt(mean_squared_error(y,p))),mae=float(mean_absolute_error(y,p)),r2=float(r2_score(y,p)),bias=float(np.mean(p-y)),p90_abs_error=float(np.quantile(abs(y-p),.9)))
def gap(a,b):
 dx=np.maximum(abs(a.cx.to_numpy()[:,None]-b.cx.to_numpy()[None,:])-1000,0);dy=np.maximum(abs(a.cy.to_numpy()[:,None]-b.cy.to_numpy()[None,:])-1000,0);return np.sqrt(dx*dx+dy*dy).min(axis=1)>1000
base={**decision['settings'],**decision['local_weighting_settings']}; configs=[{'name':'champion','params':copy.deepcopy(base)}]
changes=[('poisson',{'rf__criterion':'poisson'},{}),('poisson_more_features',{'rf__criterion':'poisson','rf__max_features':.8},{}),('poisson_leaf8',{'rf__criterion':'poisson','rf__min_samples_leaf':8},{}),('leaf8',{'rf__min_samples_leaf':8},{}),('leaf12',{'rf__min_samples_leaf':12},{}),('depth10_features80',{'rf__max_depth':10,'rf__max_features':.8},{}),('wider15km',{}, {'bandwidth_m':15000.}),('wider20km_leaf8',{'rf__min_samples_leaf':8},{'bandwidth_m':20000.}),('poisson_raw_count',{'rf__criterion':'poisson'},{'scale_mode':'none'}),('poisson_road_sqrt',{'rf__criterion':'poisson'},{'scale_mode':'road_sqrt'})]
for name,rf,other in changes:
 p=copy.deepcopy(base);p['rf_params'].update(rf);p.update(other);configs.append({'name':name,'params':p})
if args.study=='rotation':
 configs=[{'name':'champion','params':copy.deepcopy(base)}]
 for angle in [15.,30.,45.,60.,75.]:
  p=copy.deepcopy(base);p['rotation_degrees']=angle;configs.append({'name':'rotation_'+str(int(angle)), 'params':p})
if args.study=='blend':
 configs=[{'name':'champion','params':copy.deepcopy(base)}]
 for weight in [.25,.5,.75]:
  p=copy.deepcopy(base);p.update(rotation_degrees=60.,rotated_weight=weight);configs.append({'name':'blend_'+str(weight),'params':p})
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':hashlib.sha256(modelpath.read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'seeds':[7,42,99],'configs':configs,'selection':'Fixed 5fold1km-gap CV on720training rows. Require both meanfoldRMSE andMAE lower than champion. Shortlist2 byRMSE. Fit720 and select validation166 winner lowering bothRMSE andMAE. Freeze before geographic gate.','geographic_gate':'North/east20pct of886development rows; >1km-square gap. Require each region RMSE andMAE ratio<=1.05 and meanratio<=1.01 for bothmetrics. These are reused development diagnostics, not independent tests.','legacy_gate':'Only if geographic gate passes, fit886; evaluate frozen candidate once on reused227region. Replace only ifRMSE+MAE lower andp90<=1.02champion. Exploratory adaptive acceptance, not independent validation.','features':'Same18 columns; no neighboring target inputs; no raw modifications; model type remains RF','retention':'One production champion, no unsuccessful candidate model files'}
dump(protocol,'protocol.json'); results=[]; predictions={i:np.full(len(tr),np.nan)for i in range(len(configs))}
fitcache={}
def fit(ci,a):
 params=configs[ci]['params'];factory=CoordinateBlendForest if 'rotated_weight'in params else(RotatedLocalSpatialForest if 'rotation_degrees'in params else LocalWeightedSpatialForest)
 if args.study=='blend':
  key=tuple(a.grid_id)
  if fitcache.get('key')!=key:fitcache.clear();fitcache['key']=key
  slot='champion'if ci==0 else'blend'
  if slot not in fitcache:fitcache[slot]=factory(**params,seeds=(7,42,99)).fit(a[cols],a.count_2017_2021)
  m=fitcache[slot]
  if ci:m.rotated_weight=params['rotated_weight']
  return m
 return factory(**params,seeds=(7,42,99)).fit(a[cols],a.count_2017_2021)
for fi,f in enumerate(folds):
 a=tr[tr.grid_id.isin(f['buffered_fit_ids'])];b=tr[tr.grid_id.isin(f['eval_ids'])];assert gap(a,b).all()
 for ci,c in enumerate(configs):
  m=fit(ci,a);p=m.predict(b[cols]);predictions[ci][b.index]=p;results.append({'candidate':ci,'name':c['name'],'fold':fi,**metrics(b.count_2017_2021,p)});print('CV',fi,ci,c['name'],flush=True)
 pd.DataFrame(results).to_csv(O/'cv_fold_scores.csv',index=False)
f=pd.DataFrame(results);scores=[]
for ci,c in enumerate(configs):
 assert np.isfinite(predictions[ci]).all(); ff=f[f.candidate==ci];scores.append({'candidate':ci,'name':c['name'],**metrics(tr.count_2017_2021,predictions[ci]),'mean_fold_rmse':float(ff.rmse.mean()),'mean_fold_mae':float(ff.mae.mean())})
s=pd.DataFrame(scores);s.to_csv(O/'cv_scores.csv',index=False);a=s.iloc[0];short=s[(s.candidate!=0)&(s.mean_fold_rmse<a.mean_fold_rmse)&(s.mean_fold_mae<a.mean_fold_mae)].sort_values(['mean_fold_rmse','mean_fold_mae']).head(2).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True)
v=[]
for ci in [0]+short:
 m=fit(ci,tr);p=m.predict(va[cols]);v.append({'candidate':ci,'name':configs[ci]['name'],**metrics(va.count_2017_2021,p)})
v=pd.DataFrame(v);v.to_csv(O/'validation_scores.csv',index=False);a=v.iloc[0];passing=v[(v.candidate!=0)&(v.rmse<a.rmse)&(v.mae<a.mae)];ci=int(passing.sort_values(['rmse','mae']).iloc[0].candidate)if len(passing)else 0
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
 champion=joblib.load(modelpath);m=fit(ci,dev);test=df[df.eligible&(df.split=='test')];before=champion.predict(test[cols]);after=m.predict(test[cols]);bm=metrics(test.count_2017_2021,before);am=metrics(test.count_2017_2021,after);out.update({'legacy_evaluated':True,'before':bm,'after':am,'promote':am['rmse']<bm['rmse']and am['mae']<bm['mae']and am['p90_abs_error']<=1.02*bm['p90_abs_error']});pd.DataFrame({'grid_id':test.grid_id,'observed':test.count_2017_2021,'before':before,'after':after}).to_csv(O/'legacy_comparison.csv',index=False)
 if out['promote']:joblib.dump(m,O/'candidate.joblib')
assert hashlib.sha256(modelpath.read_bytes()).hexdigest()==protocol['reference_sha256'];dump(out,'evaluation.json');print('COMPLETE',json.dumps(out),flush=True)
