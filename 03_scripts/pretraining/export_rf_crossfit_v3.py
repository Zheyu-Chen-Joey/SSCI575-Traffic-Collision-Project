"""Independent checks and transparent diagnostics of the RF-only cross-fit experiment."""
import sys,pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,geopandas as gpd,joblib
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from pipeline_definition import make_pipeline,feature_names
from rf_residual_model import CrossFittedResidualForest
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
O=ROOT/'04_outputs/rf_crossfit_v3';M=ROOT/'05_models/rf_crossfit_v3';F=O/'figures';F.mkdir(exist_ok=True);ev=json.loads((O/'evaluation.json').read_text());pr=json.loads((O/'protocol.json').read_text());folds=json.loads((O/'nested_fold_ids.json').read_text());df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');tr=df[df.eligible&(df.split=='train')];va=df[df.eligible&(df.split=='validation')];dev=pd.concat([tr,va],ignore_index=True);test=df[df.eligible&(df.split=='test')];cols=feature_names('enhanced');allpred=pd.read_csv(O/'all_predictions.csv');assert hashlib.sha256((ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv').read_bytes()).hexdigest()==pr['input_sha256']
for fold in folds:
 a=df[df.grid_id.isin(fold['fit_ids'])];b=df[df.grid_id.isin(fold['evaluation_ids'])];assert set(a.split)=={'train'}and set(b.split)=={'train'};assert not(set(a.block_id)&set(b.block_id))
 for inner in fold['inner']:
  ia=set(inner['fit_ids']);ib=set(inner['oof_ids']);assert ia|ib==set(fold['fit_ids']);assert not ia&ib;assert not(ia|ib)&set(fold['evaluation_ids'])
model=joblib.load(M/'v3_frozen_rf.joblib');old=joblib.load(ROOT/'05_models/rf_project_v1/enhanced_optimized_rf.joblib');assert isinstance(model,CrossFittedResidualForest)
for fit in [model.base_,model.correction_]:assert all(np.isclose(t.tree_.weighted_n_node_samples[0],886)for t in fit.named_steps['rf'].estimators_)
a,b=model.crossfit_splits_[0];assert not(set(dev.iloc[a].block_id)&set(dev.iloc[b].block_id));check=make_pipeline('enhanced').set_params(rf__n_jobs=4,**pr['base_params']);check.fit(dev.iloc[a][cols],dev.iloc[a].count_2017_2021);assert np.allclose(check.predict(dev.iloc[b][cols]),model.oof_base_prediction_[b])
for key,m in [('v1',old),('v3',model)]:
 p=m.predict(test[cols]);s=ev[key]['legacy_evaluation'];assert np.isclose(s['rmse'],np.sqrt(mean_squared_error(test.count_2017_2021,p)));assert np.isclose(s['mae'],mean_absolute_error(test.count_2017_2021,p));assert np.isclose(s['r2'],r2_score(test.count_2017_2021,p));out=allpred[allpred.model==key];assert len(out)==1473 and np.isfinite(out.predicted).all();assert np.allclose(m.predict(df[cols]),out.predicted);assert np.allclose(out.residual,out.count_2017_2021-out.predicted)
oldrows=allpred[(allpred.model=='v1')&(allpred.prediction_role=='legacy_evaluation_reuse')].copy();oldrows['abs_error']=oldrows.residual.abs();oldrows['squared_error']=oldrows.residual**2;top=oldrows.nlargest(25,'abs_error').merge(df[['grid_id',*cols]],on='grid_id',validate='one_to_one');top.to_csv(O/'high_residual_legacy_cells.csv',index=False);top10=int(np.ceil(len(oldrows)*.1));share=float(oldrows.nlargest(top10,'squared_error').squared_error.sum()/oldrows.squared_error.sum());bias_by_split=[]
for (m,split),a in allpred[allpred.eligible].groupby(['model','split']):bias_by_split.append({'model':m,'split':split,'n':len(a),'mean_observed':float(a.count_2017_2021.mean()),'mean_predicted':float(a.predicted.mean()),'mean_observed_minus_predicted':float(a.residual.mean()),'rmse_descriptive':float(np.sqrt((a.residual**2).mean()))})
pd.DataFrame(bias_by_split).to_csv(O/'split_error_diagnostics.csv',index=False)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.dpi':180});grid=gpd.read_file(ROOT/'01_data/processed/pretraining_1km/grid_1000.gpkg');g=grid[['grid_id','geometry']].merge(df,on='grid_id');
for key in ['v1','v3']:
 p=allpred[allpred.model==key];g=g.merge(p[['grid_id','predicted','residual']].rename(columns={'predicted':key+'_pred','residual':key+'_resid'}),on='grid_id',validate='one_to_one')
