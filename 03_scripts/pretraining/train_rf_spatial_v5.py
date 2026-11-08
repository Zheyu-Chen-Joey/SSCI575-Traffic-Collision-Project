"""Position-augmented RF, with actual square-to-square1km-buffered training CV."""
import sys,pathlib,json,hashlib,datetime,itertools
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.model_selection import GroupKFold,ParameterSampler
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from pipeline_definition import feature_names
from rf_spatial_model import SpatialCoverageForest
O=ROOT/'04_outputs/rf_spatial_v5';M=ROOT/'05_models/rf_spatial_v5';O.mkdir(exist_ok=True);M.mkdir(exist_ok=True);assert not(O/'evaluation.json').exists(),'Use a new run directory for further experiments'
def write(v,n):(O/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item()if hasattr(x,'item')else str(x)),encoding='utf-8')
def met(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
def moran(r,xy,perms=0):
 z=np.asarray(r)-np.mean(r);n=len(z);k=min(8,n-1);nn=cKDTree(xy).query(xy,k=k+1)[1][:,1:];den=z@z;I=float((z[:,None]*z[nn]).sum()/k/den);v={'I':I,'k':k}
 if perms:
  rng=np.random.default_rng(575);null=[]
  for _ in range(perms):
   q=rng.permutation(z);null.append((q[:,None]*q[nn]).sum()/k/den)
  v['p_two_sided']=float((1+np.sum(np.abs(np.asarray(null)+1/(n-1))>=abs(I+1/(n-1))))/(perms+1));v['permutations']=perms
 return v
def buffer_keep(a,b,gap):
 # Exact distance between axis-aligned FULL1km squares; city fragments cannot make it smaller.
 dx=np.maximum(np.abs(a.cx.to_numpy()[:,None]-b.cx.to_numpy()[None,:])-1000,0);dy=np.maximum(np.abs(a.cy.to_numpy()[:,None]-b.cy.to_numpy()[None,:])-1000,0);dist=np.sqrt(dx*dx+dy*dy).min(axis=1);return dist>gap
src=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';df=pd.read_csv(src);e=df[df.eligible];tr=e[e.split=='train'].copy();va=e[e.split=='validation'].copy();dev=pd.concat([tr,va],ignore_index=True);original=feature_names('enhanced');cols=original+['cx','cy'];base=json.loads((ROOT/'04_outputs/rf_project_v1/frozen_selection.json').read_text())['enhanced']['best_parameters'];params=[base]+list(ParameterSampler({'rf__n_estimators':[500],'rf__max_depth':[8,12,16,None],'rf__min_samples_leaf':[3,5,10],'rf__min_samples_split':[10],'rf__max_features':[.5,.7,1.0],'rf__criterion':['squared_error','poisson']},n_iter=7,random_state=57505));settings=[{'landuse_mode':lu,'scale_mode':sc,'rf_params':base,'include_position':False}for lu,sc in itertools.product(['raw','conditional'],['none','signal_sqrt'])]+[{'landuse_mode':lu,'scale_mode':sc,'rf_params':pa,'include_position':True}for lu,sc,pa in itertools.product(['raw','conditional'],['none','signal_sqrt'],params)];outer=list(GroupKFold(5).split(tr,groups=tr.block_id));folds=[]
for fi,(a,b)in enumerate(outer):
 keep=buffer_keep(tr.iloc[a],tr.iloc[b],1000);buf=a[keep];assert len(buf)>100;folds.append((a,b,buf))
protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':'User explicitly allowed grid-center coordinate extension and continued spatial validation','original_plan_extension':True,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'crs':'EPSG26911','position_fields':'(cx-345000)/1000,(cy-3730000)/1000 in km; fixed transformations, no target-derived coordinates','input_features':cols,'candidates':settings,'CV':'training720 only; fixed5km GroupKFold5; both ordinary and square-to-square gap strictly >1000m buffered fit rows','selection':'buffered5fold mean RMSE <=no-position anchor, mean MAE<=1.02anchor; rank RMSE/anchor +0.15abs(pooledOOF I)/abs(anchorI). Validate at most5 shortlisted plus matched no-position controls; single seed42 and fixed mean seeds7/42/99. Validation RMSE<original,MAE<=original,absI<=original. Choose min RMSE/anchor+0.15absI/anchor; freeze before legacy comparison.','additional_checks':'development-only north20pct/east20pct contiguous holdouts with1000m polygon gap; no refit based on legacy scores','legacy_region':'repeatedly observed, all comparisons exploratory, NOT new independent validation','no_predictors':['neighbor outcome','HIN','traffic volume','speed limit'],'interpretation':'position improves spatial interpolation if supported; not causal explanation or guaranteed new-region/time forecasting','signal_proxy':'mixed signal/control and speed-feedback locations, not a pure historical signal inventory'};write(protocol,'protocol.json');write([{'fold':i,'fit_ids':tr.iloc[a].grid_id.tolist(),'eval_ids':tr.iloc[b].grid_id.tolist(),'buffered_fit_ids':tr.iloc[c].grid_id.tolist(),'buffered_n':len(c)}for i,(a,b,c)in enumerate(folds)],'cv_fold_ids.json');scores=[];foldrows=[];oofall=[];y=tr.count_2017_2021.to_numpy();print('START',len(settings),'candidates',flush=True)
for ci,s in enumerate(settings):
 pred_modes={}
 for mode in ['ordinary','buffered']:
  p=np.zeros(len(tr));fr=[]
  for fi,(a,b,buffered)in enumerate(folds):
   fitrows=a if mode=='ordinary'else buffered;fit=SpatialCoverageForest(**s);fit.fit(tr.iloc[fitrows][cols],y[fitrows]);p[b]=fit.predict(tr.iloc[b][cols]);m=met(y[b],p[b]);fr.append(m);foldrows.append({'candidate':ci,'mode':mode,'fold':fi,'n_fit':len(fitrows),'n_eval':len(b),**m})
  scores.append({'candidate':ci,'mode':mode,'mean_rmse':float(np.mean([r['rmse']for r in fr])),'mean_mae':float(np.mean([r['mae']for r in fr])),**met(y,p),'moran_i':moran(y-p,tr[['cx','cy']])['I'],'position':s['include_position'],'landuse_mode':s['landuse_mode'],'scale_mode':s['scale_mode']});oofall.append(pd.DataFrame({'candidate':ci,'mode':mode,'grid_id':tr.grid_id,'observed':y,'predicted':p}));pred_modes[mode]=scores[-1]
 pd.DataFrame(scores).to_csv(O/'cv_scores.csv',index=False);pd.DataFrame(foldrows).to_csv(O/'cv_fold_scores.csv',index=False);print(ci,'xy',s['include_position'],s['landuse_mode'],s['scale_mode'],'bufferRMSE',round(pred_modes['buffered']['mean_rmse'],2),'I',round(pred_modes['buffered']['moran_i'],3),flush=True)
pd.concat(oofall,ignore_index=True).to_csv(O/'oof_predictions.csv',index=False);s=pd.DataFrame(scores);s=s[s['mode']=='buffered'];anchor=s[s.candidate==0].iloc[0];q=s[(s.position)&(s.mean_rmse<=anchor.mean_rmse)&(s.mean_mae<=1.02*anchor.mean_mae)].copy();q['objective']=q.mean_rmse/anchor.mean_rmse+.15*q.moran_i.abs()/abs(anchor.moran_i);short=q.sort_values('objective').head(5).candidate.astype(int).tolist();print('SHORTLIST',short,flush=True);validation=[];valrows=[];yv=va.count_2017_2021.to_numpy()
for ci in sorted(set([0,1,2,3]+short)):
 for label,seeds in [('single',(42,)),('ensemble',(7,42,99))]:
  if ci in [1,2,3]and label=='ensemble':continue
  fit=SpatialCoverageForest(**settings[ci],seeds=seeds);fit.fit(tr[cols],tr.count_2017_2021);p=fit.predict(va[cols]);key=f'{ci}_{label}';validation.append({'model_id':key,'candidate':ci,'seed_mode':label,**met(yv,p),'moran_i':moran(yv-p,va[['cx','cy']])['I']});valrows.append(pd.DataFrame({'model_id':key,'grid_id':va.grid_id,'observed':yv,'predicted':p}));joblib.dump(fit,M/f'{key}_trainonly.joblib')
v=pd.DataFrame(validation);v.to_csv(O/'validation_scores.csv',index=False);pd.concat(valrows,ignore_index=True).to_csv(O/'validation_predictions.csv',index=False);a=v[v.model_id=='0_single'].iloc[0];passed=v[(v.candidate.isin(short))&(v.rmse<a.rmse)&(v.mae<=a.mae)&(v.moran_i.abs()<=abs(a.moran_i))].copy();passed['objective']=passed.rmse/a.rmse+.15*passed.moran_i.abs()/abs(a.moran_i);choice=passed.sort_values('objective').iloc[0]if len(passed)else a;ci=int(choice.candidate);seeds=(7,42,99)if choice.seed_mode=='ensemble'else(42,);decision={'model_id':choice.model_id,'candidate':ci,'seed_mode':choice.seed_mode,'settings':settings[ci],'development_joint_gate_pass':ci in short,'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'legacy_target_for_selection':False};write(decision,'frozen_decision.json');print('FROZEN',decision,flush=True)
# Strictly development-only geographic transfer checks; fixed before legacy evaluation.
rob=[];axis_defs=[('north20pct','cy'),('east20pct','cx')]
for axis,col in axis_defs:
 cutoff=float(dev[col].quantile(.8));b=np.flatnonzero(dev[col].to_numpy()>=cutoff);a=np.flatnonzero(dev[col].to_numpy()<cutoff);a=a[buffer_keep(dev.iloc[a],dev.iloc[b],1000)];assert len(a)>100
 for name,setting,seedlist in [('no_position_anchor',settings[0],(42,)),('selected_spatial',settings[ci],seeds)]:
  fit=SpatialCoverageForest(**setting,seeds=seedlist);fit.fit(dev.iloc[a][cols],dev.iloc[a].count_2017_2021);p=fit.predict(dev.iloc[b][cols]);rob.append({'region':axis,'model':name,'n_fit':len(a),'n_eval':len(b),'cutoff':cutoff,**met(dev.iloc[b].count_2017_2021.to_numpy(),p),'moran_i':moran(dev.iloc[b].count_2017_2021.to_numpy()-p,dev.iloc[b][['cx','cy']])['I']})
pd.DataFrame(rob).to_csv(O/'geographic_transfer_checks.csv',index=False)
# Fit frozen selected model only on original886development cells.
fit=SpatialCoverageForest(**settings[ci],seeds=seeds);fit.fit(dev[cols],dev.count_2017_2021);joblib.dump(fit,M/'spatial_frozen_rf.joblib');old=joblib.load(ROOT/'05_models/rf_project_v1/enhanced_optimized_rf.joblib');test=e[e.split=='test'];yt=test.count_2017_2021.to_numpy();ev={'decision':decision,'legacy_reuse_is_exploratory':True};out=[]
for key,m,inputs in [('v1',old,original),('spatial_v5',fit,cols)]:
 p=m.predict(test[inputs]);ev[key]={'legacy_evaluation':met(yt,p),'moran':moran(yt-p,test[['cx','cy']],9999)};z=df[['grid_id','split','eligible','count_2017_2021','cx','cy']].copy();z['model']=key;z['predicted']=m.predict(df[inputs]);z['residual']=z.count_2017_2021-z.predicted;z['prediction_role']=np.where(~z.eligible,'boundary_extrapolation',np.where(z.split=='test','legacy_reuse','development_fit'));out.append(z)
write(ev,'evaluation.json');pd.concat(out,ignore_index=True).to_csv(O/'all_predictions.csv',index=False);print('COMPLETE',json.dumps(ev),flush=True)
