"""Independent verification and consolidated diagnostics for v4 and its conservative RF blend."""
import sys,pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,geopandas as gpd,joblib
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from pipeline_definition import feature_names,LANDUSE
from rf_coverage_scaled_model import CoverageScaledForest
from rf_fixed_blend import FixedForestBlend
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
O=ROOT/'04_outputs/rf_stability_blend_v4b';V=ROOT/'04_outputs/rf_coverage_v4';F=O/'figures';F.mkdir(exist_ok=True);df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');e=df[df.eligible];tr=e[e.split=='train'];dev=pd.concat([tr,e[e.split=='validation']],ignore_index=True);test=e[e.split=='test'];cols=feature_names('enhanced');model=joblib.load(ROOT/'05_models/rf_stability_blend_v4b/blend_frozen.joblib');ev=json.loads((O/'evaluation.json').read_text());v4=json.loads((V/'evaluation.json').read_text());sourcehash=hashlib.sha256((ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv').read_bytes()).hexdigest();assert sourcehash==json.loads((V/'protocol.json').read_text())['input_sha256'];folds=json.loads((V/'cv_fold_ids.json').read_text())
for fold in folds:
 a=df[df.grid_id.isin(fold['fit_ids'])];b=df[df.grid_id.isin(fold['eval_ids'])];assert set(a.split)=={'train'}and set(b.split)=={'train'};assert not(set(a.block_id)&set(b.block_id))
scaled=joblib.load(ROOT/'05_models/rf_coverage_v4/v4_frozen_rf.joblib');before=dev[cols].copy();transformed=scaled._X(before);pd.testing.assert_frame_equal(before,dev[cols]);coverage=(1-before.landuse_uncovered_fraction).clip(0,1);assert np.allclose(transformed[LANDUSE].sum(axis=1)[coverage>0],(before[LANDUSE].sum(axis=1)/coverage)[coverage>0],equal_nan=True);assert np.allclose(scaled._scale(before),np.sqrt(1+before.signal_density_snapshot_km2));assert np.isfinite(scaled.predict(test[cols])).all()
for m in scaled.forests_:assert all(np.isclose(t.tree_.weighted_n_node_samples[0],886)for t in m.named_steps['rf'].estimators_)
old=joblib.load(ROOT/'05_models/rf_project_v1/enhanced_optimized_rf.joblib');pold=old.predict(test[cols]);pnew=model.predict(test[cols]);assert np.allclose(pnew,.5*pold+.5*scaled.predict(test[cols]));y=test.count_2017_2021.to_numpy();assert np.isclose(np.sqrt(mean_squared_error(y,pnew)),ev['blend']['legacy_evaluation']['rmse']);assert np.isclose(mean_absolute_error(y,pnew),ev['blend']['legacy_evaluation']['mae']);assert np.isclose(r2_score(y,pnew),ev['blend']['legacy_evaluation']['r2'])
# Conditional paired block bootstrap; no refitting, no new independent test.
rng=np.random.default_rng(575);groups=test.block_id.unique();by={g:np.flatnonzero(test.block_id.to_numpy()==g)for g in groups};boot=[]
for _ in range(2000):
 ix=np.concatenate([by[g]for g in rng.choice(groups,len(groups),replace=True)]);boot.append({'delta_rmse':float(np.sqrt(np.mean((y[ix]-pnew[ix])**2))-np.sqrt(np.mean((y[ix]-pold[ix])**2))),'delta_mae':float(np.mean(abs(y[ix]-pnew[ix]))-np.mean(abs(y[ix]-pold[ix])))})
b=pd.DataFrame(boot);b.to_csv(O/'paired_block_bootstrap.csv',index=False);interval={c:{'lower':float(b[c].quantile(.025)),'upper':float(b[c].quantile(.975))}for c in b};(O/'bootstrap_intervals.json').write_text(json.dumps(interval,indent=2));res=y-pnew;z=res-res.mean();nn=cKDTree(test[['cx','cy']]).query(test[['cx','cy']],k=9)[1][:,1:];den=z@z;I=float((z[:,None]*z[nn]).sum()/8/den);rng=np.random.default_rng(575);null=[]
for _ in range(9999):
 q=rng.permutation(z);null.append((q[:,None]*q[nn]).sum()/8/den)
