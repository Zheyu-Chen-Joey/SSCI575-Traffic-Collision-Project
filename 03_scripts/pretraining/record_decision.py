from pathlib import Path
import json
p=Path('02_config/analysis.json');d=json.loads(p.read_text(encoding='utf-8-sig'));d.update({'working_candidate_m':1100,'final_scale_m':1000,'scale_decision':{'basis':'user_selected_practical_working_scale','date_local':'2026-11-07','reason':'standard 1 km reporting and aggregation; not claimed to be NSR optimum'},'model_allowed':False,'execution_scope':'data_and_training_scripts_only_no_fit'});p.write_text(json.dumps(d,indent=2),encoding='utf8')
p=Path('AGENTS.md');s=p.read_text(encoding='utf-8-sig').replace('当前未完成最终尺度确认，不运行 RF。','用户已于2026年11月7日选定1000米工作尺度，属于实践选择而非唯一NSR最优。用户本次明确只准备数据和训练脚本，不训练RF；数据质量门槛仍须独立检查。');p.write_text(s,encoding='utf8')
