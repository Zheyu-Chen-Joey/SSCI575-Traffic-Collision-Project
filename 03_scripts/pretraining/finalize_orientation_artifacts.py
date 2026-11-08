"""Update metadata and README for the verified three-direction RF."""
from pathlib import Path
import json,csv,datetime
R=Path(__file__).resolve().parents[2];P=R/'04_outputs/rf_spatial_v5';C=P/'orientation_optimization';ev=json.loads((P/'evaluation.json').read_text());summary=json.loads((C/'improvement_summary.json').read_text());decision=json.loads((P/'frozen_decision.json').read_text());scores=list(csv.DictReader((P/'comparison_metrics.csv').open()));old=next(x for x in scores if x['model']=='Previous coordinate RF');new=next(x for x in scores if x['model']=='Current best RF');latest={'new_configurations':12,'baseline_evaluations':1,'promoted':True,'selected':'25pct0degree plus25pct45degree plus50pct60degree local RF','evidence':'04_outputs/rf_spatial_v5/orientation_optimization','legacy_status':'adaptive exploratory reuse; not independent confirmation'}
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d.update(version='multi_orientation_RF_v8',method=latest['selected'],updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),latest_refinement=latest,orientation_settings=decision['orientation_settings'])
 if rel.startswith('00_admin'):d.update(performance=ev['spatial_v5'],limits=['legacy and development regions repeatedly reused; adaptive selection','residual Moran remains significant','improvement intervals include zero','median absolute error and positive bias worsened','covariate snapshot and reporting completeness limitations'])
 else:d.update(current_model_class='rf_orientation_ensemble.OrientationEnsembleForest',current_method=latest['selected'],legacy_metrics=ev['spatial_v5'],current_improvement=summary)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for rel in ['02_config/feature_design.json','02_config/spatial_extension_v5.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8'));d['previous_coordinate_blend_extension']=d.pop('current_coordinate_blend_extension',{});d['current_orientation_extension']={'model_class':'rf_orientation_ensemble.OrientationEnsembleForest','original_input_count':18,'grid_side_m':1000,**decision['orientation_settings'],'decision':'04_outputs/rf_spatial_v5/frozen_decision.json','validation':'04_outputs/rf_spatial_v5/orientation_optimization','independent_confirmation':False};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
