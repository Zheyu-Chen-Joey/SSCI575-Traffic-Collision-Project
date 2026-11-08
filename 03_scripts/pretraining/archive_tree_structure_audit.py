"""Retain a failed tree-structure experiment without changing the champion."""
from pathlib import Path
import json,csv,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[2];S=R/'06_reports/_qa/tree_structure_v8';O=R/'04_outputs/rf_spatial_v5/tree_structure_v8';result=json.loads((S/'evaluation.json').read_text());protocol=json.loads((S/'protocol.json').read_text());assert not result['promote'],'A successful candidate needs full promotion verification'
mp=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';assert hashlib.sha256(mp.read_bytes()).hexdigest()==protocol['reference_sha256'];assert len(list((R/'05_models').rglob('*.joblib')))==1
source=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv';assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol['input_sha256']
O.mkdir(exist_ok=True)
for p in S.iterdir():
 if p.suffix in ['.csv','.json']:shutil.copy2(p,O/p.name)
rows=list(csv.DictReader((S/'cv_scores.csv').open()));validation=list(csv.DictReader((S/'validation_scores.csv').open()));verify={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_sha256_unchanged':protocol['reference_sha256'],'source_sha256_unchanged':protocol['input_sha256'],'production_model_count':1,'promoted':False,'legacy_evaluated_this_round':result['legacy_evaluated']};(O/'verification.json').write_text(json.dumps(verify,indent=2),encoding='utf-8')
reason='验证区双指标或90分位门槛未通过'if not result['decision']['development_validation_pass']else('连续地域稳定性门槛未通过'if not result['geographic_gate_pass']else'复用原区域的探索性接受门槛未通过')
lines=['随机森林树结构优化验证记录','','结论：本轮8种新配置未替换当前三方向RF。原因：'+reason+'。','','数据与方法','使用原18字段、固定1km网格及相同清理版本。原始快照和230536条有效事故记录保持不变。','固定0度25%、45度25%、60度50%的组合，测试叶节点3/4/6、较深或较浅树、特征比例0.65/0.8、80% bootstrap抽样，以及全局1000树/局部400树。','训练720格采用原固定五折，并保持完整方格大于1km的间隔；只在折内训练数据拟合预处理与所有RF组件。','平均折RMSE与MAE均下降后最多入围3项；166格验证要求RMSE、MAE下降且90分位不明显退步，冻结后才做开发区连续北侧/东侧留出。','只有地域检查通过才进行一次原227格探索性比较。所有区域已复用，不属于新的独立确认。','','五折开发结果','配置 | 平均折RMSE | 平均折MAE']
for row in rows:lines.append(f"{row['name']} | {float(row['mean_fold_rmse']):.4f} | {float(row['mean_fold_mae']):.4f}")
lines+=['','166格验证结果','配置 | RMSE | MAE | 绝对误差90分位']
for row in validation:lines.append(f"{row['name']} | {float(row['rmse']):.4f} | {float(row['mae']):.4f} | {float(row['p90_abs_error']):.4f}")
lines+=['','是否本轮再次查看原227格：'+str(result['legacy_evaluated']),'当前保留模型原227格探索性指标仍为RMSE80.6253、MAE53.0539、R²0.8184、残差Moran I0.2808。','没有调整残差色标、平滑误差或删除困难格。保留失败实验的参数与验证证据，不保存失败候选模型实体。','详细协议、逐折指标、冻结决定及哈希校验见04_outputs/rf_spatial_v5/tree_structure_v8。']
report=R/'06_reports/RF_Tree_Structure_Validation.txt';report.write_text('\n'.join(lines),encoding='utf-8-sig')
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;d=json.loads(p.read_text(encoding='utf-8-sig'));d['latest_tree_structure_audit']={'new_configurations':8,'promoted':False,'reason':reason,'legacy_evaluated':result['legacy_evaluated'],'report':'06_reports/RF_Tree_Structure_Validation.txt','evidence':'04_outputs/rf_spatial_v5/tree_structure_v8'};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'README.md';text=p.read_text(encoding='utf-8');note='\n追加8种树结构配置均未通过完整接受门槛，当前模型与地图保持不变。见[树结构验证记录](06_reports/RF_Tree_Structure_Validation.txt)。\n'
if '追加8种树结构配置'not in text:text=text.replace('## 使用与复现',note+'\n## 使用与复现')
p.write_text(text,encoding='utf-8');print(json.dumps(verify))
