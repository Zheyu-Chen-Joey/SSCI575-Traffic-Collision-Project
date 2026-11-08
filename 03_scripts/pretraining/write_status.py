import pathlib,json,html,datetime,sys
ROOT=pathlib.Path.cwd();sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd
Q=ROOT/'04_outputs/pretraining';P=ROOT/'01_data/processed/pretraining_1km';df=pd.read_csv(P/'model_table_1000_final.csv');qa=json.load(open(Q/'feature_build_qa.json'));di=qa['grid_diagnostics'];readiness=json.load(open(Q/'readiness.json'));checks=json.load(open(Q/'verification.json'))
text=f'''SSCI575 训练前准备状态报告
日期：2026年11月7日（America/Los_Angeles）

范围与结论
用户确认仅准备数据和训练脚本，不训练、评估或部署模型。已选定1000米实践工作尺度，不宣称NSR最优。1km网格、可获取的数据、特征构造、固定空间分割、未拟合管道与输入检查均已落盘。原研究设计尚未完全达到可训练状态：2017—2021交通流量数值仍缺失，质量检查会阻止完整baseline训练。

一 1km网格与响应
EPSG:26911；固定原点(345000,3730000)米；半开区间点归属。全域1473格，事故总数230536；零事故比例13.2383%。保留所有零事故格。城市面积占原方格>=80%的1113格作为拟建模样本，其余360个边界碎格仍保留在完整表中。
训练720格、验证166格、测试227格。测试块沿用预先保留的5km哈希块，开发区域使用独立哈希规则分出验证块。同一块不会进入不同分区，没有按目标或测试性能调整分区。空间块之间没有额外距离缓冲。
1km主诊断使用886个非测试合格格：球状模型、25km最大距离、1km箱宽、每箱>=30对、配对数加权多初值。NSR={di['nsr']:.6f}，Range={di['range_m']/1000:.2f}km，Moran I={di['moran_i_knn8']:.6f}，199次置换p={di['moran_p']:.3f}。Range仍超出拟合距离，不当作已证实相关距离。该结果属于1000米，未沿用1100米数值。

二 本次补齐的数据
人口：Census官方2021 ACS5离线表B01003，总人口估计与90%误差界；2941个相交block group全部匹配。按完整BG面积做权重，再计算网格内人口，市界估计汇总约3895136人（面积分配估计，不等于直接发布的城市人口）。误差界用权重后的平方和开方，隐含不同BG估计独立，属于近似。人口几何覆盖最低99.65%。
道路：筛选TIGER2021机动车道路S1100/S1200/S1400/S1630/S1640，共27759个分解后市内线段，长度约13764.620km。逐格切分后长度守恒相对差异约5.14e-15。道路类型使用长度主导MTFCC；曲折度是线长/端点直线距的分段代理，不是物理曲率。
交叉口：另下载2021 TIGER Edges，使用95452条市界附近次级/地方/服务道路的原始TNID节点，以至少3条不同TLID边为候选条件，得到42672个市内拓扑连接点；节点坐标一致性检查无>1m差异。排除主干高速与匝道，不将几何相交线、折线拐点或裁剪端点直接当作交叉口。该定义仍未逐一现场核实立交和实际路口控制。
功能分类：Caltrans官方洛杉矶县115738个源对象，裁剪分解后88645个线要素。按同一Caltrans网络长度为分母计算freeway(类1/2)、arterial(类3/4)、collector(5/6)、local(7)占比。市内长度约12824.728km，分格守恒通过。它与TIGER网络的道路总长度不可混作同一分母；该服务为当前快照，未证明研究期一致。
土地利用：50643个市内面，7类，在每格内对同类几何求并集，避免重复面积。类别间最大重叠比例约0.00000661，无>1%重叠格；平均覆盖约81.02%，中位数81.29%。未覆盖面积单列，不把它归为某一用地。19格没有用地图面，类别比例记缺失而非全部0。
信号：5506个市内点，按0.1m坐标去重后5464点；按网格汇总密度。88.99%的原始信号点距离TIGER拓扑连接点<=30m，中位距离1.26m。这是空间一致性检查，不证明2017—2021安装历史。

三 未解决的数据项
LADOT Traffic Counts Summary官方汇总表5953行，排除7条无效日期后范围2010-07-15至2016-12-07，研究期2017—2021为0行。MAN计数通常为6小时计数并由发布方扩展，与实际AADT不可自动等同。该表没有坐标。未把这批旧观测或6800个NavigateLA位置对象替代为研究期交通流量。
NavigateLA正常公开入口提供免责声明与使用条件，直接计数报告无法访问。未接受新条款、未绕过限制，也未从受限报告批量下载。后续可提供有权使用的研究期计数文件，或明确修改研究设计删除Traffic Volume。
训练检查按“训练格实测交通数值覆盖至少50%”设置项目操作阈值，并要求不能整列缺失；阈值不是文献证明的普适界限。当前覆盖0%，因此完整baseline被阻断。缺值插补仅能在未来训练折内执行，不能为整列没有观测的数据创造暴露信息。
2021年事故源接口18796条。逐年核对已证明本地提取与发布接口一致，没有因分页上限截断；尚未证明发布记录覆盖全部真实事故。目标应称为该公开接口记录的事故负担，不能把2021年减少直接当作交通安全改善。

四 建模输入与脚本
完整表：01_data/processed/pretraining_1km/model_table_1000_final.csv（{len(df)}行，{len(df.columns)}列）及同名GPKG。
空间分割：spatial_split_1000.csv；按eligible筛选的train/validation/test表及05_models/pretraining下baseline/enhanced的X/y文件。
数据字典：04_outputs/pretraining/data_dictionary.csv。
未拟合管道：03_scripts/pretraining/pipeline_definition.py，baseline原六类变量；enhanced增加曲折度、功能分类高速与主干道占比、信号密度。排除限速、视距和rurality。
prepare_training.py --check-only：生成并检查输入，不拟合预处理或RF。
train_rf.py：默认只打印说明，不拟合。未来有明确训练授权且通过readiness检查，才使用--execute-training。所有缺失填补与编码位于Pipeline内，并在训练区域GroupKFold中拟合；参数搜索不读取最终测试性能。脚本包括未来验证、测试及残差Moran输出逻辑，本次未执行。
import_traffic_values.py --input 授权CSV路径：按02_config/traffic_values_input_template.csv输入研究期日当量交通计数。先按站点观测平均，再按网格站点平均，不能当作完整5年AADT；输出日期及类型审计。
run_preparation.ps1：使用已有下载快照重建所有特征并检查，不调用模型训练。

五 质量与可复现性
独立最近规则格中心分配重算事故数，与半开区间统计完全一致；逐年目标和总目标一致；无ID重复与空间块跨区。既有151个原始快照sha256全部未变。未发现目标、坐标或分区字段进入模型特征列表；两种管道都保持未拟合。未生成训练后的.joblib模型，没有预测或精度结果。
来源与新文件校验：00_admin/pretraining_manifest.json和00_admin/pretraining_sources.json；环境版本：05_models/pretraining/environment.json。准备脚本在当前Windows项目环境运行时可能需要读取.runtime的权限。已有PPT与Word是前一阶段快照，未冒充已同步此次新数据。

六 主要官方来源
ACS：https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/acsdt5y2021-b01003.dat
TIGER Edges：https://www2.census.gov/geo/tiger/TIGER2021/EDGES/tl_2021_06037_edges.zip
功能分类：https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/CRS_Functional_Classification/FeatureServer/0
交通汇总：https://data.lacity.org/resource/94wu-3ps3.json
事故源：https://data.lacity.org/resource/d5tf-ez2w.json
原有道路、BG、市界、土地利用与信号来源见此前数据清单。
'''
design=json.loads((ROOT/'02_config/feature_design.json').read_text())
if not design['include_traffic_volume']:
 text=text.replace('原研究设计尚未完全达到可训练状态：2017—2021交通流量数值仍缺失，质量检查会阻止完整baseline训练。','用户已明确暂时移除交通流量。修订后的五类基础特征与增强特征输入均通过准备检查，readiness为ready_for_training_inputs_no_fit；这不代表已训练或研究期完整性问题已经解决。')
 text=text.replace('三 未解决的数据项','三 暂时排除的交通数据及研究限制')
 text=text.replace('后续可提供有权使用的研究期计数文件，或明确修改研究设计删除Traffic Volume。','本次已按用户确认暂时从两套模型输入删除Traffic Volume。历史计数和位置仅保留作审计，不进入模型。')
 text=text.replace('训练检查按“训练格实测交通数值覆盖至少50%”设置项目操作阈值，并要求不能整列缺失；阈值不是文献证明的普适界限。当前覆盖0%，因此完整baseline被阻断。缺值插补仅能在未来训练折内执行，不能为整列没有观测的数据创造暴露信息。','交通覆盖阈值仅在未来明确重新纳入该变量时适用。当前检查只针对修订设计选中的特征，无整列缺失，阻断项为空。缺值插补仍只可在未来训练折内执行，不能为未观测的交通流量创造信息。')
 text=text.replace('baseline原六类变量','baseline五类变量（道路密度、交叉口密度、道路类型、人口密度、土地利用组成）')
 text += '\n七 研究设计修订\n本阶段不控制直接车辆暴露，不能输出事故率或声称暴露调整后的事故风险。道路与人口变量不宣称替代交通流量。baseline与enhanced仍在相同空间分割上比较，但baseline已不等同于原六类特征方案。旧Word与PPT保留此前方案快照，本次有效设计以02_config/feature_design.json为准。\n'
