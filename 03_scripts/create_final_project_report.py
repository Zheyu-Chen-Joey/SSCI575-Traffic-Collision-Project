"""Create the final project report using frozen evaluation artifacts, not hand-entered scores."""
from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path.cwd();O=R/'04_outputs/rf_project_v1';M=R/'05_models/rf_project_v1';E=json.loads((M/'evaluation.json').read_text());S=json.loads((O/'frozen_selection.json').read_text());CI=json.loads((O/'bootstrap_intervals.json').read_text());H=json.loads((O/'hin_context.json').read_text());V=json.loads((O/'verification.json').read_text());D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.left_margin=sec.right_margin=Inches(.75);sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.6)
for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
 st=D.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0);st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
D.styles['Normal'].font.size=Pt(10.5);D.styles['Normal'].paragraph_format.line_spacing=1.12;D.styles['Normal'].paragraph_format.space_after=Pt(7)
for n,size in [('Title',22),('Heading 1',17),('Heading 2',12),('Caption',9)]:D.styles[n].font.size=Pt(size)
for el in list(D.styles.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
def p(t):return D.add_paragraph(t)
def h(t):D.add_heading(t,1)
def sub(t):D.add_heading(t,2)
def page(t):h(t);D.paragraphs[-1].paragraph_format.page_break_before=True
def fig(name,width=6.6):D.add_picture(str(O/'figures'/name),width=Inches(width))
def table(headers,rows):
 t=D.add_table(rows=1,cols=len(headers));t.autofit=False
 for i,x in enumerate(headers):t.rows[0].cells[i].text=str(x)
 for row in rows:
  cells=t.add_row().cells
  for i,x in enumerate(row):cells[i].text=str(x)
 for ri,row in enumerate(t.rows):
  for cell in row.cells:
   tcPr=cell._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
   for k in ['top','bottom','left','right']:
    el=OxmlElement('w:'+k);el.set(qn('w:w'),'80');el.set(qn('w:type'),'dxa');mar.append(el)
   tcPr.append(mar);b=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');b.append(el)
   tcPr.append(b)
   if ri==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF5');tcPr.append(sh)
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=1.05
    for run in para.runs:run.font.size=Pt(10);run.bold=ri==0
  trpr=row._tr.get_or_add_trPr()
  if ri==0:trpr.append(OxmlElement('w:tblHeader'))
 D.add_paragraph().paragraph_format.space_after=Pt(1)
 return t
D.add_paragraph('洛杉矶交通事故空间负担预测项目报告','Title');p('SSCI 575  |  City of Los Angeles  |  2017–2021  |  2026年11月7日')
p('本报告使用已下载并清理的数据，完成基础与增强 Random Forest 的训练、空间交叉验证调参、独立测试、稳定性检查和地图输出。最终采用的增强模型在预留测试区取得 R² 0.732、RMSE 97.98 起/格和 MAE 64.96 起/格。模型用于回溯预测公开记录的五年事故负担，不能解释为未来事故预测、暴露调整后的风险或因果效应。')
sub('主要结论')
p('道路设计特征在本次固定划分中提供了额外预测信息。增强模型优于两种基础模型；增强模型调参后的测试 RMSE 较其初始版本降低约1.25%。基础模型调参虽然改善训练空间交叉验证分数，却未改善独立测试结果，所有结果均保留。')
p('模型残差仍有显著空间聚集：增强模型测试残差的8近邻 Moran’s I 为0.2996，9999次置换双侧p=0.0001。空间块重采样下，增强相对基础的RMSE差异95%区间跨过0，因此不能宣称其优势在所有地区都稳定成立。')
sub('独立测试结果')
labels={'baseline_initial':'基础 初始','baseline_optimized':'基础 调参','enhanced_initial':'增强 初始','enhanced_optimized':'增强 调参'}
table(['模型','RMSE 起/格','MAE 起/格','R²'],[[labels[k],f"{E[k]['test']['rmse']:.2f}",f"{E[k]['test']['mae']:.2f}",f"{E[k]['test']['r2']:.3f}"]for k in labels])
p('测试集为227个合格网格。所有最终模型在相同的886个开发网格上重拟合后，在同一预留测试区批量评估。增强模型在查看测试结果之前已依据验证区表现确定为推荐模型。模型未部署为在线服务。')
sub('对计划书的执行')
p('执行一开始方案的共同研究目标：洛杉矶市域、2017–2021事故数量、规则网格、多源城市环境数据、单一RF算法、基础与增强特征比较、残差诊断及HIN背景对照。结合已完成的31尺度诊断，沿用用户确定的1km工作尺度；沿用用户已确认的数据可用性调整，不恢复缺失的交通流量或未通过审计的限速。')
page('研究设计与数据')
sub('研究问题')
p('RQ1 道路网络、人口和土地利用能否预测事故空间差异；RQ2 道路设计能否增加预测信息；RQ3 尺度诊断与空间验证如何限定1km结果的解释。')
table(['数据','版本与处理','用途'],[
['LAPD事故','2017–2021；232695下载记录；剔除403无效位置与1756市外记录；保留230536','目标及尺度诊断'],
['TIGER Roads与Edges','2021；市内机动车道路13764.620km；原始TNID/TLID拓扑推导42672路口节点','道路密度 类型 路口 弯曲代理'],
['ACS B01003与BG','2021五年估计；2941个相交BG；按完整BG面积分配人口；MOE近似传播','人口密度'],
['LA General Plan Land Use','当前下载快照；50643市内要素；类别内部求并；保留未覆盖比例','7类土地占比'],
['Caltrans功能分类','当前快照；高速类1和2 干道类3和4；占比使用该分类网络自身长度作分母','高速与干道占比'],
['LADOT信号点','当前快照；5506点；0.1m坐标去重后5464点；非历史安装清单','信号点密度'],
['官方HIN2024','325条市内要素；883.941km；模型训练完成后补充下载','仅地图背景对照']])
sub('实际输入')
p('基础模型使用12个字段：道路密度、路口密度、人口密度、主导道路类型、7类土地占比和未覆盖比例。增强模型再增加4个字段：长度加权道路弯曲代理、高速功能分类占比、干道功能分类占比、信号点密度，共16个字段。字段数量不包含one-hot展开及缺失指示器。')
page('网格与空间验证方法')
p('土地类别为住宅、商业、工业、开放空间与公共设施、机场、港口和停车用地。没有土地利用观测的格保持缺失；所有数值插补均在相应训练折内部学习。交通流量、限速、视距、人口衍生rurality、HIN、坐标、网格ID及事故年计数均不进入预测特征。')
p('统一使用EPSG:26911，网格原点为E345000、N3730000。有效事故采用半开区间分配，每条只进入一个格；零事故格保留。所有网格事故总数核对为230536。共有1473个市界相交格，按市界面积占原方格至少80%的规则选出1113个建模格。边界小碎格的预测仅作外推，不计入性能。')
sub('尺度选择说明')
p('此前在500–5000m、150m步长的31种尺度上完成半变异与NSR诊断，1100m是首个浅局部低点，不是全局最低或唯一最优。用户最终选定1000m以便整数量化。1000m另行计算：非测试合格格的NSR=0.258680，Moran’s I=0.740240；球状模型range约37.13km，超过25km最大拟合lag，因此仍是外推，不宣称稳定平台。此次RF不反过来选择网格大小。')
sub('空间划分')
p('固定5km块保持原先划分：训练720格、验证166格、测试227格。测试块规则为(bx×73856093+by×19349663)%5==0；非测试块验证规则为(bx×83492791+by×297121507)%5==1。同一块不跨集合。主要划分没有距离缓冲；因此另在开发区做1km中心距离隔离敏感性检查。')
sub('训练与优化')
p('每种特征集均评估25个预先记录的参数候选，其中候选0为初始配置。训练区使用按5km块分组的5折交叉验证，共250次折内模型拟合。以平均RMSE最小选择候选，MAE仅用于同分排序；预处理与RF位于同一Pipeline，插补和编码不会先在全样本学习。')
p('候选范围包括树数300或500、最大深度8或12或不限、叶最少样本1/3/5/10、max_features为sqrt/0.7/1.0，以及平方误差或Poisson分裂准则。它们均为同一RF回归算法；Poisson仅为非负计数的分裂选项，不是额外模型。初始配置为300棵树、深度12、叶5、分裂10、sqrt特征和平方误差。随机种子42，候选抽样种子575。')
p('验证区用于查看开发表现和预先推荐增强模型。两套调参结果在最终测试前写入frozen_selection.json；最终将训练和验证合并为886格重拟合，并在同一测试批次报告四个主模型和预先声明的2017–2020目标敏感性。测试后没有继续调参。')
page('预测表现与优化效果')
fig('01_test_comparison.png',6.8)
fig('02_observed_predicted.png',6.6)
p('增强调参模型的RMSE较初始基础模型下降17.63%，较调参基础模型下降25.31%；但相对自身初始增强模型的下降仅1.25%，说明主要收益来自新增特征，本次参数优化带来较小附加收益。只用开发集均值作常数参考的测试RMSE为189.29，R²约−0.001。')
p('验证集增强RMSE从139.64降至129.42，R²从0.779升至0.810；基础模型验证RMSE从169.17变为170.12。不同空间区域的计数分布不同，不能直接把验证与测试误差差异解释为训练质量变化。')
page('参数选择与过拟合诊断')
fig('05_training_cv.png',6.7)
table(['配置','基础 调参','增强 调参'],[['树数','500','500'],['最大深度','不限','8'],['叶最少样本','5','5'],['分裂最少样本','10','10'],['max_features','0.7','0.7'],['分裂准则','Poisson','平方误差']])
p('基础模型的训练空间CV平均RMSE由111.70降至108.13，增强模型由97.67降至95.21。折间差异较大；图中误差棒为5折标准误，仅描述候选评估波动，不是总体泛化置信区间。')
p('基础调参模型的CV改善没有转化为测试改善：测试RMSE从118.96升至131.18。这是空间异质性与有限调参样本下的实际结果，不能只展示较好的CV分数。保留初始基础模型作为透明参照，不用已看到的测试表现重新选择或训练“更好”的基础模型。')
p('模型采用bootstrap树集成、叶大小约束及空间交叉验证。没有按OOB误差停止加树；树数作为候选配置在训练空间CV中比较。OOB不作为主要泛化证据；最终评估以未参与拟合的测试区为准。')
page('残差空间结构与高负担网格')
fig('03_test_maps.png',6.8)
p('地图仅展示227个测试格，灰色区域没有在此图中评估。残差定义为观测−预测；正残差表示低估，负残差表示高估。开发区拟合值和边界外推值在GIS结果中另有角色标签，不能混入测试图或测试指标。')
p('测试目标的8近邻Moran’s I为0.6197；基础调参残差I=0.3039，增强调参残差I=0.2996，两者p均为0.0001。空间结构得到部分吸收，但剩余误差仍聚集；增强模型并未消除残差空间相关；初始基础模型残差I为0.2603，低于增强调参模型，因此本次只支持预测提升，不支持剩余空间聚集同步下降。4/8/12近邻的完整结果保存在evaluation.json。权重为测试格中心间有向k近邻、行标准化，测试块之间的空隙会形成较长连接。')
p('增强模型测试预测最高10%的23格捕获约30.03%的测试事故负担；与观测最高23格重合15格，即65.22%。这是网格层面的描述性优先筛查表现，不能据此给具体路口提出工程干预结论。')
page('变量贡献与解释边界')
fig('04_validation_importance.png',6.8)
p('使用仅在训练720格拟合的调参模型，在166个验证格上逐字段置换20次，以RMSE增加量表示模型依赖程度。图中误差为置换重复的标准差。这是模型开发后的探索性解释，不是独立测试的特征选择实验。')
imp=list(csv.DictReader((O/'enhanced_validation_permutation_importance.csv').open()))[:5]
table(['增强模型字段','平均RMSE增加','置换标准差'],[[r['feature'],f"{float(r['delta_rmse_mean']):.2f}",f"{float(r['delta_rmse_std']):.2f}"]for r in imp])
p('信号点密度在当前模型中贡献突出，人口密度和商业土地占比也包含预测信息。信号密度可能同时代理道路等级、活动强度和城市中心性；不能解释为“信号导致事故”。相关特征可能分摊重要性，置换也可能生成现实中少见的变量组合，故不将排名当作稳定因果排序。')
p('信号点和Caltrans功能分类是当前快照，未证实2017–2021始终一致；信号点也不等同于经过全量实地核验的历史信号交叉口。道路弯曲指标是线长/端点距离的分段代理，对道路切段方式敏感，不能称为工程测量曲率。')
page('稳定性检查与不确定性')
fig('06_development_sensitivity.png',6.8)
p('另在886个开发格上，按固定5km块使用101、202、303三个种子重分训练与评估区；外部测试格完全不参与。这些不同划分的目标分布不同，其RMSE不可直接当作同一测试的重复结果。增强模型在三种划分中均优于基础模型，但绝对误差随区域变化较大。')
p('在种子101划分中，剔除距评估格中心不超过1000m的训练格，训练格由668减至576。增强模型RMSE由96.28变为98.28，基础模型由113.26变为118.61。该检查显示结论并非完全依赖紧邻训练格，但1km中心间隔不是对更远空间相关的完整排除。')
p('额外RF种子7与99在原训练/验证划分上，增强模型验证RMSE为130.17和129.60，接近主种子的129.42。所有敏感性结果仅用于描述，未用于继续修改参数或最终测试结果。')
p('对最终测试5km块进行2000次成对有放回重采样，增强减基础的RMSE差异95%分位区间为[−67.77, 2.81]起/格，MAE差异为[−31.19, 1.66]，R²差异为[−0.020, 0.476]。区间跨0，不能宣称差异在常用95%水平下稳定为正收益。该区间条件于当前划分、已训练模型和有限测试块，并未重新拟合模型，也不是全市随机抽样推断。')
p('针对2021年记录数异常偏低，保留同一推荐模型和参数，将目标改为2017–2020四年总数作预先声明的敏感性检查：测试R²=0.734，RMSE=89.47。四年与五年目标量纲规模不同，不能用更小RMSE宣称更好模型；该检查也不能修复或证明2021事故完整性。')
page('官方HIN背景对照与数据限制')
fig('07_HIN_context.png',6.7)
p('官方2024 High Injury Network仅作背景对照。模型预测最高的23个测试格中，22格有HIN线段，比例95.65%；全部测试格相应比例为48.90%。这是1km网格与任意HIN线段相交的粗粒度重合，可能受道路密度和城区位置影响。')
p('HIN针对死亡与重伤道路，模型针对全部公开记录事故；两者目标不同，而且HIN利用重叠历史事故期，因此不能作为独立真值或声称获得95.65%的模型准确率。HIN没有进入任何训练特征、参数选择或主评估指标。')
p('其他限制：事故公开坐标存在定位精度问题；人口假设在完整BG面积内均匀分布，包含水域且MOE传播近似；土地利用、信号与功能分类快照存在时间不一致；拓扑路口不保证物理平交；空间块没有在主划分中设置距离缓冲。结果适用于当前记录、空间单元和研究设计。')
page('年度记录与项目复现')
fig('08_annual_records.png',6.3)
p('清理后市内事故按年合计在图中列示；原始公开接口下载量2017至2021分别为57727、57159、56628、42385、18796。当前下载已与接口逐年计数核对，但这只证明提取完整，不能证明真实世界事故上报完整。2021年的低计数仍限定五年总负担的解释，不能据此推断交通安全显著改善。')
sub('交付与复现')
p('模型：05_models/rf_project_v1保留初始、调参、训练区解释模型以及2017–2020敏感性模型。推荐增强模型在886个开发格拟合；测试格始终未进入其拟合。GIS：04_outputs/rf_project_v1/grid_predictions_1000.gpkg含网格预测与HIN图层，CSV及WGS84 GeoJSON一并保存。')
p('训练协议、候选参数、5折ID清单、冻结选择、逐折得分、验证置换重要性、敏感性、空间块bootstrap、完整指标和校验结果均位于04_outputs/rf_project_v1。独立检查重载每个最终模型重新计算预测和指标，并核对每棵树的开发样本总权重为886；原始数据SHA256和230536事故守恒通过。')
p('复查现有结果：python 03_scripts/pretraining/verify_trained_project.py。生成地图：python 03_scripts/pretraining/export_project_results.py。预测：python 03_scripts/pretraining/predict_frozen_rf.py --input 已聚合特征.csv --output 新输出.csv。使用项目.runtime中的GIS及机器学习依赖。训练入口run_project_training.py禁止覆盖已完成测试的同名运行；未来扩展研究必须另建运行并声明已有测试结果已被查看。')
page('数据来源与方法参考')
for t in ['LAPD https://data.lacity.org/resource/d5tf-ez2w.json','Census TIGER2021 https://www2.census.gov/geo/tiger/TIGER2021/','ACS B01003 https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/acsdt5y2021-b01003.dat','LA land use https://maps.lacity.org/lahub/rest/services/City_Planning_Department/MapServer/7','Caltrans https://geodata.dot.ca.gov/arcgis/rest/services/chhighway/CRS_Functional_Classification/FeatureServer/0','Signals https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/30','HIN2024 https://maps.lacity.org/arcgis/rest/services/Mapping/NavigateLA/MapServer/172','RF及置换解释 https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html ; https://scikit-learn.org/stable/modules/permutation_importance.html','尺度方法 Chen et al. 2019 https://doi.org/10.1371/journal.pone.0225139 ; 研究背景 Bao et al. 2017 https://doi.org/10.1016/j.aap.2017.06.012']:
 para=p(t);para.paragraph_format.space_after=Pt(3)
 for r in para.runs:r.font.size=Pt(9)
header=sec.header.paragraphs[0];header.text='SSCI 575  洛杉矶交通事故空间负担预测';header.style='Normal'
for r in header.runs:r.font.size=Pt(8)
f=sec.footer.paragraphs[0];f.alignment=2;f.add_run('SSCI 575  |  ');fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
for r in f.runs:r.font.size=Pt(9)
out=R/'06_reports/SSCI575_Final_Project_Report.docx';D.save(out);(R/'06_reports/SSCI575_Final_Project_Report.txt').write_text('\n'.join(p.text for p in D.paragraphs),encoding='utf-8');print(out)
