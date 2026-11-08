from pathlib import Path
import json,datetime,hashlib,shutil
R=Path.cwd();O=R/'04_outputs/rf_project_v1';M=R/'05_models/rf_project_v1';E=json.loads((M/'evaluation.json').read_text());old=json.loads((R/'07_agents/status.json').read_text());old['scope']='RF training optimization evaluation and project report';old['training_executed']=True;old['model_gate']='passed_and_trained_user_authorized';old['preparation_status']='trained_and_independently_verified';old['completed']+=['baseline_and_enhanced_RF','training_only_spatial_CV_optimization','frozen_validation_selection','one_batch_final_test','residual_Moran_4_8_12','development_split_buffer_seed_sensitivity','2017_2020_target_sensitivity','paired_test_block_bootstrap','validation_permutation_importance','official_HIN_context','prediction_residual_maps_and_GIS','final_project_report'];old['remaining']=[];old['feature_design']=json.loads((R/'02_config/feature_design.json').read_text());old['current_results']={'report':'06_reports/SSCI575_Final_Project_Report.docx','run':'04_outputs/rf_project_v1','recommended_model':'05_models/rf_project_v1/enhanced_optimized_rf.joblib','test':E['enhanced_optimized']['test'],'residual_moran':E['enhanced_optimized']['residual_moran']['8'],'limitations':'spatially clustered residuals; paired-block difference CI includes0; historical snapshot and2021 reporting limits'};(R/'07_agents/status.json').write_text(json.dumps(old,ensure_ascii=True,indent=2),encoding='utf-8')
p=R/'README.md';p.write_text('''# 当前项目结果 2026年11月7日

用户已明确授权训练与优化。已在1000米工作网格完成基础/增强RF训练、空间CV调参、冻结选择及一次性保留测试评估。模型未部署在线服务。

推荐增强RF：测试R²=0.7317，RMSE=97.9848起/格，MAE=64.9598起/格。初始基础RF的RMSE=118.9641；调参基础RF反而变差，完整保留。残差Moran I=0.2996、p=0.0001；成对空间块bootstrap的RMSE差异95%区间跨0，不能宣称所有地区稳定优于基础。

报告：06_reports/SSCI575_Final_Project_Report.docx。模型：05_models/rf_project_v1。数据、图、GIS预测与残差、协议和校验：04_outputs/rf_project_v1。操作说明：06_reports/PROJECT_DELIVERABLES.txt。

沿用已确认的1km实践尺度与变量排除，未恢复不合适的交通流量、限速、视距或rurality。目标为公开记录的2017–2021事故总负担，不是未来预测、因果效果或暴露调整风险。最终测试区未参与模型选择或拟合。

以下是训练前及尺度研究的历史状态，不能当作当前尚未训练。

---

'''+p.read_text(),encoding='utf-8')
p=R/'06_reports/grid_decision.md';p.write_text('当前训练阶段更新：用户选定1000米工作尺度后，已完成RF训练与评估。尺度仍是实践选择，不是唯一NSR最优；RF测试结果不用于反向选尺度。最终结果见SSCI575_Final_Project_Report.docx。\n\n'+p.read_text(),encoding='utf-8')
for i,src in enumerate([r'C:/Users/czy08/OneDrive/xwechat_files/wxid_2nok8y7qz5qt22_f08b/msg/file/2026-09/SSCI575_Traffic_Project_Presentation_Script.docx',r'C:/Users/czy08/OneDrive/xwechat_files/wxid_2nok8y7qz5qt22_f08b/msg/file/2026-10/SSCI575_Presentation2_CN_with_New_Dataset_Verification(2).docx']):
 dest=R/f'00_admin/source/user_reference_{i+1}.docx'
 if not dest.exists():shutil.copy2(src,dest)
