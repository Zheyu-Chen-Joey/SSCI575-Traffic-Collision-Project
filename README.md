# SSCI575 交通事故空间负担预测 最优结果版

当前只保留一个模型：**空间位置扩展RF v5**。这里的“最优”指已记录候选中RMSE和MAE最低，不表示残差空间聚集最小。研究范围为City of Los Angeles，目标为2017–2021公开记录的事故总数，工作尺度为固定1km网格。

## 最终交付

- [最优版本报告 Word](06_reports/RF_Spatial_Extension_v5.docx)
- [最优结果包](06_reports/SSCI575_Project_Results.zip)
- [唯一保留模型](05_models/rf_spatial_v5/spatial_frozen_rf.joblib)
- [输入契约](05_models/rf_spatial_v5/input_contract.json)
- [全市实际 预测与残差图](04_outputs/rf_spatial_v5/figures/03_full_city_comparison.png)
- [GIS预测 GPKG](04_outputs/rf_spatial_v5/spatial_predictions_1000.gpkg) · [CSV](04_outputs/rf_spatial_v5/spatial_predictions_1000.csv) · [GeoJSON](04_outputs/rf_spatial_v5/spatial_predictions_1000.geojson)
- [清理清单与检查](00_admin/cleanup_manifest.json)

## 结果及边界

原227个评估格已被多次查看，以下属于探索性复用比较，不能称为全新独立验证。

| 指标 | 当前空间RF |
|---|---:|
| RMSE 起/格 | 92.89 |
| MAE 起/格 | 59.86 |
| R² | 0.759 |
| 残差 Moran I | 0.3317 |

相对原RF，RMSE降低5.20%、MAE降低7.86%，但残差空间聚集没有下降。同参数的1km真实网格间隔验证中，加入坐标后RMSE由96.43升至99.61；开发区东侧留出改善，北侧略有退步。它是当前覆盖内的空间扩展候选，不保证通用的时空外推，也不作因果解释。

旧候选模型、中间优化目录、重复报告/PPT与临时检查文件已清理。为支撑报告中的比较，保留少量冻结参考预测、验证CSV及简要优化审计摘要；不再依赖旧模型实体。原始数据快照与来源保留。旧版本可在正常Git历史中追溯。

## 使用与复现

在项目根目录、已安装记录依赖的Python环境中运行：

```powershell
$env:PYTHONUTF8='1'
python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 01_data/processed/pretraining_1km/model_table_1000_final.csv --output spatial_predictions_new.csv
python 03_scripts/pretraining/export_rf_spatial_v5.py
```

输入为原16个聚合变量及cx/cy，共18字段；坐标必须是EPSG:26911米制固定1km格中心，不能使用经纬度。预测输出须为新路径。环境与依赖见05_models/rf_spatial_v5/environment.json、requirements.txt和根目录requirements.txt。Git LFS保存模型、GPKG、GeoJSON和ZIP，克隆后需完成LFS下载。

仅按冻结参数复现最终模型，不再搜索旧候选：

```powershell
python 03_scripts/pretraining/train_best_spatial_rf.py --execute-training --output reproduced_spatial_rf.joblib
```

该入口只拟合886个开发格，不使用227个原评估格拟合或选参，也不覆盖现有模型。不要把重复评估旧区域当作新的独立验证。

## 数据与方法

原点E345000/N3730000，EPSG:26911；1473个市界相交格，1113个合格格，230536条有效事故守恒并保留零事故格。输入表位于01_data/processed/pretraining_1km/model_table_1000_final.csv。1km为已确定的实践尺度，不宣称唯一NSR最优。

原始快照、数据来源、清理QA和必要尺度诊断保留，以便核查数据完整性。人口面积分配、土地缺失、2021记录数下降及快照时间一致性仍有限制。设施变量是混合信号/速度反馈标志点的密度代理，见[语义更正](06_reports/Signal_Source_Semantics_Clarification.txt)。没有加入邻格真实事故数、HIN、交通流量、限速、视距或rurality。

保留的模型所用模块为pipeline_definition.py、rf_coverage_scaled_model.py和rf_spatial_model.py；导出脚本现在使用唯一模型加哈希核验的冻结参考预测，清理后仍可运行。

课程资料只保留[最后修改的PPT](06_reports/presentations/SSCI575_Presentation2_Downloads_Minimal_Final.pptx)和[对应讲稿](06_reports/SSCI575_Presentation2_Speaking_Script.docx)，其阶段性内容以最终模型报告为准。

Agent脚手架、本地运行环境与临时检查文件不发布。精简ZIP不包含全部原始快照或本地环境，完整原始数据核查使用完整仓库。
