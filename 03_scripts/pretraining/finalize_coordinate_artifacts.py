"""Update public metadata to the verified coordinate RF champion."""
from pathlib import Path
import json,datetime
R=Path(__file__).resolve().parents[2];P=R/'04_outputs/rf_spatial_v5';C=P/'continued_optimization';ev=json.loads((P/'evaluation.json').read_text());change=json.loads((C/'improvement_summary.json').read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
latest={'date':'2026-11-07','new_configurations':18,'baseline_evaluations':3,'studies':['RF objective and regularization','fixed position rotation','coordinate RF convex blending'],'promoted':True,'selected':'50pct original plus50pct60degree-rotated local RF','evidence':'04_outputs/rf_spatial_v5/continued_optimization','legacy_evaluation':'exploratory reused227region; not independent confirmation'}
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d.update(version='coordinate_blended_spatial_RF_v7',method=latest['selected'],updated_utc=now,latest_refinement=latest)
 if rel.startswith('00_admin'):
  d['performance']=ev['spatial_v5'];d['limits']=['legacy and development regions repeatedly reused; adaptive selection','residual Moran remains significant','median absolute error slightly worsened despite lower RMSE/MAE/p90','historical snapshot and reporting completeness limitations']
 else:d.update(current_model_class='rf_coordinate_blend_model.CoordinateBlendForest',current_method=latest['selected'],legacy_metrics=ev['spatial_v5'],current_improvement=change)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for rel in ['02_config/spatial_extension_v5.json','02_config/feature_design.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8'));d['current_coordinate_blend_extension']={'user_authorized_position_features':True,'model_class':'rf_coordinate_blend_model.CoordinateBlendForest','original_input_columns_unchanged':18,'rotation_degrees':60,'rotated_weight':.5,'grid_size_m_unchanged':1000,'decision':'04_outputs/rf_spatial_v5/frozen_decision.json','validation':'04_outputs/rf_spatial_v5/continued_optimization','independent_confirmation':False};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
readme='''# SSCI575 交通事故空间负担预测 最优结果版

当前只保留一个模型：**原坐标与旋转坐标的局部加权RF组合**。研究City of Los Angeles 2017–2021公开记录的事故总数，采用固定1km网格。“最优”指已记录候选中的当前保留结果，不表示误差已消除或获得新的独立验证。

## 最终交付

- [最优版本报告 Word](06_reports/RF_Spatial_Extension_v5.docx)
- [最优结果包](06_reports/SSCI575_Project_Results.zip)
- [唯一保留模型](05_models/rf_spatial_v5/spatial_frozen_rf.joblib) · [输入契约](05_models/rf_spatial_v5/input_contract.json)
- [全市实际 预测与残差图](04_outputs/rf_spatial_v5/figures/03_full_city_comparison.png)
- [GIS预测 GPKG](04_outputs/rf_spatial_v5/spatial_predictions_1000.gpkg) · [CSV](04_outputs/rf_spatial_v5/spatial_predictions_1000.csv) · [GeoJSON](04_outputs/rf_spatial_v5/spatial_predictions_1000.geojson)
- [本轮完整验证记录](04_outputs/rf_spatial_v5/continued_optimization) · [清理清单](00_admin/cleanup_manifest.json)

## 当前结果

原227个评估格与开发地域已被多次查看，下列原区域比较属于探索性复用；后续研究方向和保留决策已受这些区域影响，不能称为新的独立测试。

| 原227格指标 | 前局部RF | 当前坐标组合RF |
|---|---:|---:|
| RMSE 起/格 | 83.51 | 81.02 |
| MAE 起/格 | 54.57 | 53.24 |
| R² | 0.8052 | 0.8166 |
| 残差 Moran I | 0.3134 | 0.2895 |
| 绝对误差90分位 起/格 | 149.26 | 140.50 |

RMSE下降2.98%，MAE下降2.44%。227格中130格绝对误差减小、97格增大；绝对误差中位数28.24→29.03略退步。Moran置换p=0.0001，残差仍显著聚集。

本轮测试10个损失/正则化配置、5个固定坐标旋转、3个RF组合权重，共18个新配置。每组研究另含现有模型对照。冻结组合为50%原坐标RF与50%60°旋转坐标RF。旋转只改变授权坐标输入的表达，1km分析网格和原始18个输入不变。

五折1km间隔空间CV的平均折RMSE95.59→92.90、MAE59.93→58.44；166格验证RMSE82.70→82.50、MAE52.82→52.35。开发区连续北侧留出RMSE44.25→43.69、MAE34.04→33.74；东侧RMSE140.90→135.92、MAE94.39→87.17。门槛在查看本轮原区域结果前冻结，但地域检查已被复用，改善仍需新数据确认。

前一轮37组细化配置未通过连续地域检查，见[历史优化记录](06_reports/RF_Refinement_20261107.txt)。当前研究保留其失败证据，不保存失败候选模型。

## 使用与复现

```powershell
$env:PYTHONUTF8='1'
python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 01_data/processed/pretraining_1km/model_table_1000_final.csv --output spatial_predictions_new.csv
python 03_scripts/pretraining/train_best_spatial_rf.py --execute-training --output reproduced_spatial_rf.joblib
python 03_scripts/pretraining/export_rf_spatial_v5.py
```

模型类型为CoordinateBlendForest，文件夹名称保持兼容。固定复现入口只拟合886个开发格，不用原227格拟合或选参，并拒绝覆盖现有文件。18个输入含EPSG:26911米制cx/cy，必须是固定网格中心，不能输入经纬度。预测输出须使用新路径。

每个坐标方向包含3个种子7/42/99的全局RF，各500树；另有10个局部RF，各200树。局部高斯带宽10km、锚点间距20km、最近3中心、有效样本数至少40，内部25%全局加75%局部。方向间再按50%组合。目标按设施密度加1的平方根缩放后拟合并还原。全部为RF，没有邻格真实事故数输入。

运行所需模块均在03_scripts/pretraining，包括pipeline_definition、rf_coverage_scaled_model、rf_spatial_model、rf_local_weighted_model、rf_rotated_local_model、rf_coordinate_blend_model。依赖见根目录及模型目录requirements.txt；Git LFS保存模型、GPKG、GeoJSON与ZIP，克隆后须完成LFS下载。

## 数据与边界

原点E345000/N3730000，EPSG:26911；1473个市界相交格，1113个合格格，230536条有效事故守恒，保留零事故格。1km为用户确定的实践尺度，不宣称唯一NSR最优，模型结果不用于反向选择尺度。

预测图中黑框为原227个评估格，其余有色格为开发区拟合结果。红色残差表示低估，蓝色表示高估。残差图保持上一版本的固定色标，未平滑残差或剔除困难格。

人口分配、土地缺失、2021记录数下降及快照时间一致性仍有限制。设施变量为混合信号/速度反馈标志密度代理，见[语义更正](06_reports/Signal_Source_Semantics_Clarification.txt)。未加入交通流量、限速、视距、rurality或HIN。

原始数据快照与来源保留；旧冠军保存冻结预测，模型实体只保留当前一个，旧版本可通过Git追溯。课程资料保留[最后PPT](06_reports/presentations/SSCI575_Presentation2_Downloads_Minimal_Final.pptx)与[讲稿](06_reports/SSCI575_Presentation2_Speaking_Script.docx)，其阶段性内容以当前报告为准。

Agent脚手架与本地运行环境不发布。精简ZIP包含必要数据、代码、报告和审计，不包含全部原始快照；完整来源核查使用完整仓库。
'''
(R/'README.md').write_text(readme,encoding='utf-8')
print('Updated current-model metadata and README')
