"""Publish support-guard results without promoting a failed geographic candidate."""
from pathlib import Path
import sys,json,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'.runtime'))
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
O=R/'04_outputs/support_protection_optimization';O.mkdir(exist_ok=True);sources={'hull_only':'supported_cluster_v8','distance_guard':'distance_supported_v8'};results={}
for name,folder in sources.items():
 source=R/'06_reports/_qa'/folder;result=json.loads((source/'evaluation.json').read_text());assert not result['promote']and not result['legacy_evaluated'];dest=O/name;dest.mkdir(exist_ok=True)
 for file in source.iterdir():
  if file.suffix in ['.csv','.json']:shutil.copy2(file,dest/file.name)
 results[name]=result
mp=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';source=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(mp)=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357';assert sha(source)=='9f9645d7400b60c29e19c053cc5161df4b2c9c48de16963fa774a730c0b73779';assert len(list((R/'05_models').rglob('*.joblib')))==1
scores=pd.read_csv(O/'distance_guard/geographic_scores.csv');pred=pd.read_csv(O/'distance_guard/geographic_predictions.csv');regions=['north20pct','east20pct','interior_6_6','interior_6_8'];comparison=[]
for name in regions:
 ref=scores[(scores.region==name)&(scores.candidate==0)].iloc[0];new=scores[(scores.region==name)&(scores.candidate==6)].iloc[0];comparison.append({'region':name,'n_fit':int(ref.n_fit),'n_eval':int(ref.n_eval),'reference_rmse':float(ref.rmse),'candidate_rmse':float(new.rmse),'reference_mae':float(ref.mae),'candidate_mae':float(new.mae),'reference_p90':float(ref.p90_abs_error),'candidate_p90':float(new.p90_abs_error),'reference_errors_gt200':int(ref.error_gt200_count),'candidate_errors_gt200':int(new.error_gt200_count),'reference_moran_i':float(ref.moran_i),'candidate_moran_i':float(new.moran_i),'active_gate_fraction':float(new.active_gate_fraction),'max_gate':float(new.max_gate)})
comparison=pd.DataFrame(comparison);comparison.to_csv(O/'regional_comparison.csv',index=False);boundary=comparison[comparison.region.isin(regions[:2])];assert np.allclose(boundary.reference_rmse,boundary.candidate_rmse,atol=1e-9,rtol=0)and(boundary.max_gate==0).all()
grid=gpd.read_file(R/'01_data/processed/pretraining_1km/grid_1000.gpkg')[['grid_id','geometry']];selected=pred[pred.candidate==6].merge(grid,on='grid_id',validate='many_to_one');selected=gpd.GeoDataFrame(selected,geometry='geometry',crs=26911);selected.to_file(O/'development_support_gates.gpkg',driver='GPKG');fig,axes=plt.subplots(2,2,figsize=(10,9));titles={'north20pct':'North boundary | correction =0','east20pct':'East boundary | correction =0','interior_6_6':'Interior I-110 area | 18 cells','interior_6_8':'Interior Hollywood area | 24 cells'}
for ax,name in zip(axes.flat,regions):
 grid.plot(ax=ax,color='#eeeeee');part=selected[selected.region==name];part.plot(column='gate',ax=ax,cmap='viridis',norm=Normalize(0,1),edgecolor='black',linewidth=.25);ax.set_title(titles[name],fontsize=10);ax.set_axis_off()
fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,1),cmap='viridis'),ax=list(axes.flat),fraction=.025,pad=.02,label='Correction weight | 0 = retained RF; 1 = full weighted RF');fig.suptitle('Development holdouts | geometry-only support gate, not residual magnitude');fig.subplots_adjust(top=.88,bottom=.03,left=.02,right=.88,wspace=.04,hspace=.12);fig.savefig(O/'development_support_gate_map.png',dpi=180,bbox_inches='tight');plt.close(fig)
val0=pd.read_csv(O/'hull_only/validation_scores.csv').set_index('candidate');val1=pd.read_csv(O/'distance_guard/validation_scores.csv').set_index('candidate');data=pd.DataFrame([{'model':'Retained','rmse':val0.loc[0].rmse,'p90':val0.loc[0].p90_abs_error,'large':val0.loc[0].error_gt200_count,'moran':val0.loc[0].moran_i},{'model':'Hull guard','rmse':val0.loc[4].rmse,'p90':val0.loc[4].p90_abs_error,'large':val0.loc[4].error_gt200_count,'moran':val0.loc[4].moran_i},{'model':'Distance guard','rmse':val1.loc[6].rmse,'p90':val1.loc[6].p90_abs_error,'large':val1.loc[6].error_gt200_count,'moran':val1.loc[6].moran_i}]);data.to_csv(O/'validation_comparison.csv',index=False);fig,axes=plt.subplots(1,4,figsize=(12,3.6))
for ax,key,title in zip(axes,['rmse','p90','large','moran'],['Validation RMSE','90th percentile','Errors >200','Residual Moran I']):
 values=data[key].to_numpy();ax.bar(data.model,values,color=['#537aa3','#bf6738','#55976d']);ax.set_title(title,fontsize=10);ax.tick_params(axis='x',rotation=15,labelsize=8);ax.set_ylim(0,values.max()*1.2)
 for i,x in enumerate(values):ax.text(i,x,f'{x:.3f}'if key=='moran'else(f'{x:.0f}'if key=='large'else f'{x:.2f}'),ha='center',va='bottom',fontsize=8)
fig.suptitle('Development validation improves | internal geographic gates still fail',fontsize=11);fig.tight_layout();fig.savefig(O/'validation_support_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
gates=json.loads((O/'distance_guard/geographic_gates.json').read_text());representative=next(x for x in gates if x['candidate']==6);summary={'new_configurations':12,'production_model_promoted':False,'legacy_evaluated_this_round':False,'outer_boundary_decline_eliminated_by_fallback':True,'outer_extrapolation_improved':False,'all_interior_gates_pass':False,'representative_not_adopted_config':{'hull_taper_m':2000,'distance_taper_start_m':2000,'max_training_distance_m':5000,'correction_strength':1},'reference_interior':representative['reference_interior'],'candidate_interior':representative['candidate_interior'],'validation_reference':val1.loc[0].to_dict(),'validation_candidate':val1.loc[6].to_dict(),'selection_limit':'All regions are repeatedly used developer checks. Interior blocks chosen from prior trainingOOF diagnostics. No independent confirmation.'};(O/'decision_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
verification={'model_sha256_unchanged':sha(mp),'input_sha256_unchanged':sha(source),'model_count':1,'boundary_gates_all_zero':True,'boundary_reference_predictions_equal_candidate':True,'legacy_region_not_evaluated_this_round':True,'no_source_snapshots_changed':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(O/'verification.json').write_text(json.dumps(verification,indent=2))
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d['support_protection_optimization']={'report':'06_reports/RF_Support_Protection_Optimization.docx','outputs':'04_outputs/support_protection_optimization','new_configurations':12,'promoted':False,'boundary_decline_removed_by_fallback':True,'interior_joint_goals_pass':False,'legacy_evaluated':False};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'README.md';text=p.read_text(encoding='utf-8');note='''
## 连续地域保护试验

本轮测试12种几何支持保护。训练位置凸包外回退到原RF，使北侧与东侧连续留出预测与对照相同；这表示避免候选退步，不表示提高外推准确度。再加入最近训练距离衰减后，166格验证RMSE82.47→81.04，大于200起误差格8→6、Moran I0.0554→0.0381。

新增内部5km留出块6_6与6_8分别覆盖I-110和Hollywood训练误差簇；距离保护候选在合并42格中的RMSE187.28→188.43、MAE146.79→148.10、Moran I0.1746→0.1796，未通过联合门槛。正式模型不变，本轮未再次评估原227格。详见[地域保护报告](06_reports/RF_Support_Protection_Optimization.docx)、[开发留出保护图](04_outputs/support_protection_optimization/development_support_gate_map.png)及[全部证据](04_outputs/support_protection_optimization)。

'''
if '## 连续地域保护试验'not in text:text=text.replace('## 使用与复现',note+'## 使用与复现')
p.write_text(text,encoding='utf-8');print(json.dumps(summary,indent=2))
