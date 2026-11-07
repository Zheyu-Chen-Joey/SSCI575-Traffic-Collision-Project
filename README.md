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
