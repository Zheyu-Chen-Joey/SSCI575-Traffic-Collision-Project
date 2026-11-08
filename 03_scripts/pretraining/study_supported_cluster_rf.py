"""Geometry-guarded cluster RF with boundary AND interior development holdouts."""
from pathlib import Path
import sys,json,hashlib,datetime,copy,argparse
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'.runtime'),str(R/'03_scripts/pretraining')]
import numpy as np,pandas as pd,joblib
from scipy.spatial import cKDTree
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from rf_supported_cluster_model import SupportedClusterForest
from rf_cluster_weighted_model import training_residual_diagnostics,polygon_gap_keep
ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args=ap.parse_args()
P=R/'04_outputs/rf_spatial_v5';O=R/'06_reports/_qa/supported_cluster_v8';O.mkdir(exist_ok=True,parents=True);assert args.resume or not(O/'protocol.json').exists();mp=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();assert sha(mp)=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357';source=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv';df=pd.read_csv(source);tr=df[df.eligible&(df.split=='train')].reset_index(drop=True);va=df[df.eligible&(df.split=='validation')].reset_index(drop=True);dev=pd.concat([tr,va],ignore_index=True);cols=json.loads((R/'05_models/rf_spatial_v5/input_contract.json').read_text())['features'];D=json.loads((P/'frozen_decision.json').read_text());base={**D['settings'],**D['local_weighting_settings'],**D['orientation_settings']};folds=json.loads((P/'cv_fold_ids.json').read_text());configs=[{'candidate':0,'taper_m':0.,'strength':0.}]+[{'candidate':i+1,'taper_m':t,'strength':s}for i,(t,s)in enumerate((t,s)for t in[0.,2000.,5000.]for s in[.5,1.])]
def dump(value,name):(O/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
def metrics(y,p,xy):
 y=np.asarray(y);p=np.asarray(p);r=y-p;z=r-r.mean();k=min(8,len(y)-1);ix=cKDTree(np.asarray(xy)).query(np.asarray(xy),k=k+1)[1][:,1:];I=float((z[:,None]*z[ix]).sum()/k/(z@z))if z@z>0 else 0
 return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y)),'p90_abs_error':float(np.quantile(abs(r),.9)),'error_gt200_count':int((abs(r)>200).sum()),'moran_i':I}
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_sha256':sha(mp),'input_sha256':sha(source),'base_settings':base,'configs':configs,'seeds':[7,42,99],'correction':'Fixed strong1 local-only trainOOF weighting from prior study. Blend with retained RF using only convex-hull training support; correctionzero outside hull, taperinside boundary0/2/5km. Input18 andgrid unchanged.','nested_weights':'Reuse frozen innerOOF weights only for exact same fitgridIDs+order. Otherwise recompute3fold1km-gap lightweight RF seed42 global200/local100. No evaluation labels in weights.','development_selection':'Fixed5fold1km-gap train720. Require meanRMSE+MAE lower,p90/errorgt200/absMoran no worse. Shortlist3 bymeanRMSE. Validation166 requiresRMSE+MAE lower,p90/errorgt200/absMoran no worse. Evaluate ALLvalidationpassing candidates on4geographic development holdouts beforefinalfreeze.','geographic_boundary':'North20pct/east20pct with1km-square-gap. Require allRMSE,MAE,p90,errorgt200 no worse thanreferencewithin1e-9. Zero correction is fallback protection, not improved extrapolation.','geographic_interior':'Fixed5km blocks6_6 and6_8 from previouslyidentifiedTRAININGOOFclusters; adaptive development stress checks, not independent tests. Keep1km-square-gap. EachRMSE+MAE<=1.02reference; pooledRMSE,MAE,p90,errorgt200,absMoran no worse.','freeze':'Choose minimumvalidationRMSE thenMAE amongcandidates passingall4geographicchecks. Freeze beforeone legacycomparison.','legacy_gate':'Reused227 exploratoryonly. RequireRMSE+MAE strictlylower,p90+errorgt200 no worse withatleastone strictlylower,andabsoluteMoranI strictlylower. No tolerance relaxation afterviewing.','scope_limits':'Spatial support does not prove feature validity or calibrated uncertainty. Interior holdouts test supportguard insidecity; allregions have been used for development.'}
if args.resume:
 saved=json.loads((O/'protocol.json').read_text());assert saved['input_sha256']==sha(source)and saved['configs']==configs and saved['base_settings']==base;protocol=saved