g['prediction_role']=np.where(~g.eligible,'boundary_extrapolation',np.where(g.split=='test','legacy_evaluation_reuse','development_fit'));g.to_file(O/'grid_predictions_comparison_1000.gpkg',driver='GPKG');g.drop(columns='geometry').to_csv(O/'grid_predictions_comparison_1000.csv',index=False)
for mode in ['legacy','full_city']:
 d=g[g.eligible&(g.split=='test')]if mode=='legacy'else g[g.eligible];limit=max(d.v1_resid.abs().max(),d.v3_resid.abs().max());fig,axes=plt.subplots(1,2,figsize=(10,7))
 for ax,col,title in zip(axes,['v1_resid','v3_resid'],['Original RF retained','Cross-fitted RF correction experiment']):
  g.plot(ax=ax,color='#eeeeee');d.plot(column=col,ax=ax,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),legend=True,legend_kwds={'shrink':.45});ax.set_axis_off();ax.set_title(title,fontsize=11)
  if mode=='full_city':g[g.eligible&(g.split=='test')].boundary.plot(ax=ax,color='black',linewidth=.3)
 fig.suptitle('Legacy evaluation cells | same residual color scale'if mode=='legacy'else'Full city overview | black outlines mark legacy evaluation cells\nOther colored cells are development fitted residuals, not independent evaluation',fontsize=11);fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(F/f'{mode}_residual_comparison.png',bbox_inches='tight');plt.close(fig)
vs=pd.read_csv(O/'validation_scores.csv');rows=[]
for key,label in [('v1','Original'),('v3','Cross-fit')]:rows.append({'model':label,**ev[key]['legacy_evaluation'],'moran':ev[key]['moran']['I']})
fig,axes=plt.subplots(1,3,figsize=(10,3.5))
for ax,c,title in zip(axes,['rmse','mae','moran'],['Legacy RMSE','Legacy MAE','Legacy residual Moran I']):
 vals=[r[c]for r in rows];ax.bar(['Original','Cross-fit'],vals,color=['#537aa3','#bf6738']);ax.set_title(title)
 for i,v in enumerate(vals):ax.text(i,v,f'{v:.3f}'if c=='moran'else f'{v:.2f}',ha='center',va='bottom')
