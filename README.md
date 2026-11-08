残差优化后续试验：新增24组RF开发候选，v2在旧测试区Moran略降但RMSE变差，属于取舍而非全面改善。正式v1模型与报告保留；见06_reports/Residual_Refinement_v2.txt及04_outputs/rf_residual_refinement_v2。旧测试再次使用是探索性对照。

# 当前项目结果 2026年11月7日

用户已明确授权训练与优化。已在1000米工作网格完成基础/增强RF训练、空间CV调参、冻结选择及一次性保留测试评估。模型未部署在线服务。

推荐增强RF：测试R²=0.7317，RMSE=97.9848起/格，MAE=64.9598起/格。初始基础RF的RMSE=118.9641；调参基础RF反而变差，完整保留。残差Moran I=0.2996、p=0.0001；成对空间块bootstrap的RMSE差异95%区间跨0，不能宣称所有地区稳定优于基础。

报告：06_reports/SSCI575_Final_Project_Report.docx。模型：05_models/rf_project_v1。数据、图、GIS预测与残差、协议和校验：04_outputs/rf_project_v1。操作说明：06_reports/PROJECT_DELIVERABLES.txt。

沿用已确认的1km实践尺度与变量排除，未恢复不合适的交通流量、限速、视距或rurality。目标为公开记录的2017–2021事故总负担，不是未来预测、因果效果或暴露调整风险。最终测试区未参与模型选择或拟合。

以下是训练前及尺度研究的历史状态，不能当作当前尚未训练。

---

限速审计更新：FHWA NHS限速已下载；30m直接上报潜在道路覆盖11.98%，历史有效期未核实，暂不纳入增强模型。见06_reports/speed_limit_audit_20261107.txt。未训练模型。

# 2026年11月7日训练前准备

当前工作网格已按用户决定固定为1000米，属于实践选择。1km统计已经单独计算，未沿用1100米结果。本次明确不训练模型。

当前建模表：01_data/processed/pretraining_1km/model_table_1000_final.csv及GPKG。1473个市界相交格，1113个合格格；固定训练/验证/测试为720/166/227格。人口、道路、拓扑路口、土地利用、信号和功能分类特征已完成。

用户已确认暂时移除交通流量。当前baseline使用道路密度、交叉口密度、道路类型、人口密度、土地利用五类特征；enhanced增加道路设计特征。所选输入无整列缺失，readiness已通过。人口分配、历史快照及2021事故覆盖等研究限制仍须保留。

详细状态：06_reports/pretraining_status_20261107.txt。检查项：04_outputs/pretraining/readiness.json与verification.json。数据字典：04_outputs/pretraining/data_dictionary.csv。

检查而不训练：
```powershell
python 03_scripts/pretraining/prepare_training.py --check-only
python 03_scripts/pretraining/verify_inputs.py
```

有效设计以02_config/feature_design.json为准。交通数据和缺失字段保留供审计，但不进入baseline或enhanced的X文件，不参与插补。研究预测公开记录的事故负担，不计算暴露调整事故率。未来重新纳入交通流量需要单独修订设计。train_rf.py默认不会拟合，本次不执行训练。

以下内容保留早期1100米候选诊断记录，其当时的数据缺口和尺度状态不代表当前状态。

---

# 洛杉矶交通事故项目

本文件夹已按原始资料 → 下载 → 清理 → 尺度诊断 → 特征构建 → 模型 → 报告建立目录。

运行环境：Windows Python 3.13；依赖隔离安装到 .runtime，不修改系统依赖。脚本从本项目根目录运行。

```powershell
python 03_scripts/01_download.py
python 03_scripts/03_download_predictors.py
python 03_scripts/02_clean_and_grid.py
python 03_scripts/04_clean_predictors.py
python 03_scripts/05_sensitivity.py
```

当前31个网格均已生成，事故总量守恒检查通过。1,100m 是球状模型的首个候选局部低点，尚不能当作确认的最佳尺度。最终决定和未完成事项见06_reports/grid_decision.md。运行下载时需要网络；人口接口目前返回 Missing Key，不能当作成功数据。

01_download.py 是初始下载脚本，人口接口失败将停止后续步骤；已下载的原始快照仍保留。后续修复见07_agents/tasks/data.md。不要反复下载已存在的大型文件。

完整本地重现（原始下载已在）：
```powershell
python 03_scripts/02_clean_and_grid.py
python 03_scripts/04_clean_predictors.py
python 03_scripts/05_sensitivity.py
python 03_scripts/07_origin_sensitivity.py
python 03_scripts/08_finalize.py
python 03_scripts/09_verify.py
```
最终报告说明了人口数值与交通报告数值尚未完成。不要将当前文件夹视为已经可以直接训练模型的完整特征表。

Range补充验证：python 03_scripts/10_validate_range.py；解释见06_reports/range_validation.md。该验证不训练RF、不改网格，也不使用预留测试区域。
