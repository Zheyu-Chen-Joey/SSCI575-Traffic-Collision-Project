"""Publish negative/generalization evidence for targeted RF weighting."""
from pathlib import Path
import sys,json,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'.runtime'))
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=R/'04_outputs/cluster_targeted_optimization';mapping={'global_and_local':'cluster_weighting_v8_run2','local_only':'cluster_local_weighting_v8','weak_local_025':'cluster_conservative_v8_canonical'};phases={}
for label,folder in mapping.items():
 source=R/'06_reports/_qa'/folder;result=json.loads((source/'evaluation.json').read_text());assert not result['promote']and not result['legacy_evaluated'];dest=O/label;dest.mkdir(exist_ok=True)
 for file in source.iterdir():
  if file.suffix in ['.csv','.json']:shutil.copy2(file,dest/file.name)
 phases[label]=result
model=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';sha=hashlib.sha256(model.read_bytes()).hexdigest();assert sha=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357';source=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv';assert hashlib.sha256(source.read_bytes()).hexdigest()=='9f9645d7400b60c29e19c053cc5161df4b2c9c48de16963fa774a730c0b73779';assert len(list((R/'05_models').rglob('*.joblib')))==1
global_scores=pd.read_csv(O/'global_and_local/validation_scores.csv').set_index('candidate');local_scores=pd.read_csv(O/'local_only/validation_scores.csv').set_index('candidate');names=['Retained','Global + local','Local only','Weak local'];values=[global_scores.loc[0],global_scores.loc[3],local_scores.loc[3],local_scores.loc[1]];plot_table=pd.DataFrame([{'model':n,**v.to_dict()}for n,v in zip(names,values)]);plot_table.to_csv(O/'validation_comparison.csv',index=False);fig,axes=plt.subplots(2,3,figsize=(12,6.5));colors=['#537aa3','#bf6738','#55976d','#919191']
for ax,key,title in zip(axes.flat,['rmse','mae','p90_abs_error','error_gt200_count','moran_i'],['RMSE','MAE','90th percentile error','Cells with error >200','Residual Moran I']):
 v=plot_table[key].to_numpy();ax.bar(np.arange(4),v,color=colors);ax.set_xticks(np.arange(4),names,rotation=15,fontsize=8);ax.set_title(title);ax.set_ylim(0,max(v)*1.2)
 for i,x in enumerate(v):ax.text(i,x,f'{x:.3f}'if key=='moran_i'else(f'{x:.0f}'if key=='error_gt200_count'else f'{x:.2f}'),ha='center',va='bottom',fontsize=8)
axes.flat[-1].axis('off');axes.flat[-1].text(0,.8,'Development validation: 166 cells\nCandidates failed geographic stability checks.\nProduction model unchanged.\nNo new legacy-region comparison this round.',va='top',fontsize=10);fig.suptitle('Targeted weighting improves development metrics | not independent confirmation');fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(O/'validation_targeted_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
summary={'new_weight_configurations':7,'additional_conservative_check':'already tested weaklocal.25, frozen before its geographic check; canonical train-then-validation order','model_promoted':False,'legacy_region_evaluated_this_round':False,'training_large_error_cells':41,'FDR_significant_training_cells':21,'validation_reference':global_scores.loc[0].to_dict(),'validation_strong_local':local_scores.loc[3].to_dict(),'retained_metrics':{'rmse':80.62533236979074,'mae':53.05394497363826,'r2':.8183694418353425,'moran_i':.280837},'reason':'No candidate passed both per-region and mean regional stability gates. All diagnostic improvements are development evidence.','phases':phases};(O/'decision_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
verification={'model_sha256_unchanged':sha,'input_sha256_unchanged':hashlib.sha256(source.read_bytes()).hexdigest(),'production_model_count':1,'target_total':230536,'no_legacy_or_validation_targets_in_cluster_map':True,'weight_detector_nested_inside_each_outer_fit_subset':True,'cached_weights_only_when_exact_fit_grid_ids_match':True,'local_only_global_prediction_equivalence_smoke_check_passed':True,'legacy_targets_not_evaluated_this_round':True,'formal_model_unchanged':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(O/'verification.json').write_text(json.dumps(verification,indent=2))
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d['cluster_targeted_optimization']={'outputs':'04_outputs/cluster_targeted_optimization','report':'06_reports/RF_Cluster_Targeted_Optimization.docx','new_weight_configurations':7,'promoted':False,'legacy_evaluated':False,'validation_large_error_cells_before':8,'validation_large_error_cells_strong_local':6,'reason':'Failed geographic stability gates; retained current champion'};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'README.md';text=p.read_text(encoding='utf-8');note='''
## 针对大误差和空间聚集的优化

本轮仅用720个训练格的固定折外残差定位，发现41格绝对误差超过200起。局部Moran的9999次置换及BH校正后有21格显著，主要低估连通片位于I-110/Harbor Fwy/S Vermont Ave和Hollywood Blvd/Franklin Ave/Vine St一带；道路仅作定位参照，不作原因判断。见[聚集诊断图](04_outputs/cluster_targeted_optimization/training_residual_clusters.png)。

共测试7种训练误差加权配置，权重只由各外层训练子集内部的3折带间隔RF残差生成，预测不使用邻格真实事故数。较强局部加权在166格开发验证中将RMSE82.47→81.33、MAE52.07→51.62、大于200起误差格8→6、Moran I0.0554→0.0366；但连续地域留出未通过稳定性门槛，弱局部权重也未通过。正式模型保持不变，本轮未再次评估原227格。

详见[针对性优化报告](06_reports/RF_Cluster_Targeted_Optimization.docx)、[验证指标图](04_outputs/cluster_targeted_optimization/validation_targeted_comparison.png)与[嵌套验证记录](04_outputs/cluster_targeted_optimization)。这些是反复使用开发区得到的探索性证据，不是新独立测试。

'''
if '## 针对大误差和空间聚集的优化'not in text:text=text.replace('## 使用与复现',note+'## 使用与复现')
p.write_text(text,encoding='utf-8');print(json.dumps(verification))
