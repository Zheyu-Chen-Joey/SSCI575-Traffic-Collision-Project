"""Retain the unsuccessful refinement audit without replacing the champion."""
from pathlib import Path
import json, hashlib, shutil, datetime, csv

R = Path(__file__).resolve().parents[2]
S = R / '06_reports/_qa/refined_local'
O = R / '04_outputs/rf_spatial_v5/refinement_20261107'
O.mkdir(exist_ok=True)
protocol = json.loads((S / 'protocol.json').read_text())
result = json.loads((S / 'evaluation.json').read_text())
assert result['promote'] is False and result['geographic_gate_pass'] is False
model = R / '05_models/rf_spatial_v5/spatial_frozen_rf.joblib'
sha = hashlib.sha256(model.read_bytes()).hexdigest()
assert sha == protocol['reference_sha256']
assert len(list((R / '05_models').rglob('*.joblib'))) == 1
data = R / '01_data/processed/pretraining_1km/model_table_1000_final.csv'
assert hashlib.sha256(data.read_bytes()).hexdigest() == protocol['input_sha256']
with data.open(newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
assert sum(float(x['count_2017_2021']) for x in rows) == 230536
for name in ['protocol.json', 'cv_scores.csv', 'cv_fold_scores.csv', 'validation_scores.csv', 'frozen_decision.json', 'geographic_gate.csv', 'evaluation.json']:
    shutil.copy2(S / name, O / name)
assert not (S / 'legacy_comparison.csv').exists()
verification = {'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'champion_sha256_unchanged': sha, 'input_sha256_unchanged': protocol['input_sha256'], 'crashes_conserved': 230536, 'production_model_count': 1, 'legacy_region_not_evaluated_this_round': True, 'promoted': False}
(O / 'verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
report = '''随机森林细化优化验证记录（2026-11-07）

结论：完成37组配置的开发集验证，本轮不替换当前模型。

数据与目标
City of Los Angeles，2017–2021事故总数，EPSG:26911固定1km网格。
输入表未变；1473格、230536条有效事故守恒。合格1113格按原划分为训练720、验证166、原评估227。
仅使用既有18项输入（含授权的网格中心坐标）；没有增加邻格真实事故数。

方法
保持全局RF参数及目标归一化不变，细化局部高斯带宽、锚点间距、叶节点、树深、特征抽样比例与全局/局部混合权重。
另测试依据最近训练格中心距离衰减局部修正：超过5km后以5km衰减尺度回归全局预测。此距离是训练支持度，不是分析网格大小。
固定种子708生成6组补充参数，与6组预设参数分别搭配3个混合权重，加现有模型对照，共37组。
训练720格按原五折划分；每折清除与验证格完整方格边界距离不超过1km的训练格。预处理、全局RF、局部RF均只拟合折内训练数据。
按预先保存规则入围4组，在166格验证区选择同时降低RMSE和MAE的方案。
冻结方案后，检查开发886格的北侧和东侧连续地域留出，并保留大于1km的完整方格间隔。
要求两个地域的新/旧RMSE比均值和MAE比均值均不超过1.01，才进入原227格的探索性比较。

结果（单位：起/格）
                    现有模型     冻结候选
五折平均RMSE          95.5888      93.4835
五折平均MAE           59.9261      59.7849
166格验证RMSE         82.7019      75.2047
166格验证MAE          52.8166      48.7894
北侧留出RMSE          44.2477      49.7871
北侧留出MAE           34.0450      39.0307
东侧留出RMSE         140.8983     145.9423
东侧留出MAE           94.3862      96.1207

冻结候选使用5km带宽、10km锚点间距、叶节点5、深度16、特征比例0.5、局部权重1.0与距离衰减。两个地域的RMSE比均值约1.0805、MAE比均值约1.0824，超过1.01门槛。
因此未评估原227格，未保存候选模型实体，未替换生产模型，未更改残差图或色标。
生产模型原227格探索性指标仍为RMSE83.5063、MAE54.5720、R²0.8052。这些数值来自此前多次复用的区域，不能作为全新独立验证。

解释与下一步
较窄局部模型改善覆盖内插值，但连续区域外推变差。验证区改善不能推广为全市普遍改善；残差颜色也不应被强制变白。
本轮地域留出亦已被查看，后续反复使用属于开发验证。若继续研究，应补充与研究年份匹配的解释变量，或在冻结方法后取得新的独立数据验证，而非继续依靠旧评估区域选参。
所有原始数据、既有模型与现有结果图保持不变。详细参数、逐折指标、冻结决定及哈希校验见04_outputs/rf_spatial_v5/refinement_20261107。
'''
(R / '06_reports/RF_Refinement_20261107.txt').write_text(report, encoding='utf-8-sig')
for rel in ['00_admin/latest_results.json', '07_agents/status.json']:
    p = R / rel
    d = json.loads(p.read_text(encoding='utf-8-sig'))
    d['latest_refinement'] = {'date': '2026-11-07', 'candidate_count': 37, 'promoted': False, 'reason': 'continuous north/east geographic stability gate failed', 'audit': '06_reports/RF_Refinement_20261107.txt', 'evidence': '04_outputs/rf_spatial_v5/refinement_20261107', 'legacy_evaluated': False}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
readme = R / 'README.md'
text = readme.read_text(encoding='utf-8')
note = '\n本轮追加37组细化配置，验证区RMSE降至75.20，但连续北侧与东侧留出退步，未通过稳定性门槛；保留当前模型。本轮未再次评估原227格。见[优化验证记录](06_reports/RF_Refinement_20261107.txt)。\n'
if '本轮追加37组细化配置' not in text:
    text = text.replace('## 使用与复现', note + '\n## 使用与复现')
readme.write_text(text, encoding='utf-8')
print(json.dumps(verification))
