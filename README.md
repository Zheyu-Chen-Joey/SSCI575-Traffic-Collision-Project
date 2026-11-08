# SSCI575 交通事故空间负担预测 最优结果版

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
| RMSE 起/格 | 81.02 | 80.63 |
| MAE 起/格 | 53.24 | 53.05 |
| R² | 0.8166 | 0.8184 |
| 残差 Moran I | 0.2895 | 0.2808 |
| 绝对误差90分位 起/格 | 140.50 | 138.21 |

RMSE下降0.49%，MAE下降0.35%，123格绝对误差下降、104格上升。收益很小：中位绝对误差29.03→29.69、平均预测偏差9.79→10.29均略退步。空间块重采样的RMSE与MAE改善区间均包含0。残差仍显著聚集，Moran置换p=0.0001。

本轮预设12种新方向组合与1项当前模型对照。带1km间隔的五折平均RMSE92.9041→92.2924，MAE58.4437→58.0446。166格验证RMSE82.4950→82.4728，MAE52.3508→52.0701。北侧连续留出RMSE43.6904→43.4298、MAE33.7376→33.6188；东侧RMSE135.9205→134.7356、MAE87.1665→84.7845。所有门槛在本轮原区域比较前冻结，但这些空间检查已复用，属于开发证据。


追加8种树结构配置均未通过完整接受门槛，当前模型与地图保持不变。见[树结构验证记录](06_reports/RF_Tree_Structure_Validation.txt)。


## 高误差区域排查与纠错

已完成[高残差调查报告](06_reports/RF_Residual_Hotspots_Investigation.docx)及[诊断地图与逐格证据](04_outputs/residual_investigation)。独立重算事故、设施点、交叉口、道路与人口聚合未发现计数或拼接差异；土地利用50644个下载对象匹配ID快照。原227格中最差23格贡献64.7%的平方误差。训练集无土地利用全缺测格，原评估区有14格；机场用地主导训练格仅6个。两项均是解释线索，不能作为因果结论。

训练缺测模拟虽改善压力情景，但真实原区域RMSE80.63→81.84、MAE53.05→53.71，未替换当前模型。现有预测接口与GIS新增土地利用缺测、覆盖不足、机场零居住人口代理的输入提示，共标记45个合格格。提示不是置信区间，未标记也不保证准确。未修改事故数、补造土地利用或人工修正高误差格的预测。


追加6种缩放配置未通过完整接受门槛，当前模型与地图保持不变。见[缩放验证记录](06_reports/RF_Scaling_Validation.txt)。


追加3种缩放组合配置未通过完整接受门槛，当前模型与地图保持不变。见[缩放组合验证记录](06_reports/RF_Scaling_Blend_Validation.txt)。


双缩放RF候选在原227格探索性比较中RMSE78.67、MAE51.80、R²0.8271，均改善；但绝对误差90分位138.21→143.42（增加3.77%），超过预设2%上限，未替换当前生产模型。见[平均与尾部误差权衡图](04_outputs/rf_spatial_v5/scaling_blend_v8/error_tradeoff.png)。


## 针对大误差和空间聚集的优化

本轮仅用720个训练格的固定折外残差定位，发现41格绝对误差超过200起。局部Moran的9999次置换及BH校正后有21格显著，主要低估连通片位于I-110/Harbor Fwy/S Vermont Ave和Hollywood Blvd/Franklin Ave/Vine St一带；道路仅作定位参照，不作原因判断。见[聚集诊断图](04_outputs/cluster_targeted_optimization/training_residual_clusters.png)。

共测试7种训练误差加权配置，权重只由各外层训练子集内部的3折带间隔RF残差生成，预测不使用邻格真实事故数。较强局部加权在166格开发验证中将RMSE82.47→81.33、MAE52.07→51.62、大于200起误差格8→6、Moran I0.0554→0.0366；但连续地域留出未通过稳定性门槛，弱局部权重也未通过。正式模型保持不变，本轮未再次评估原227格。

详见[针对性优化报告](06_reports/RF_Cluster_Targeted_Optimization.docx)、[验证指标图](04_outputs/cluster_targeted_optimization/validation_targeted_comparison.png)与[嵌套验证记录](04_outputs/cluster_targeted_optimization)。这些是反复使用开发区得到的探索性证据，不是新独立测试。


## 连续地域保护试验

本轮测试12种几何支持保护。训练位置凸包外回退到原RF，使北侧与东侧连续留出预测与对照相同；这表示避免候选退步，不表示提高外推准确度。再加入最近训练距离衰减后，166格验证RMSE82.47→81.04，大于200起误差格8→6、Moran I0.0554→0.0381。

新增内部5km留出块6_6与6_8分别覆盖I-110和Hollywood训练误差簇；距离保护候选在合并42格中的RMSE187.28→188.43、MAE146.79→148.10、Moran I0.1746→0.1796，未通过联合门槛。正式模型不变，本轮未再次评估原227格。详见[地域保护报告](06_reports/RF_Support_Protection_Optimization.docx)、[开发留出保护图](04_outputs/support_protection_optimization/development_support_gate_map.png)及[全部证据](04_outputs/support_protection_optimization)。


## Hollywood专项验证记录

Hollywood内部24格的研究候选局部改善，但166格验证RMSE由82.47升至82.56，I-110残差Moran I略升，未采用。按最新保留要求，研究模型包已删除，项目仅保留上方唯一生产模型。此前834格匹配诊断仅作历史研究记录，不能当作全市正式结果。见[验证摘要](06_reports/RF_Hollywood_Validation.txt)及[逐格诊断](04_outputs/hollywood_targeted_optimization)。

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
