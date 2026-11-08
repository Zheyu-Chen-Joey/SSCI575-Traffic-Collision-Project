"""Frozen multi-orientation RF study using only existing development partitions."""
import pathlib,sys,json,hashlib,datetime,copy
R=pathlib.Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'.runtime'),str(R/'03_scripts/pretraining')]
import numpy as np,pandas as pd,joblib
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from rf_local_weighted_model import LocalWeightedSpatialForest
from rf_rotated_local_model import RotatedLocalSpatialForest
from rf_orientation_ensemble import OrientationEnsembleForest
P=R/'04_outputs/rf_spatial_v5';O=R/'06_reports/_qa/orientation_ensemble';O.mkdir(exist_ok=True,parents=True);assert not(O/'protocol.json').exists()
source=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv';mp=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(mp)=='fe5057d5a2fd68ab7c5c4073744242974b2f874c9580f01bb924d646196cd749','Study requires frozen v7 champion'
df=pd.read_csv(source);tr=df[df.eligible&(df.split=='train')].reset_index(drop=True);va=df[df.eligible&(df.split=='validation')].reset_index(drop=True);dev=pd.concat([tr,va],ignore_index=True);cols=json.loads((R/'05_models/rf_spatial_v5/input_contract.json').read_text())['features'];decision=json.loads((P/'frozen_decision.json').read_text());base={**decision['settings'],**decision['local_weighting_settings']};folds=json.loads((P/'cv_fold_ids.json').read_text());seeds=(7,42,99)
configs=[([0,60],[.5,.5]),([0,45,60],[1/3,1/3,1/3]),([0,60,75],[.5,.25,.25]),([0,45,75],[.5,.25,.25]),([0,30,60],[.5,.25,.25]),([0,45,60,75],[.25]*4),([0,30,45,60,75],[.2]*5),([0,60,75],[.25,.5,.25]),([0,45,60],[.25,.25,.5]),([0,30,60],[.25,.25,.5]),([0,45,75],[.25,.375,.375]),([0,60,75],[.6,.2,.2]),([0,45,60,75],[.5,1/6,1/6,1/6])]
def dump(x,n):(O/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def metrics(y,p):
 y=np.asarray(y);return dict(rmse=float(np.sqrt(mean_squared_error(y,p))),mae=float(mean_absolute_error(y,p)),r2=float(r2_score(y,p)),bias=float(np.mean(p-y)),p90_abs_error=float(np.quantile(abs(y-p),.9)))
def gap(a,b):
 dx=np.maximum(abs(a.cx.to_numpy()[:,None]-b.cx.to_numpy()[None,:])-1000,0);dy=np.maximum(abs(a.cy.to_numpy()[:,None]-b.cy.to_numpy()[None,:])-1000,0);return np.sqrt(dx*dx+dy*dy).min(axis=1)>1000
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':sha(mp),'input_sha256':sha(source),'base_settings':base,'seeds':list(seeds),'configs':[{'candidate':i,'angles':a,'weights':w}for i,(a,w)in enumerate(configs)],'selection':'Fixed 5fold1km-square-gap CV on train720. Both meanfoldRMSE andMAE must lower than champion; shortlist3 bymeanRMSE. Fittrain720 and evaluate166validation; require bothRMSE+MAE lower andp90<=1.02champion; choose lowestRMSE thenMAE. Freeze before geographic check.','geographic_gate':'Development886 north/east20pct contiguous holdouts with>1km-square-gap. EveryregionRMSE+MAE ratio<=1.05; mean regionratio<=1.01 forbothmetrics. These repeatedly viewed checks are development only.','legacy_gate':'After geographic pass only, frozen model fit886 and evaluated once on reused227region; promote only ifRMSE+MAE lower andp90<=1.02champion. Adaptive exploratory acceptance, not independent testing.','features':'Existing18 only, zero change to1km grid orraw records; basis models fit only foldtraining; no neighboring outcome atprediction','cost':'Basis forests shared across convex combinations within same training subset; no sharing between training folds'};dump(protocol,'protocol.json')
def basis(a,b,angles):
 predictions={}
 for angle in sorted(set(angles)):
  m=(LocalWeightedSpatialForest(**base,seeds=seeds)if angle==0 else RotatedLocalSpatialForest(**base,seeds=seeds,rotation_degrees=float(angle))).fit(a[cols],a.count_2017_2021);predictions[angle]=m.predict(b[cols]);print('BASIS',len(a),len(b),angle,flush=True)
 return predictions
def combine(pred,ci):
 angles,weights=configs[ci];return sum(w*pred[a]for a,w in zip(angles,weights))
oof={i:np.full(len(tr),np.nan)for i in range(len(configs))};rows=[]
for fi,f in enumerate(folds):
 a=tr[tr.grid_id.isin(f['buffered_fit_ids'])];b=tr[tr.grid_id.isin(f['eval_ids'])];assert gap(a,b).all();pred=basis(a,b,[0,30,45,60,75])
 for ci in range(len(configs)):
  pp=combine(pred,ci);oof[ci][b.index]=pp;rows.append({'fold':fi,'candidate':ci,**metrics(b.count_2017_2021,pp)})
 pd.DataFrame(rows).to_csv(O/'cv_fold_scores.csv',index=False)
table=pd.DataFrame(rows);scores=[]
for ci in range(len(configs)):
 assert np.isfinite(oof[ci]).all();t=table[table.candidate==ci];scores.append({'candidate':ci,**metrics(tr.count_2017_2021,oof[ci]),'mean_fold_rmse':float(t.rmse.mean()),'mean_fold_mae':float(t.mae.mean())})
s=pd.DataFrame(scores);s.to_csv(O/'cv_scores.csv',index=False);pd.DataFrame({'grid_id':tr.grid_id,**{str(k):v for k,v in oof.items()}}).to_csv(O/'oof_predictions.csv',index=False);ref=s.iloc[0];short=s[(s.candidate!=0)&(s.mean_fold_rmse<ref.mean_fold_rmse)&(s.mean_fold_mae<ref.mean_fold_mae)].sort_values(['mean_fold_rmse','mean_fold_mae']).head(3).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True)
angles=set(a for ci in[0]+short for a in configs[ci][0]);pred=basis(tr,va,angles);val=[{'candidate':ci,**metrics(va.count_2017_2021,combine(pred,ci))}for ci in[0]+short];v=pd.DataFrame(val);v.to_csv(O/'validation_scores.csv',index=False);pd.DataFrame({'grid_id':va.grid_id,**{str(ci):combine(pred,ci)for ci in[0]+short}}).to_csv(O/'validation_predictions.csv',index=False);ref=v.iloc[0];passing=v[(v.candidate!=0)&(v.rmse<ref.rmse)&(v.mae<ref.mae)&(v.p90_abs_error<=ref.p90_abs_error*1.02)];ci=int(passing.sort_values(['rmse','mae']).iloc[0].candidate)if len(passing)else 0
frozen={'candidate':ci,'angles':configs[ci][0],'weights':configs[ci][1],'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'validation_pass':bool(ci)};dump(frozen,'frozen_decision.json');print('FROZEN',ci,flush=True);geo=[];gate=False
if ci:
 for name,col in[('north20pct','cy'),('east20pct','cx')]:
  threshold=dev[col].quantile(.8);b=dev[dev[col]>=threshold];a=dev[dev[col]<threshold];a=a.loc[gap(a,b)];pred=basis(a,b,set(configs[0][0]+configs[ci][0]))
  for k in[0,ci]:geo.append({'region':name,'candidate':k,'n_fit':len(a),'n_eval':len(b),**metrics(b.count_2017_2021,combine(pred,k))})
 g=pd.DataFrame(geo);g.to_csv(O/'geographic_gate.csv',index=False);old=g[g.candidate==0].set_index('region');new=g[g.candidate==ci].set_index('region');ratios=new[['rmse','mae']]/old[['rmse','mae']];gate=bool((ratios<=1.05).all().all()and(ratios.mean()<=1.01).all());dump(ratios.to_dict(),'geographic_ratios.json')
out={'decision':frozen,'geographic_gate_pass':gate,'legacy_evaluated':False,'promote':False}
if ci and gate:
 m=OrientationEnsembleForest(**base,seeds=seeds,orientation_angles=tuple(configs[ci][0]),orientation_weights=tuple(configs[ci][1])).fit(dev[cols],dev.count_2017_2021);old=joblib.load(mp);test=df[df.eligible&(df.split=='test')];before=old.predict(test[cols]);after=m.predict(test[cols]);bm=metrics(test.count_2017_2021,before);am=metrics(test.count_2017_2021,after);out.update(legacy_evaluated=True,before=bm,after=am,promote=am['rmse']<bm['rmse']and am['mae']<bm['mae']and am['p90_abs_error']<=1.02*bm['p90_abs_error']);pd.DataFrame({'grid_id':test.grid_id,'observed':test.count_2017_2021,'before':before,'after':after}).to_csv(O/'legacy_comparison.csv',index=False)
 if out['promote']:joblib.dump(m,O/'candidate.joblib')
assert sha(mp)==protocol['reference_sha256'];dump(out,'evaluation.json');print('COMPLETE',json.dumps(out),flush=True)
