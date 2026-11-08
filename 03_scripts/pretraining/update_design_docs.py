import pathlib,json
R=pathlib.Path.cwd();p=R/'03_scripts/pretraining/write_status.py';s=p.read_text(encoding='utf-8-sig');needle="(ROOT/'06_reports/pretraining_status_20261107.txt').write_text(text,encoding='utf8')"
replacement="""design=json.loads((ROOT/'02_config/feature_design.json').read_text())
if not design['include_traffic_volume']:
 text=text.replace('原研究设计尚未完全达到可训练状态：2017—2021交通流量数值仍缺失，质量检查会阻止完整baseline训练。','用户已明确暂时移除交通流量。修订后的五类基础特征与增强特征输入均通过准备检查，readiness为ready_for_training_inputs_no_fit；这不代表已训练或研究期完整性问题已经解决。')
 text=text.replace('三 未解决的数据项','三 暂时排除的交通数据及研究限制')
 text=text.replace('后续可提供有权使用的研究期计数文件，或明确修改研究设计删除Traffic Volume。','本次已按用户确认暂时从两套模型输入删除Traffic Volume。历史计数和位置仅保留作审计，不进入模型。')
 text=text.replace('训练检查按“训练格实测交通数值覆盖至少50%”设置项目操作阈值，并要求不能整列缺失；阈值不是文献证明的普适界限。当前覆盖0%，因此完整baseline被阻断。缺值插补仅能在未来训练折内执行，不能为整列没有观测的数据创造暴露信息。','交通覆盖阈值仅在未来明确重新纳入该变量时适用。当前检查只针对修订设计选中的特征，无整列缺失，阻断项为空。缺值插补仍只可在未来训练折内执行，不能为未观测的交通流量创造信息。')
 text=text.replace('baseline原六类变量','baseline五类变量（道路密度、交叉口密度、道路类型、人口密度、土地利用组成）')
 text += '\\n七 研究设计修订\\n本阶段不控制直接车辆暴露，不能输出事故率或声称暴露调整后的事故风险。道路与人口变量不宣称替代交通流量。baseline与enhanced仍在相同空间分割上比较，但baseline已不等同于原六类特征方案。旧Word与PPT保留此前方案快照，本次有效设计以02_config/feature_design.json为准。\\n'
(ROOT/'06_reports/pretraining_status_20261107.txt').write_text(text,encoding='utf8')"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("'remaining':['2017_2021_traffic_volume_values_or_explicit_feature_design_revision']", "'remaining':[],'feature_design':design,'preparation_status':'ready_for_training_inputs_no_fit'")
s=s.replace("'model_gate':'closed'", "'model_gate':'not_executed_user_requested_prepare_only'")
p.write_text(s,encoding='utf8')
# Update documentation to the selected feature design, retaining historical sections below.
p=R/'README.md';t=p.read_text(encoding='utf-8-sig');t=t.replace('唯一硬性缺口是2017—2021交通流量数值。官方可下载汇总表止于2016年；当前列保持缺失，readiness阻止完整baseline训练。历史一致性及2021事故覆盖仍须按报告解释。','用户已确认暂时移除交通流量。当前baseline使用道路密度、交叉口密度、道路类型、人口密度、土地利用五类特征；enhanced增加道路设计特征。所选输入无整列缺失，readiness已通过。人口分配、历史快照及2021事故覆盖等研究限制仍须保留。')
t=t.replace('有权使用的研究期交通数据可按02_config/traffic_values_input_template.csv准备，使用import_traffic_values.py导入后重跑finalize_inputs.py和prepare_training.py。不要把旧计数或位置数量冒充研究期交通流量。未来训练入口train_rf.py默认不会拟合，且数据不合格时禁止执行训练。','有效设计以02_config/feature_design.json为准。交通数据和缺失字段保留供审计，但不进入baseline或enhanced的X文件，不参与插补。研究预测公开记录的事故负担，不计算暴露调整事故率。未来重新纳入交通流量需要单独修订设计。train_rf.py默认不会拟合，本次不执行训练。')
p.write_text(t,encoding='utf8')
p=R/'AGENTS.md';t=p.read_text(encoding='utf8');t+='\n## 2026年11月7日特征设计修订\n用户明确暂时移除交通流量。当前baseline为道路密度、交叉口密度、道路类型、人口密度、土地利用五类；enhanced再加道路设计。以02_config/feature_design.json为准。不得将交通位置、历史旧计数或整列缺失交通值带入任一模型。仍只准备数据和脚本，不训练RF。不得把当前结果称为暴露调整后的风险或事故率。\n';p.write_text(t,encoding='utf8')
p=R/'02_config/feature_design.json';d=json.loads(p.read_text());d['research_questions']={'RQ1':'How well do road network, population and land-use features predict recorded2017–2021 collision counts at1km?','RQ2':'Do road sinuosity, functional-class shares and signal density improve prediction over the revised five-group baseline?','RQ3':'What sensitivity and limitations do spatial scale diagnostics reveal for the practical1km working grid?'};p.write_text(json.dumps(d,indent=2),encoding='utf8')