else:dump(protocol,'protocol.json')
def diagnostics(a):
 for folder in [R/'04_outputs/cluster_targeted_optimization/global_and_local',R/'04_outputs/cluster_targeted_optimization/local_only']:
  for file in folder.glob(f'inner_diagnostics_{len(a)}_*.csv'):
   c=pd.read_csv(file)
   if list(c.grid_id)!=list(a.grid_id):continue
   xy=a[['cx','cy']].to_numpy();ij=np.floor((xy-np.array([345000,3730000]))/5000).astype(int);groups=np.array([f'{i}_{j}'for i,j in ij]);records=[]
   for f,(fit,ev)in enumerate(GroupKFold(3).split(a,a.count_2017_2021,groups)):
    fit=fit[polygon_gap_keep(xy[fit],xy[ev])];records.append({'fold':f,'fit_rows':len(fit),'eval_rows':len(ev),'fit_xy':xy[fit].tolist(),'eval_xy':xy[ev].tolist()})
   return {'hard_score':c.hard_score.to_numpy(),'same_sign_neighbor_fraction':c.same_sign_neighbor_fraction.to_numpy(),'inner_folds':records}
 return training_residual_diagnostics(a[cols],a.count_2017_2021,{**base,'seeds':(7,42,99)})
def fit(a):return SupportedClusterForest(**base,seeds=(7,42,99)).fit_with_diagnostics(a[cols],a.count_2017_2021,diagnostics(a))
def predict(m,b,c,branches):
 m.support_taper_m=c['taper_m'];m.correction_strength=c['strength'];g=m.support_gate(b[cols])*m.correction_strength;return branches[0]+g*(branches[1]-branches[0]),g
def ordinary_pass(row,reference):return row.rmse<reference.rmse and row.mae<reference.mae and row.p90_abs_error<=reference.p90_abs_error and row.error_gt200_count<=reference.error_gt200_count and abs(row.moran_i)<=abs(reference.moran_i)
if not args.resume:
 oof={i:np.full(len(tr),np.nan)for i in range(len(configs))};gates={i:np.zeros(len(tr))for i in range(len(configs))};rows=[]
 for fi,f in enumerate(folds):
  a=tr[tr.grid_id.isin(f['buffered_fit_ids'])];b=tr[tr.grid_id.isin(f['eval_ids'])];assert polygon_gap_keep(a[['cx','cy']].to_numpy(),b[['cx','cy']].to_numpy()).all();m=fit(a);branches=m.prediction_branches(b[cols])
  for c in configs:
   p,g=predict(m,b,c,branches);oof[c['candidate']][b.index]=p;gates[c['candidate']][b.index]=g;rows.append({'fold':fi,'candidate':c['candidate'],**metrics(b.count_2017_2021,p,b[['cx','cy']]),'active_gate_fraction':float((g>0).mean())})
  pd.DataFrame(rows).to_csv(O/'cv_fold_scores.csv',index=False);print('CV',fi,'completed',flush=True)
 f=pd.DataFrame(rows);scores=[]
 for c in configs:
  ci=c['candidate'];assert np.isfinite(oof[ci]).all();ff=f[f.candidate==ci];scores.append({'candidate':ci,**metrics(tr.count_2017_2021,oof[ci],tr[['cx','cy']]),'mean_fold_rmse':float(ff.rmse.mean()),'mean_fold_mae':float(ff.mae.mean()),'active_gate_fraction':float((gates[ci]>0).mean())})
 s=pd.DataFrame(scores);s.to_csv(O/'cv_scores.csv',index=False);pd.DataFrame({'grid_id':tr.grid_id,**{str(i):p for i,p in oof.items()}}).to_csv(O/'oof_predictions.csv',index=False);r=s.iloc[0];passing=s[(s.candidate!=0)&(s.mean_fold_rmse<r.mean_fold_rmse)&(s.mean_fold_mae<r.mean_fold_mae)&(s.p90_abs_error<=r.p90_abs_error)&(s.error_gt200_count<=r.error_gt200_count)&(s.moran_i.abs()<=abs(r.moran_i))];short=passing.sort_values(['mean_fold_rmse','mean_fold_mae']).head(3).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True)
 m=fit(tr);branches=m.prediction_branches(va[cols]);val=[];vp={}
 for ci in [0]+short:
  p,g=predict(m,va,configs[ci],branches);vp[ci]=p;val.append({'candidate':ci,**metrics(va.count_2017_2021,p,va[['cx','cy']]),'active_gate_fraction':float((g>0).mean())})
 v=pd.DataFrame(val);v.to_csv(O/'validation_scores.csv',index=False);pd.DataFrame({'grid_id':va.grid_id,**{str(i):p for i,p in vp.items()}}).to_csv(O/'validation_predictions.csv',index=False);eligible=[int(row.candidate)for _,row in v.iterrows()if row.candidate!=0 and ordinary_pass(row,v.iloc[0])];print('VALIDATION_PASS',eligible,flush=True)
 geo=[];geopred=[]
 if eligible:
  cases=[]
  for name,col in [('north20pct','cy'),('east20pct','cx')]:
   threshold=dev[col].quantile(.8);cases.append((name,dev[dev[col]<threshold],dev[dev[col]>=threshold],'boundary'))
  for block in ['6_6','6_8']:cases.append(('interior_'+block,dev[dev.block_id!=block],dev[dev.block_id==block],'interior'))
  for name,a,b,kind in cases:
   a=a.loc[polygon_gap_keep(a[['cx','cy']].to_numpy(),b[['cx','cy']].to_numpy())];assert len(b)>8;m=fit(a);branches=m.prediction_branches(b[cols])
   for ci in [0]+eligible:
    p,g=predict(m,b,configs[ci],branches);geo.append({'region':name,'kind':kind,'candidate':ci,'n_fit':len(a),'n_eval':len(b),**metrics(b.count_2017_2021,p,b[['cx','cy']]),'active_gate_fraction':float((g>0).mean()),'max_gate':float(g.max())});geopred +=[{'region':name,'kind':kind,'candidate':ci,'grid_id':gid,'observed':float(y),'predicted':float(pp),'cx':float(cx),'cy':float(cy),'gate':float(gg)}for gid,y,pp,cx,cy,gg in zip(b.grid_id,b.count_2017_2021,p,b.cx,b.cy,g)]
   print('GEO',name,'completed',flush=True)
  pd.DataFrame(geo).to_csv(O/'geographic_scores.csv',index=False);pd.DataFrame(geopred).to_csv(O/'geographic_predictions.csv',index=False)
