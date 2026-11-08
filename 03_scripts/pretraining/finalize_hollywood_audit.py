"""Publish Hollywood research improvement and whole-validation limitations together."""
from pathlib import Path
import sys,json,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'.runtime'))
import numpy as np,pandas as pd,geopandas as gpd
from scipy.spatial import cKDTree
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
O=R/'04_outputs/hollywood_targeted_optimization';O.mkdir(exist_ok=True);sources={'nested_study':'hollywood_residual_v8','diagnostic_holdouts':'hollywood_residual_diagnostic'}
for name,folder in sources.items():
 source=R/'06_reports/_qa'/folder;result=json.loads((source/'evaluation.json').read_text());assert not result.get('legacy_evaluated',False);dest=O/name;dest.mkdir(exist_ok=True)
 for f in source.iterdir():
  if f.suffix in ['.csv','.json']:shutil.copy2(f,dest/f.name)
control=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';research=R/'05_models/rf_hollywood_research/hollywood_holdout_pair.joblib';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(control)=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357';assert research.exists();D=pd.read_csv(R/'01_data/processed/pretraining_1km/model_table_1000_final.csv');pred=pd.read_csv(O/'diagnostic_holdouts/geographic_predictions.csv');hw=pred[pred.region=='interior_6_8'].merge(D,on=['grid_id','cx','cy'],validate='one_to_one');assert len(hw)==24;hw['control_residual']=hw.observed-hw.control_prediction;hw['candidate_residual']=hw.observed-hw.candidate_prediction;hw['before_abs_error']=abs(hw.control_residual);hw['after_abs_error']=abs(hw.candidate_residual);hw['change_abs_error']=hw.after_abs_error-hw.before_abs_error;hw['threshold200_improved']=(hw.before_abs_error>200)&(hw.after_abs_error<=200);hw.to_csv(O/'hollywood_per_grid_comparison.csv',index=False)
thresholds=pd.DataFrame([{'absolute_error_threshold':t,'control_cells':int((hw.before_abs_error>t).sum()),'research_cells':int((hw.after_abs_error>t).sum())}for t in [150,200,250,300]]);thresholds.to_csv(O/'threshold_sensitivity.csv',index=False);labels=hw.i.astype(int).floordiv(2).astype(str)+'_'+hw.j.astype(int).floordiv(2).astype(str);groups=labels.unique();indices={g:np.flatnonzero((labels==g).to_numpy())for g in groups};rng=np.random.default_rng(575);boot=[]
for _ in range(2000):
 ix=np.concatenate([indices[g]for g in rng.choice(groups,len(groups),replace=True)]);a=hw.before_abs_error.to_numpy()[ix];b=hw.after_abs_error.to_numpy()[ix];boot.append([np.sqrt(np.mean(b*b))-np.sqrt(np.mean(a*a)),np.mean(b)-np.mean(a)])
boot=np.array(boot);uncertainty={'method':'2000paired2km-block resamples inside24developmentcells, seed575','blocks':len(groups),'delta_RMSE_quantile95':np.quantile(boot[:,0],[.025,.975]).tolist(),'delta_MAE_quantile95':np.quantile(boot[:,1],[.025,.975]).tolist(),'limitation':'Conditionalonfixedmodels andrepeatedlyviewed developerregion; excludesselection/retraining uncertainty, notindependentconfirmation'};(O/'conditional_bootstrap.json').write_text(json.dumps(uncertainty,indent=2))
grid=gpd.read_file(R/'01_data/processed/pretraining_1km/grid_1000.gpkg')[['grid_id','geometry']];g=gpd.GeoDataFrame(hw.merge(grid,on='grid_id',validate='one_to_one'),geometry='geometry',crs=26911);g.to_file(O/'hollywood_holdout_comparison.gpkg',driver='GPKG');area=grid.merge(D[['grid_id','block_id']],on='grid_id').query("block_id=='6_8'");limit=json.loads((R/'04_outputs/rf_spatial_v5/figure_color_scale.json').read_text())['full_city_residual_abs_limit'];assert max(g.control_residual.abs().max(),g.candidate_residual.abs().max())<=limit
fig,axes=plt.subplots(1,3,figsize=(13,4.8))
for ax,column,title in zip(axes,['observed','control_residual','candidate_residual'],['Observed collisions','Matched control residual','Research candidate residual']):
 area.plot(ax=ax,color='#eee');kwargs={'cmap':'YlOrRd','vmin':0,'vmax':float(D.loc[D.eligible,'count_2017_2021'].max())}if column=='observed'else{'cmap':'RdBu_r','norm':TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit)};g.plot(column=column,ax=ax,legend=True,legend_kwds={'shrink':.5},edgecolor='gray',linewidth=.4,**kwargs)
 for row in g.itertuples():ax.text(row.cx,row.cy,f'{getattr(row,column):.0f}',ha='center',va='center',fontsize=7)
 if column!='observed':g[g[column].abs()>200].boundary.plot(ax=ax,color='black',linewidth=1.3)
 ax.set_xlim(374800,380200);ax.set_ylim(3769800,3775200);ax.set_axis_off();ax.set_title(title,fontsize=10)
