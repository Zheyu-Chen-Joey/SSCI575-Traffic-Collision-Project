# SSCI575 Traffic Collision Project

## 当前版本 空间位置扩展 RF v5

研究 City of Los Angeles 2017–2021 年公开记录的交通事故负担，使用固定1km网格。当前扩展候选在原16字段之外加入已获用户授权的网格中心坐标，使用3个随机种子的RF平均。原模型及全部优化实验保留作对照。

### 最新交付

- [空间扩展与验证报告 Word](06_reports/RF_Spatial_Extension_v5.docx)
- [最新结果包](06_reports/SSCI575_Project_Results.zip)
- [操作与复现说明](06_reports/PROJECT_DELIVERABLES.txt)
- [全市实际值 预测值与残差图](04_outputs/rf_spatial_v5/figures/03_full_city_comparison.png)
- [同参数坐标消融](04_outputs/rf_spatial_v5/figures/04_coordinate_ablation.png)
- [当前空间模型](05_models/rf_spatial_v5/spatial_frozen_rf.joblib)
- [模型输入契约](05_models/rf_spatial_v5/input_contract.json)
- [GIS预测结果](04_outputs/rf_spatial_v5/spatial_predictions_1000.gpkg)

### 当前比较结果

下表为已多次查看的原227个测试格上的**探索性复用比较**，不是全新独立验证。

| 模型 | RMSE 起/格 | MAE 起/格 | R² | 残差 Moran I |
|---|---:|---:|---:|---:|
| 原RF v1 | 97.98 | 64.96 | 0.732 | 0.2996 |
| 保守RF组合 v4b | 97.53 | 63.84 | 0.734 | 0.3189 |
| 同参数无坐标对照 | 95.49 | 61.90 | 0.745 | 0.3259 |
| 空间扩展 v5 | 92.89 | 59.86 | 0.759 | 0.3317 |

v5较原RF的RMSE降低5.20%、MAE降低7.86%，但残差空间聚集没有下降。相同参数下，加入坐标的模型在实际1km网格间隔的训练折外验证中退步（RMSE96.43→99.61）；开发区东侧地域留出改善，北侧略有退步。不可把当前误差下降解释为普遍空间泛化改善。需要新的时空外部验证。

### 运行当前离线模型

在项目根目录、已安装记录依赖的Python环境中运行：

```powershell
$env:PYTHONUTF8='1'
python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 01_data/processed/pretraining_1km/model_table_1000_final.csv --output spatial_predictions_new.csv
```

输出路径须为新文件。输入必须包含原16个聚合字段及cx/cy，后两列为EPSG:26911固定1km网格中心的米制坐标，不是经纬度。该模型估计历史记录事故总数，不预测未来年份。环境版本见05_models/rf_spatial_v5/environment.json；依赖列表见05_models/rf_project_v1/requirements.txt。Git LFS保存模型、GPKG、GeoJSON与ZIP，克隆后需完成LFS下载。

### 验证与数据契约

- 固定EPSG:26911，原点E345000/N3730000；1473个市界相交格，1113个合格格；230536条有效事故守恒，零事故格保留。
- 训练/验证/原测试为720/166/227格。最终空间模型只拟合886个开发格。
- 选模采用开发区空间CV及验证；实际完整方格距离不超过1km的训练格从缓冲CV中排除。没有邻格真实事故数、HIN或测试目标预测变量。
- [训练协议](04_outputs/rf_spatial_v5/protocol.json)、[同参数消融](04_outputs/rf_spatial_v5/matched_coordinate_ablation.csv)、[地域留出](04_outputs/rf_spatial_v5/geographic_transfer_checks.csv)、[独立校验](04_outputs/rf_spatial_v5/verification.json)完整保留。
- 无数据不冒充0。人口面积分配、土地利用缺失、2021记录数下降与历史快照一致性仍有限制。
- 信号字段实际为含速度反馈标志的混合设施点密度代理，见[语义更正](06_reports/Signal_Source_Semantics_Clarification.txt)。不能称为纯历史信号交叉口清单，也不作因果解释。
- 1km为用户选择的实践尺度，不宣称唯一NSR最优。交通流量、限速、视距及人口衍生rurality未纳入。

### 历史与审计

原方案训练报告保留在06_reports/SSCI575_Final_Project_Report.docx；v1、v2、v3、v4、v4b及位置残差分支均保留，不用新的更好分数覆盖失败实验。旧v1结果包保存在06_reports/archive/SSCI575_Project_Results_v1.zip。当前ZIP以v5为主，不包含全部原始下载或本地运行环境；完整重现与原始快照校验请使用完整仓库及其数据。

Agent脚手架、本地.runtime和临时检查文件不发布。