protocol=json.loads((O/'training_protocol.json').read_text());alignment={'source_documents':['00_admin/source/user_reference_1.docx','00_admin/source/user_reference_2.docx','00_admin/source/SSCI575_Project_Update.docx'],'executed':['City of Los Angeles2017–2021 recorded count target','single RF algorithm baseline/enhanced','pre-model scale diagnostics and zero cells','fixed spatial block partition and sensitivity','R2 RMSE MAE evaluation','feature interpretation and residual Moran','predicted/observed/residual maps','official HIN contextual comparison'],'authorized_amendments':['user_selected1000m practical grid','traffic volume temporarily excluded by user','speed rejected after spatial/temporal audit','sinuosity proxy for curvature; signal point density not verified historical signal-intersection inventory'],'not_claimed':['exact original six-variable replication','unique optimum grid','full temporal covariate consistency','universal statistically confirmed enhanced superiority','causal interpretation','future forecasting','independent HIN validation','online deployment'],'current_protocol':str((O/'training_protocol.json').relative_to(R))};(O/'plan_alignment.json').write_text(json.dumps(alignment,indent=2),encoding='utf-8')
text='''SSCI575 最终项目交付与操作说明

1 先读报告
06_reports/SSCI575_Final_Project_Report.docx：研究设计、来源、参数、初始/优化比较、空间残差、重要性、稳定性、局限及复现。

2 推荐模型
05_models/rf_project_v1/enhanced_optimized_rf.joblib
RF500树，深度8，叶最少5，max_features0.7，平方误差，随机种子42。含训练内插补及编码。只对本项目同定义的16个聚合字段预测；joblib需使用项目记录的依赖版本。目标是历史2017–2021公开记录数。
同目录保留两套初始/优化最终模型、仅训练区拟合的解释模型和四年目标敏感性模型。最终主模型拟合886个开发格，测试227格未拟合。

3 地图和GIS
04_outputs/rf_project_v1/figures：8张结果图。
04_outputs/rf_project_v1/grid_predictions_1000.gpkg：EPSG26911，grid_predictions和hin2024_context两层；ArcGIS Pro/QGIS可打开。
同名CSV和GeoJSON用于表格与网页制图；GeoJSON为EPSG4326。
prediction_role区分heldout_test、development_in_sample、boundary_extrapolation_not_evaluated。不能将开发区拟合值或边界外推当作测试精度。
残差=观测−预测；正值为低估。1km原点不变。

4 复查已完成结果 不重新训练
项目根目录PowerShell：
$env:PYTHONUTF8='1'
python 03_scripts/pretraining/verify_trained_project.py
python 03_scripts/pretraining/export_project_results.py
python 03_scripts/pretraining/predict_frozen_rf.py --input 01_data/processed/pretraining_1km/model_table_1000_final.csv --output 04_outputs/rf_project_v1/new_predictions.csv
Python依赖位于.runtime，脚本自动加入路径。文件environment.json记录训练环境。不要覆盖原始快照。

5 完整训练过程
03_scripts/pretraining/run_project_training.py为本次完整入口；training_protocol.json在训练前记录参数候选和CV网格ID。frozen_selection.json在测试之前冻结推荐模型。脚本阻止覆盖已完成的测试运行。
未来重复训练需建立新运行目录并明确已看过本测试结果，不能把反复使用同一测试当成新独立验证。
cv_fold_scores.csv、development_sensitivity.csv、bootstrap_intervals.json、validation_permutation_importance.csv与evaluation.json保留全部比较。历史train_rf.py仅是原先预留简版入口，本次实际使用run_project_training.py。

6 结果边界
增强调参测试R²0.7317，RMSE97.9848，MAE64.9598。基础调参未改善测试表现。残差空间聚集仍显著；增强相对基础的成对块重采样差异区间跨0。
数据缺口与用户已确认调整见plan_alignment.json及报告。HIN仅为背景对照，不能当独立真值。项目完成的是研究分析与可运行离线模型，不包括在线服务部署。
'''
(R/'06_reports/PROJECT_DELIVERABLES.txt').write_text(text,encoding='utf-8');shutil.copy2(R/'05_models/pretraining/environment.json',M/'environment.json')
# Human-readable run index is intentionally plain text, with machine contracts retained as JSON.
contract={'required_columns':json.loads((O/'frozen_selection.json').read_text())['enhanced']['features'],'target':'count_2017_2021','units':'recorded collisions over2017–2021 per clipped1km grid','crs':'EPSG26911','working_grid_side_m':1000,'origin':[345000,3730000],'not_features':['count_years','coordinates','split','HIN'],'training_rows':886,'heldout_rows':227};(M/'input_contract.json').write_text(json.dumps(contract,indent=2),encoding='utf-8')
print('Project status, source copies and usage instructions saved')