mp=float((1+np.sum(np.abs(np.array(null)+1/(len(z)-1))>=abs(I+1/(len(z)-1))))/10000);(O/'moran_permutation.json').write_text(json.dumps({'I':I,'p_two_sided':mp,'permutations':9999,'k':8},indent=2))
grid=gpd.read_file(ROOT/'01_data/processed/pretraining_1km/grid_1000.gpkg');g=grid[['grid_id','geometry']].merge(df,on='grid_id',validate='one_to_one');out=pd.read_csv(O/'all_predictions.csv')
for key in ['v1','blend']:
 sub=out[out.model==key];g=g.merge(sub[['grid_id','predicted','residual']].rename(columns={'predicted':key+'_pred','residual':key+'_resid'}),on='grid_id',validate='one_to_one')
g['prediction_role']=np.where(~g.eligible,'boundary_extrapolation',np.where(g.split=='test','legacy_reuse','development_fit'));g.to_file(O/'grid_comparison_1000.gpkg',driver='GPKG');g.drop(columns='geometry').to_csv(O/'grid_comparison_1000.csv',index=False);plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.dpi':180})
for scope in ['legacy','full_city']:
 a=g[g.eligible&(g.split=='test')]if scope=='legacy'else g[g.eligible];limit=max(a.v1_resid.abs().max(),a.blend_resid.abs().max());fig,axes=plt.subplots(1,2,figsize=(10,7))
 for ax,c,title in zip(axes,['v1_resid','blend_resid'],['V1 original RF','Conservative RF blend']):
  g.plot(ax=ax,color='#eeeeee');a.plot(column=c,ax=ax,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),legend=True,legend_kwds={'shrink':.4});ax.set_axis_off();ax.set_title(title)
  if scope=='full_city':g[g.eligible&(g.split=='test')].boundary.plot(ax=ax,color='black',linewidth=.3)
 fig.suptitle('Legacy evaluation reuse | same color scale | observed minus predicted'if scope=='legacy'else'Full city | black outlines = legacy evaluation\nOther colors show development fitted residuals, not independent accuracy',fontsize=11);fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(F/f'{scope}_residual_comparison.png',bbox_inches='tight');plt.close(fig)
rows=[]
for label,data,Ival in [('V1',ev['v1']['legacy_evaluation'],ev['v1']['moran_i']),('V4 scaled',v4['v4']['legacy_evaluation'],v4['v4']['moran']['I']),('V4b blend',ev['blend']['legacy_evaluation'],ev['blend']['moran_i'])]:rows.append({'model':label,**data,'moran_i':Ival})
s=pd.DataFrame(rows);s.to_csv(O/'model_comparison.csv',index=False);fig,axes=plt.subplots(1,3,figsize=(11,3.8))
for ax,c,title in zip(axes,['rmse','mae','moran_i'],['RMSE','MAE','Residual Moran I']):
 ax.bar(s.model,s[c],color=['#537aa3','#bf6738','#5c956e']);ax.set_title(title);ax.set_ylim(0,float(s[c].max())*1.18)
 for i,v in enumerate(s[c]):ax.text(i,v,f'{v:.3f}'if c=='moran_i'else f'{v:.2f}',ha='center',va='bottom')
fig.suptitle('Exploratory comparison on previously examined region | lower is preferred here');fig.tight_layout();fig.savefig(F/'metric_comparison.png',bbox_inches='tight');plt.close(fig)
verification={'status':'pass','input_snapshot_hash_unchanged':True,'all5CVfolds_train_only_and_block_disjoint':True,'conditional_landuse_shares_verified':True,'facility_scaling_verified':True,'original_dataframe_not_modified':True,'trained_forest_rows886':True,'blend_equals_fixed_half_half':True,'model_reload_metrics_match':True,'legacy_reuse_not_independent_confirmation':True,'bootstrap_intervals':interval,'moran_p':mp};(O/'verification.json').write_text(json.dumps(verification,indent=2));(V/'verification.json').write_text(json.dumps({k:v for k,v in verification.items()if k not in ['blend_equals_fixed_half_half','bootstrap_intervals']},indent=2));print(json.dumps(verification,indent=2))