(ROOT/'06_reports/pretraining_status_20261107.txt').write_text(text,encoding='utf8')
# Update current entry points while retaining dated historical findings below.
p=ROOT/'README.md';old=p.read_text(encoding='utf-8-sig');marker='# 2026年11月7日训练前准备\n';current='''# 2026年11月7日训练前准备

当前工作网格已按用户决定固定为1000米，属于实践选择。1km统计已经单独计算，未沿用1100米结果。本次明确不训练模型。

当前建模表：01_data/processed/pretraining_1km/model_table_1000_final.csv及GPKG。1473个市界相交格，1113个合格格；固定训练/验证/测试为720/166/227格。人口、道路、拓扑路口、土地利用、信号和功能分类特征已完成。

唯一硬性缺口是2017—2021交通流量数值。官方可下载汇总表止于2016年；当前列保持缺失，readiness阻止完整baseline训练。历史一致性及2021事故覆盖仍须按报告解释。

详细状态：06_reports/pretraining_status_20261107.txt。检查项：04_outputs/pretraining/readiness.json与verification.json。数据字典：04_outputs/pretraining/data_dictionary.csv。

检查而不训练：
```powershell
python 03_scripts/pretraining/prepare_training.py --check-only
python 03_scripts/pretraining/verify_inputs.py
```

有权使用的研究期交通数据可按02_config/traffic_values_input_template.csv准备，使用import_traffic_values.py导入后重跑finalize_inputs.py和prepare_training.py。不要把旧计数或位置数量冒充研究期交通流量。未来训练入口train_rf.py默认不会拟合，且数据不合格时禁止执行训练。

以下内容保留早期1100米候选诊断记录，其当时的数据缺口和尺度状态不代表当前状态。

---

'''
if not old.startswith(marker):p.write_text(current+old,encoding='utf8')
p=ROOT/'06_reports/grid_decision.md';old=p.read_text(encoding='utf-8-sig');p.write_text('# 2026年11月7日工作尺度更新\n\n用户选定1000米作为实践工作尺度。新网格及独立诊断见04_outputs/pretraining/feature_build_qa.json。NSR约0.25868，Range约37.13km（仍为外推）；未宣称NSR唯一最优。以下保留此前1100米候选分析的历史记录。\n\n'+old,encoding='utf8')
status={'updated_local_date':'2026-11-07','scope':'prepare_data_and_training_scripts_only','training_executed':False,'working_scale_m':1000,'scale_choice':'user_selected_practical_scale_not_nsr_optimum','completed':['exact_1km_grid','ACS2021_population_and_MOE','road_lengths_and_types','TIGER2021_topology_junctions','Caltrans_functional_shares','landuse_category_unions','signal_aggregation_and_spatial_match','spatial_train_validation_test_split','feature_dictionary','unfitted_RF_pipelines','future_training_entry_with_gate','independent_integrity_checks','raw_snapshot_hash_verification'],'remaining':[],'feature_design':design,'preparation_status':'ready_for_training_inputs_no_fit','research_caveats':readiness['review_items'],'model_gate':'not_executed_user_requested_prepare_only','readiness_path':'04_outputs/pretraining/readiness.json'};(ROOT/'07_agents/status.json').write_text(json.dumps(status,indent=2),encoding='utf8')
# Freeze exact versions needed by reproducible preparation/definitions, separate from earlier requirements.
env=json.load(open(ROOT/'05_models/pretraining/environment.json'));(ROOT/'05_models/pretraining/requirements.txt').write_text('\n'.join(f'{n}=={v}' for n,v in env['packages'].items())+'\n',encoding='utf8')
sources={'retrieved_local_date':'2026-11-07','sources':[{'name':'ACS2021 ACS5 B01003','path':'01_data/raw/pretraining_20261107/acsdt5y2021-b01003.dat','url':'https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/acsdt5y2021-b01003.dat','vintage':'2021 ACS5 (2017–2021 pooled)'},{'name':'TIGER2021 Edges LA County','path':'01_data/raw/pretraining_20261107/tl_2021_06037_edges.zip','url':'https://www2.census.gov/geo/tiger/TIGER2021/EDGES/tl_2021_06037_edges.zip','vintage':'2021'},{'name':'Caltrans functional classification','paths':'01_data/raw/pretraining_20261107/functional_class_*.json','url':'https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/CRS_Functional_Classification/FeatureServer/0','vintage':'current snapshot','requested_object_count':115738,'downloaded_object_count':115738},{'name':'LADOT Traffic Counts Summary','path':'01_data/raw/pretraining_20261107/traffic_summary.json','url':'https://data.lacity.org/resource/94wu-3ps3.json','n_rows':5953,'study_period_rows':0,'license_from_publisher_catalog':'CC0'}]};(ROOT/'00_admin/pretraining_sources.json').write_text(json.dumps(sources,indent=2),encoding='utf8');print('Saved status report and current documentation')