fig.suptitle('Hollywood 6_8 | 24 development holdout cells | both models fit834other cells\nResidual = observed - predicted | same fixed scale | bold cells have absolute error >200',fontsize=11);fig.tight_layout(rect=[0,0,1,.88]);fig.savefig(O/'hollywood_holdout_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
scores=pd.read_csv(O/'diagnostic_holdouts/geographic_scores.csv');scores.to_csv(O/'regional_metrics.csv',index=False);a=scores[(scores.region=='interior_6_8')&(scores.model=='control')].iloc[0];b=scores[(scores.region=='interior_6_8')&(scores.model=='research_candidate')].iloc[0];fig,axes=plt.subplots(1,4,figsize=(12,3.6))
for ax,key,title in zip(axes,['rmse','mae','error_gt200_count','moran_i'],['Hollywood RMSE','Hollywood MAE','Errors >200','Residual Moran I']):
 values=[a[key],b[key]];ax.bar(['Control','Research'],values,color=['#537aa3','#55976d']);ax.set_title(title,fontsize=10);ax.set_ylim(0,max(values)*1.2)
 for i,x in enumerate(values):ax.text(i,x,f'{x:.4f}'if key=='moran_i'else(f'{x:.0f}'if key=='error_gt200_count'else f'{x:.2f}'),ha='center',va='bottom',fontsize=8)
fig.suptitle('Hollywood development improvement | research only, not a production replacement',fontsize=11);fig.tight_layout();fig.savefig(O/'hollywood_metrics.png',dpi=180,bbox_inches='tight');plt.close(fig)
summary={'hollywood_joint_goals_improved':True,'formal_model_promoted':False,'validation_RMSE_gate_passed':False,'production_control_unchanged':True,'legacy_region_evaluated_this_round':False,'control_model':control.relative_to(R).as_posix(),'research_pair':research.relative_to(R).as_posix(),'pair_fit_rows':834,'hollywood_holdout_rows':24,'holdout_control_same_recipe_as_current_but_refit':True,'improved_cells':int((hw.change_abs_error<0).sum()),'worsened_cells':int((hw.change_abs_error>0).sum()),'unchanged_cells':int((hw.change_abs_error==0).sum()),'hollywood_control':a.to_dict(),'hollywood_research':b.to_dict(),'rmse_reduction_pct':float(100*(1-b.rmse/a.rmse)),'mae_reduction_pct':float(100*(1-b.mae/a.mae)),'interpretation':'Modest developerholdout gain, no significance/generalization claim. ValidationRMSEslightlyworse andI110Moran slightlyhigher, so production control retained.'};(O/'decision_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');verification={'control_sha256_unchanged':sha(control),'research_bundle_sha256':sha(research),'input_sha256':sha(R/'01_data/processed/pretraining_1km/model_table_1000_final.csv'),'source_count_total':230536,'production_model_files':1,'research_comparison_bundles':1,'holdout_and_buffer_excluded_from_pair_training':True,'pair_reloaded_predictions_match_diagnostic':True,'legacy_not_evaluated_this_round':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(O/'verification.json').write_text(json.dumps(verification,indent=2))
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d['hollywood_targeted_optimization']={'report':'06_reports/RF_Hollywood_Targeted_Optimization.docx','outputs':'04_outputs/hollywood_targeted_optimization','hollywood_joint_goals_improved':True,'formal_promoted':False,'production_control_unchanged':True,'research_pair':research.relative_to(R).as_posix(),'legacy_evaluated':False};d['retention']='one production control plus one research-only Hollywood matched holdout comparison bundle, as requested'
 if rel.startswith('07_agents'):d.update(scope='preserve_production_control_plus_Hollywood_research_pair',model_artifacts_retained=2,production_models_retained=1,research_bundles_retained=1)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'README.md';text=p.read_text(encoding='utf-8');note='''
## Hollywood专项研究对照

本轮保留当前正式模型作对照，另存[Hollywood留出研究对照包](05_models/rf_hollywood_research/hollywood_holdout_pair.joblib)及[契约](05_models/rf_hollywood_research/input_contract.json)。包内同配方对照与研究候选都只拟合834个开发格，Hollywood24格及1km缓冲均排除，公平比较；正式模型的886格版本仍原样保存。

候选用RF学习训练子集内部3折带间隔的有符号折外残差。Hollywood留出RMSE196.16→192.36、MAE150.21→146.23、绝对误差90分位311.41→307.94、超过200起误差格7→6、Moran I0.2429→0.2407；16格改善、5格变差、3格不变。改善幅度小，且减少的大误差格由202.11降至196.90，跨过200阈值，应关注阈值敏感性。

166格验证RMSE82.47→82.56略退步，I-110留出Moran I也略升，因此研究候选未替换正式模型，原227格未再评估。研究包不用于宣称全市正式模型提升。见[专项报告](06_reports/RF_Hollywood_Targeted_Optimization.docx)、[留出残差图](04_outputs/hollywood_targeted_optimization/hollywood_holdout_comparison.png)和[指标图](04_outputs/hollywood_targeted_optimization/hollywood_metrics.png)。

加载研究包后使用matched_control及research_candidate两个键。研究预测入口为03_scripts/pretraining/predict_hollywood_research_pair.py，输出明确标记research_only及留出适用范围；原正式预测入口不变。该研究配对重新训练入口为build_hollywood_comparison_pair.py --execute-training --output 新对照包.joblib，拒绝覆盖已存在文件。

'''
if '## Hollywood专项研究对照'not in text:text=text.replace('## 使用与复现',note+'## 使用与复现')
p.write_text(text,encoding='utf-8');print(json.dumps(summary,indent=2))