readme='''# SSCI575 交通事故空间负担预测 最优结果版

当前只保留一个生产模型：**0度 45度 60度坐标表达的局部加权随机森林组合**，权重依次为25%、25%、50%。研究City of Los Angeles 2017–2021公开记录的事故总数，采用固定1km网格。当前结果是适应性研究中的保留方案，不代表获得新的独立验证。

## 最终交付

- [当前报告 Word](06_reports/RF_Spatial_Extension_v5.docx) · [结果包](06_reports/SSCI575_Project_Results.zip)
- [唯一生产模型](05_models/rf_spatial_v5/spatial_frozen_rf.joblib) · [输入契约](05_models/rf_spatial_v5/input_contract.json)
- [全市实际 预测与残差图](04_outputs/rf_spatial_v5/figures/03_full_city_comparison.png) · [前后残差图](04_outputs/rf_spatial_v5/figures/02_legacy_residual_comparison.png)
- [GIS GPKG](04_outputs/rf_spatial_v5/spatial_predictions_1000.gpkg) · [CSV](04_outputs/rf_spatial_v5/spatial_predictions_1000.csv) · [GeoJSON](04_outputs/rf_spatial_v5/spatial_predictions_1000.geojson)
- [本轮验证记录](04_outputs/rf_spatial_v5/orientation_optimization) · [上轮记录](04_outputs/rf_spatial_v5/continued_optimization)

## 当前结果

原227个评估格与开发地域已被反复查看，下表属于探索性复用。研究方向和保留决策已受这些区域影响，不能称为新的独立测试。

| 原227格指标 | 前两方向RF | 当前三方向RF |
|---|---:|---:|
'''
for label,key,digits in [('RMSE 起/格','rmse',2),('MAE 起/格','mae',2),('R²','r2',4),('残差 Moran I','moran_i',4),('绝对误差90分位 起/格','p90_abs_error',2)]:readme+=f"| {label} | {float(old[key]):.{digits}f} | {float(new[key]):.{digits}f} |\n"
readme+='''
RMSE下降0.49%，MAE下降0.35%，123格绝对误差下降、104格上升。收益很小：中位绝对误差29.03→29.69、平均预测偏差9.79→10.29均略退步。空间块重采样的RMSE与MAE改善区间均包含0。残差仍显著聚集，Moran置换p=0.0001。

本轮预设12种新方向组合与1项当前模型对照。带1km间隔的五折平均RMSE92.9041→92.2924，MAE58.4437→58.0446。166格验证RMSE82.4950→82.4728，MAE52.3508→52.0701。北侧连续留出RMSE43.6904→43.4298、MAE33.7376→33.6188；东侧RMSE135.9205→134.7356、MAE87.1665→84.7845。所有门槛在本轮原区域比较前冻结，但这些空间检查已复用，属于开发证据。

## 使用与复现

```powershell
$env:PYTHONUTF8='1'
python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 01_data/processed/pretraining_1km/model_table_1000_final.csv --output spatial_predictions_new.csv
python 03_scripts/pretraining/train_best_spatial_rf.py --execute-training --output reproduced_spatial_rf.joblib
python 03_scripts/pretraining/export_rf_spatial_v5.py
```

当前模型类型OrientationEnsembleForest，仍使用18字段，含EPSG:26911米制固定1km格中心cx/cy。坐标旋转只改变预测变量表达，不改变归格、距离、原点或事故记录。固定复现仅拟合886个开发格，不用原227格拟合或选参，拒绝覆盖已有文件。

每个方向由3个种子7/42/99、各500树的全局RF与10个各200树的局部RF组成；每方向内部25%全局加75%局部。高斯带宽10km、锚点间距20km、最近3中心、有效样本数至少40。目标按设施密度加1的平方根缩放并还原。所有组件均为RF，没有邻格真实事故数作为预测输入。

所需代码在03_scripts/pretraining，包含pipeline_definition、rf_coverage_scaled_model、rf_spatial_model、rf_local_weighted_model、rf_rotated_local_model、rf_orientation_ensemble及固定训练/预测入口。依赖见requirements.txt与模型目录environment.json。Git LFS存模型、GPKG、GeoJSON及ZIP，克隆后须下载LFS对象。旧冠军实体不再重复保留，以哈希校验的冻结预测及Git历史追溯。

## 数据与限制

原点E345000/N3730000，EPSG:26911；1473个市界相交格，1113个合格格，230536条有效事故守恒，保留零事故格。1km为用户确定的实践尺度，不宣称唯一NSR最优，模型结果不用于反向选择尺度。

全市图黑框为原227个评估格，其余有色格为开发区拟合结果。红残差表示低估，蓝表示高估。固定残差界限保持原区域±341.46、全市±517.82；未平滑残差或删除困难格。全图不能当作独立测试结果。

人口面积分配、土地缺失、2021记录下降和快照年份仍有限制。设施变量是混合信号及速度反馈标志点密度代理，见[语义更正](06_reports/Signal_Source_Semantics_Clarification.txt)。未加入HIN、交通流量、限速、视距或rurality。结论仅用于历史记录负担拟合，不是未来风险或因果效应。

必要尺度说明见[网格决策](06_reports/grid_decision.md)；前37组失败实验见[历史记录](06_reports/RF_Refinement_20261107.txt)。[最后PPT](06_reports/presentations/SSCI575_Presentation2_Downloads_Minimal_Final.pptx)与[讲稿](06_reports/SSCI575_Presentation2_Speaking_Script.docx)为阶段性资料，以当前模型报告为准。

原始数据快照不覆盖。Agent脚手架、本地环境及临时QA不发布。精简结果包包含必要数据、模型、代码、报告和验证记录，不包含全部原始快照；来源核查使用完整仓库。
'''
(R/'README.md').write_text(readme,encoding='utf-8');print('Updated current orientation-model metadata')