fig.suptitle('Exploratory reuse of previously examined region | lower is preferred here');fig.tight_layout();fig.savefig(F/'metric_comparison.png',bbox_inches='tight');plt.close(fig)
cv=pd.read_csv(O/'cv_scores.csv');ci=int(ev['decision']['selected_candidate']);best=vs[vs.candidate==ci].iloc[0];base=vs[vs.candidate==0].iloc[0];report=f'''RF折外残差校正优化复核

结论：进行了72组RF残差校正配置及原模型对照。开发区改善未迁移到旧测试区，不替换正式v1模型。不根据旧测试区继续调参。

方法：保持原16个输入字段和1km网格。基础森林500树深度8；校正森林300树，深度3/5/8、叶最少8/15/30、max_features0.7/1.0，校正强度0.25/0.5/0.75/1.0。二者均为RF，但属于双阶段RF组合，是原单森林方案的探索性扩展。
在训练720格做外层5折，每个外层训练部分另做内层3折，仅用内层折外残差拟合校正森林。外层评估格的目标既不进入基础森林，也不进入校正残差标签。坐标只用于诊断权重，不是特征；不使用邻格真实事故数、HIN或旧测试残差；不平滑真实残差。
本次CV为开发区模型选择诊断，基础配置来自早期调参且已查看旧结果，因此不能把它包装成全新无偏验证。
联合门槛：训练折外RMSE、MAE和绝对Moran均不劣于对照，再最多4候选进入验证区。验证RMSE必须下降且MAE、绝对Moran不得升高。候选{ci}在旧测试评估前冻结。最终886开发格上重新生成5折残差标签，拟合两森林，旧测试227格从不拟合。

验证区166格：
原RF RMSE={base.rmse:.2f},MAE={base.mae:.2f},R²={base.r2:.3f},残差Moran I={base.moran_i:.4f}
新方案 RMSE={best.rmse:.2f},MAE={best.mae:.2f},R²={best.r2:.3f},残差Moran I={best.moran_i:.4f}

旧测试区探索性复用：
原RF RMSE={ev['v1']['legacy_evaluation']['rmse']:.2f},MAE={ev['v1']['legacy_evaluation']['mae']:.2f},R²={ev['v1']['legacy_evaluation']['r2']:.3f},Moran I={ev['v1']['moran']['I']:.4f}
新方案 RMSE={ev['v3']['legacy_evaluation']['rmse']:.2f},MAE={ev['v3']['legacy_evaluation']['mae']:.2f},R²={ev['v3']['legacy_evaluation']['r2']:.3f},Moran I={ev['v3']['moran']['I']:.4f}
两个Moran置换p均为0.0001（9999次）。新方案增加了旧测试区高估偏差，未降低该区误差或聚集。因此开发集改善不足以支持替换正式模型。旧测试区自v1起已被查看，不能重新声称独立验证。

误差诊断：原模型旧测试区平方误差的{share:.1%}集中在绝对误差最高的{top10}个格。完整高残差前25格清单保存在high_residual_legacy_cells.csv，含实际、预测、残差、位置及现有解释变量，供核对源数据与局部道路情况，不能据此删格提高指标。区域平均误差见split_error_diagnostics.csv；开发区为拟合误差，不是独立泛化评估。

解释与下一步：现有输入下，验证区学到的残差规律未稳定转移；继续增加树数或深度无法保证改善。优先核实高残差格道路/信号/人口与事故定位，再考虑具有一致时段、覆盖充分的交通暴露或其他道路特征，或单独声明位置趋势扩展。没有新数据，本轮不能证明误差不可再降低，也不能保证继续调参一定有效。任何新设计须记录变化，并争取新的空间或时间外部验证。

文件：04_outputs/rf_crossfit_v3包含协议、嵌套折ID、完整CV与验证分数、冻结决定、预测、GIS、地图及校验；05_models/rf_crossfit_v3保留实验模型。正式模型仍为05_models/rf_project_v1/enhanced_optimized_rf.joblib。加载实验模型前需将03_scripts/pretraining加入模块路径，以加载rf_residual_model.py。
官方方法参考：https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.cross_val_predict.html 。独立重载校验：python 03_scripts/pretraining/export_rf_crossfit_v3.py。
''';(ROOT/'06_reports/RF_Crossfit_Residual_Optimization_v3.txt').write_text(report,encoding='utf-8');verification={'status':'pass','input_hash_unchanged':True,'all_outer_and_inner_ids_train_only':True,'outer_evaluation_ids_excluded_from_inner_residual_labels':True,'final_crossfit_one_fold_independently_refitted_and_matched':True,'both_forests_fit886development_rows':True,'saved_model_prediction_metrics_reproduced':True,'legacy_test_is_exploratory_reuse':True,'formal_primary_model_unchanged':True,'top10pct_cells_squared_error_share':share};(O/'verification.json').write_text(json.dumps(verification,indent=2));print(report)
