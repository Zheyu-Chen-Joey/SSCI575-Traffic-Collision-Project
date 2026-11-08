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