else:
 v=pd.read_csv(O/'validation_scores.csv');eligible=[int(row.candidate)for _,row in v.iterrows()if row.candidate!=0 and ordinary_pass(row,v.iloc[0])];geo=pd.read_csv(O/'geographic_scores.csv').to_dict('records');geopred=pd.read_csv(O/'geographic_predictions.csv').to_dict('records');print('RESUME completed developmental predictions',flush=True)
geopass=[];gate_records=[]
for ci in eligible:
 g=pd.DataFrame(geo);ref=g[g.candidate==0].set_index('region');new=g[g.candidate==ci].set_index('region');bound=new[new.kind=='boundary'];bref=ref.loc[bound.index];boundary_ok=bool((bound[['rmse','mae','p90_abs_error','error_gt200_count']]<=bref[['rmse','mae','p90_abs_error','error_gt200_count']]+1e-9).all().all());inside=new[new.kind=='interior'];iref=ref.loc[inside.index];ratio=inside[['rmse','mae']]/iref[['rmse','mae']];per_region_ok=bool((ratio<=1.02).all().all());records=pd.DataFrame(geopred);a=records[(records.candidate==0)&(records.kind=='interior')];b=records[(records.candidate==ci)&(records.kind=='interior')];a=a.sort_values(['region','grid_id']);b=b.sort_values(['region','grid_id']);bm=metrics(a.observed,a.predicted,a[['cx','cy']]);nm=metrics(b.observed,b.predicted,b[['cx','cy']]);pooled_ok=all(nm[k]<=bm[k]+1e-9 for k in ['rmse','mae','p90_abs_error','error_gt200_count'])and abs(nm['moran_i'])<=abs(bm['moran_i'])+1e-9;ok=boundary_ok and per_region_ok and pooled_ok;gate_records.append({'candidate':ci,'boundary_pass':boundary_ok,'interior_per_region_pass':per_region_ok,'interior_pooled_pass':pooled_ok,'reference_interior':bm,'candidate_interior':nm,'pass':ok})
 if ok:geopass.append(ci)
dump(gate_records,'geographic_gates.json');ci=int(v[v.candidate.isin(geopass)].sort_values(['rmse','mae']).iloc[0].candidate)if geopass else 0;decision={'candidate':ci,'config':configs[ci],'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'development_and_geographic_pass':bool(ci)};dump(decision,'frozen_decision.json');out={'decision':decision,'promote':False,'legacy_evaluated':False};print('FROZEN',ci,flush=True)
if ci:
 m=fit(dev);m.support_taper_m=configs[ci]['taper_m'];m.correction_strength=configs[ci]['strength'];test=df[df.eligible&(df.split=='test')];champion=joblib.load(mp);before=champion.predict(test[cols]);after=m.predict(test[cols]);bm=metrics(test.count_2017_2021,before,test[['cx','cy']]);am=metrics(test.count_2017_2021,after,test[['cx','cy']]);ok=am['rmse']<bm['rmse']and am['mae']<bm['mae']and am['p90_abs_error']<=bm['p90_abs_error']and am['error_gt200_count']<=bm['error_gt200_count']and(am['p90_abs_error']<bm['p90_abs_error']or am['error_gt200_count']<bm['error_gt200_count'])and abs(am['moran_i'])<abs(bm['moran_i']);out.update(legacy_evaluated=True,before=bm,after=am,promote=bool(ok));pd.DataFrame({'grid_id':test.grid_id,'observed':test.count_2017_2021,'before':before,'after':after,'gate':m.support_gate(test[cols])}).to_csv(O/'legacy_comparison.csv',index=False)
 if ok:joblib.dump(m,O/'candidate.joblib')
assert sha(mp)==protocol['reference_sha256'];dump(out,'evaluation.json');print('COMPLETE',json.dumps(out),flush=True)
