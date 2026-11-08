"""Synchronize release metadata after user-requested research-model removal."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1]
model=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib'
assert hashlib.sha256(model.read_bytes()).hexdigest()=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357'
assert list((R/'05_models').rglob('*.joblib'))==[model]
summary='Hollywood专项研究记录\n\n该候选未通过166格验证RMSE门槛，未采用。按用户最新要求，已删除研究配对模型及其推理入口，只保留三方向RF生产模型。原始逐格诊断和研究方法留作追溯，不表示仍保留候选模型。\nHollywood24格匹配留出对照：RMSE196.16至192.36，MAE150.21至146.23，超过200起误差格7至6，Moran I 0.2429至0.2407。166格验证RMSE82.47至82.56，I-110 Moran I略升。配对诊断使用834格训练，不同于正式886格模型；本轮未重评原227格。\n'
(R/'06_reports/RF_Hollywood_Validation.txt').write_text(summary,encoding='utf-8')
p=R/'README.md';s=p.read_text(encoding='utf-8');a=s.index('## Hollywood专项研究对照');b=s.index('## 使用与复现',a)
s=s[:a]+'''## Hollywood专项验证记录

Hollywood内部24格的研究候选局部改善，但166格验证RMSE由82.47升至82.56，I-110残差Moran I略升，未采用。按最新保留要求，研究模型包已删除，项目仅保留上方唯一生产模型。此前834格匹配诊断仅作历史研究记录，不能当作全市正式结果。见[验证摘要](06_reports/RF_Hollywood_Validation.txt)及[逐格诊断](04_outputs/hollywood_targeted_optimization)。

'''+s[b:];p.write_text(s,encoding='utf-8')
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d.update(retention='one retained orientation ensemble RF; research bundle removed by latest user request',model_artifacts_retained=1,production_models_retained=1,research_bundles_retained=0)
 if 'scope'in d:d['scope']='single_best_orientation_RF_release'
 h=d.get('hollywood_targeted_optimization',{});h.pop('research_pair',None);h.update(report='06_reports/RF_Hollywood_Validation.txt',research_pair_retained=False);p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
for rel in ['decision_summary.json','verification.json']:
 p=R/'04_outputs/hollywood_targeted_optimization'/rel;d=json.loads(p.read_text());d.update(research_bundle_retained=False,retention_update='Removed by latest user request; metrics and hashes below describe historical diagnostic execution only')
 if rel=='verification.json':d['research_comparison_bundles']=0
 d.pop('research_pair',None);p.write_text(json.dumps(d,indent=2),encoding='utf-8')
p=R/'03_scripts/package_best_results.py';s=p.read_text();s=s.replace("[R/'06_reports/RF_Hollywood_Targeted_Optimization.docx',R/'03_scripts/create_hollywood_targeted_report.py']","[R/'06_reports/RF_Hollywood_Validation.txt',R/'03_scripts/retain_single_release.py']");s=s.replace("'build_hollywood_comparison_pair.py','predict_hollywood_research_pair.py',",'');s=s.replace("'finalize_hollywood_audit.py'", "'finalize_hollywood_audit.py'")
s=s.replace("one production control plus the user-requested research-only matched Hollywood holdout pair; originals remain in full repository","one retained production RF; research candidate entities removed; historical validation evidence retained")
p.write_text(s,encoding='utf-8')
print('Single retained release synchronized')
