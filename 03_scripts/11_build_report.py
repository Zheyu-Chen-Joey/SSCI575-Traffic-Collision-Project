from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from pathlib import Path
import csv,json
ROOT=Path.cwd();d=Document();sec=d.sections[0];sec.page_height=Inches(11.7);sec.page_width=Inches(8.3);sec.top_margin=sec.bottom_margin=Inches(.7);sec.left_margin=sec.right_margin=Inches(.75)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
 st=d.styles[name];st.font.name='Calibri';st._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');st.font.color.rgb=RGBColor(0,0,0)
 st.font.size=Pt(10.5 if name=='Normal' else 17 if name=='Heading 1' else 12 if name=='Heading 2' else 25 if name=='Title' else 9 if name=='Caption' else 12)
 st.paragraph_format.space_after=Pt(5);st.paragraph_format.line_spacing=1.12
 for border in list(st.element.xpath('.//w:pBdr')):border.getparent().remove(border)
normal=d.styles['Normal'];normal.paragraph_format.widow_control=True
foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=foot.add_run('SSCI 575  |  ');run.font.size=Pt(8)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');foot._p.append(f)
def p(t,style=None):return d.add_paragraph(t,style)
def h(t):d.add_heading(t,level=1)
def sub(t):d.add_heading(t,level=2)
def page(t):d.add_page_break();h(t)
def table(headers,rows,widths=None,size=9):
 t=d.add_table(rows=1, cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for i,x in enumerate(headers):t.rows[0].cells[i].text=str(x)
 rep=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(rep)
 for row in rows:
  cells=t.add_row().cells
  for i,x in enumerate(row):cells[i].text=str(x)
 for k,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
  for i,c in enumerate(row.cells):
   if widths:c.width=Inches(widths[i])
   c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;tcpr=c._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
   tcpr.append(borders);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DFE8EF' if k==0 else 'F4F6F8' if k%2==0 else 'FFFFFF');tcpr.append(sh)
   mar=OxmlElement('w:tcMar')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:w'),'80');e.set(qn('w:type'),'dxa');mar.append(e)
   tcpr.append(mar)
   for par in c.paragraphs:
    par.paragraph_format.space_after=Pt(2);par.paragraph_format.space_before=Pt(2);par.paragraph_format.line_spacing=1.05
    for r in par.runs:r.font.size=Pt(size);r.bold=k==0
 return t
def pic(path,width,caption):
 d.add_picture(str(ROOT/path),width=Inches(width));d.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER;p(caption,'Caption')
p('洛杉矶交通事故网格尺度选择与验证报告','Title');p('SSCI 575  数据准备 方法实施与验证结果','Subtitle');p('研究时期 2017—2021年  |  报告日期 2026年11月6日')
h('摘要与分析范围')
p('本报告整理 City of Los Angeles 交通事故项目的数据获取与清理、31种规则网格的尺度搜索，以及针对1100米候选尺度开展的拟合距离、网格原点和空间块删除验证。当前证据支持将1100米作为后续研究的工作尺度，但尚未证明它是唯一或全局最优尺度。原25公里拟合所得约39.3公里变程，没有得到持续经验平台的直接支持。')
p('本阶段完成的是建模前的空间尺度诊断。Random Forest尚未训练，完整解释变量表尚未构建；本报告中的拟合误差不是交通事故预测模型的测试误差。数据文件中的最终尺度字段仍为空，工作候选为1100米。')
sub('研究设计')
p('预测目标为每个网格内2017—2021年记录的事故总数。计划在尺度确定后，以相同空间验证设计比较基础六类变量与加入道路设计变量的增强特征集，算法均为Random Forest Regression。研究解释预测关联，不进行因果推断。')
sub('本阶段主要成果')
table(['成果','已完成内容'],[['数据准备','下载232695条事故记录，清理后保留230536条；保存道路、市界、土地利用及信号等数据。'],['多尺度分析','生成500—5000米、步长150米的31套网格，保留零事故格；逐尺度总量与几何检查通过。'],['补充验证','扩展距离拟合140组；四种原点检查；候选附近空间块删除影响分析。'],['当前限制','2021年事故完整性待核查；人口数值与带日期交通流量值尚缺；平台模型存在距离依赖。']],[1.05,5.7])
p('研究依据：项目更新计划书；方法背景：Chen等（2019）[1]。具体分箱、留出、边界阈值及参数约束为本项目的实施选择，不声称逐项复现原论文。')
page('一 数据集与用途')
p('尺度选择仅使用清理后的事故点和市界；其余数据用于后续解释变量及覆盖审计。下表清楚区分已经取得的空间几何与尚未取得的属性数值。数据来源编号对应第八节。')
table(['数据集','版本或时段','实际获取与清理','用途与限制'],[
 ['LAPD Traffic Collision [2]','2017—2021','原始232695条；保留230536条','事故计数与尺度诊断；旧接口停止更新，2021完整性待核查。'],
 ['City Boundary [3]','访问时快照','官方市界；已修复有效性并投影','界定City of Los Angeles；不是洛杉矶县界。'],
 ['TIGER Roads [4]','2021 洛杉矶县','市界裁剪后28364条','道路长度、等级及曲折度代理；MTFCC不直接等同城市arterial。'],
 ['TIGER Block Groups [5]','2021 加州','筛选县06037并与市界相交后2941个','已取得几何；仍保留完整相交BG，未等同市内人口。'],
 ['ACS 5 year [6]','2021 ACS5','API返回Missing Key网页，未取得人口数值','计划使用B01003人口估计和误差界；缺失不填0。'],
 ['General Plan Land Use [7]','访问时快照','下载50644；市界裁剪后50643个','计划计算类别面积占比；需核对ADOPTDATE与UPDATE_。'],
 ['LADOT Traffic Counts [8]','访问时快照','下载6820；市界裁剪后6800个位置对象','几何与报告链接已取得，缺少直接可用计数值和日期。'],
 ['LADOT Signal Locations [9]','访问时快照','下载5592；市界裁剪后5506个点','后续信号密度候选；需核对是否代表研究期全量信号。']],[1.35,.95,1.9,2.55],8.5)
sub('未纳入或尚未完成的数据')
p('计划书引用的Vision Zero Conventional Signals接口[10]本次仅返回60个对象，不能当作全市信号总量。限速数据尚未完成覆盖审计，视距未纳入；这两项不参与当前尺度诊断。交通计数位置在1100米网格上的覆盖率为68.86%，它不是具有2017—2021有效交通数值的覆盖率。')
page('二 清理与网格构建')
table(['事故清理步骤','数量'],[['2017—2021原始记录','232695'],['重复dr_no','0'],['缺失或粗坐标范围无效','403'],['有效坐标但位于市界外','1756'],['最终市界内记录','230536']],[4.8,1.95])
p('按date_occ筛选研究期，按dr_no识别重复；读取location_1中的经纬度，先检验经度−119至−117、纬度33至35，再用市界进行空间筛选。重合坐标不自动去重，因为不同事件可能位于同一位置。市界内记录总数不是所有事故的无遗漏普查。')
p('统一投影为NAD83 / UTM zone 11N（EPSG:26911），以米构建方格。固定原点为E=345000、N=3730000米，方向与投影坐标轴一致。尺度s=500+150k，k=0…30。按半开区间分配点，边界裁剪后仍保留零事故格。全部31尺度的事故总数均为230536，几何有效性检查通过。')
p('拟合仅使用市界面积占原方格至少80%的格；地图输出保留全部市界相交格。1100米共有1230格，其中656格同时满足训练区域与边界面积条件。')
pic(Path('04_outputs/figures/candidate_grid_1100.png'),2.1,'图1  1100米候选网格的2017—2021年事故总数。图中含预留区域，仅作全域描述；预留区域目标未进入半变异拟合。')
page('三 半变异函数与尺度选择方法')
sub('从网格内统计到网格间比较')
p('第一步计算每格事故数Z；第二步比较距离相近的网格对，其事故数差异是否也相近。网格边长决定统计单元大小，距离h则表示两个网格中心之间相隔多远，两者不是同一个参数。')
p('经验半变异函数：γ(h) = Σ[Z(xᵢ) − Z(xⱼ)]² / [2N(h)]。其中N(h)为距离落入相应分箱的网格对数，坐标为完整规则方格中心，事故数不做面积归一化。')
table(['参数','本项目解释'],[['Nugget  块金值 c₀','模型在趋近零距离时的半变异截距；不是事故数量本身。'],['Sill  总基台值 c₀+c₁','模型达到平台时的半变异水平；c₁为partial sill。'],['Range  变程 a','球状模型达到平台的距离；与1100米网格边长不同。'],['NSR  块金基台比','c₀/(c₀+c₁)。依赖拟合参数；近零NSR也可能由参数触界产生。']],[1.7,5.05])
sub('拟合与主选择规则')
p('主分析采用球状模型：t=h/a；t<1时γ=c₀+c₁(1.5t−0.5t³)，t≥1时γ=c₀+c₁。0—25公里划为25个距离箱，每箱至少30对，按每箱配对数加权最小二乘并使用多初值。参数非负，主分析Range上界50公里。')
p('每尺度最多随机抽2500格，种子575。1100米仅有656个合格训练格，因此全部使用。候选规则为首个稳定局部低点，结合样本数、零事故率、拟合质量和覆盖诊断，不机械选择全曲线最小值。')
sub('空间留出与辅助诊断')
p('预先以5公里块划分空间留出：块索引bx、by相对固定原点计算，(bx×73856093+by×19349663) mod 5 = 0的块预留。凡网格与预留块相交，整格排除出尺度拟合，避免边界格带入测试目标。主诊断使用8近邻行标准化Moran’s I与199次置换。此留出规则未提供相邻区域之间的空间缓冲。')
p('当Range接近约束上界、nugget接近零或训练格过少时，不把数值低点当作可靠最佳尺度。较粗网格因与预留块交叠而丢失大量训练样本，须保留这一分析设计造成的限制。')
page('四 初始尺度搜索与原点敏感性')
pic(Path('04_outputs/figures/nsr_scale.png'),6.65,'图2  主分析NSR随网格边长变化。橙色标记表示拟合不稳或训练格不足100；未达到30格的尺度不强行拟合。竖线为1100米候选。')
table(['边长 m','训练格数','零事故率','NSR','主拟合Range km'],[['950','899','14.18%','0.2704','26.7'],['1100','656','11.79%','0.2240','39.3'],['1250','563','11.95%','0.2259','31.1'],['1400','385','9.82%','0.1741','24.4'],['1550','307','9.91%','0.0866','21.1']],[1.0,1.2,1.3,1.2,2.05])
p('1100米比1250米的NSR低约0.0019，是首个局部低点而非全局最低。1100米主诊断Moran’s I约0.7437、置换p=0.005，说明所用邻接定义下存在空间自相关；它不证明1100米优于其他尺度。')
p('在800—1850米范围测试四种原点：(0,0)、(s/2,0)、(0,s/2)、(s/2,s/2)。其中三种在1100米出现局部低点，仅Y方向平移时低点移至1700米且其Range触及上界。固定原点可明确分析设计，但不能保证唯一低点。')
page('五 扩展距离与平台验证')
p('针对39.3公里Range超出原25公里观察范围的问题，将最大拟合距离扩展至35、45、55、65公里。保持1公里分箱、空间留出与面积阈值一致，比较球状与指数模型；指数参数a表示约95%的有效变程。为检验约束依赖，将Range上界扩展至150公里。')
p('本次在500—2450米共14种尺度上开展5种距离×2种模型，共140组拟合；这是候选邻域的补充验证，未用新设定重跑全部31尺度。')
pic(Path('04_outputs/figures/range_validation_1100.png'),5.1,'图3  黑点为经验半变异，曲线为不同最大距离的球状拟合；下图为网格对数。黑点在约35—36公里达到峰值后下降，没有形成持续平台。35公里拟合的150公里Range触及上界。')
p('更远距离网格对减少，所比较的城市区域组合也改变。趋势、方向性与城市形状均可能影响曲线，本次未分离各因素的作用。不能通过不断延长拟合距离，自动获得更可靠的平台。')
page('六 验证结果与尺度判断')
table(['最大距离 km','Range km','NSR','标准化RMSE','诊断'],[['25','39.3','0.2240','0.0616','Range超观察范围'],['35','150.0','0.0572','0.0775','Range触及上界'],['45','42.4','0.1178','0.1831','拟合范围内但非持续平台'],['55','35.4','0.1439','0.4546','长距离下降导致失配'],['65','32.0','0.1716','0.5502','长距离下降导致失配']],[1.05,.95,.85,1.15,2.75])
p('上述RMSE为各距离箱未加权残差RMSE除以训练格事故数方差；各行拟合数据范围不同，不能当作同一预测测试集上的模型优劣比较。球状模型在五种范围均出现1100米首个局部低点，但35公里拟合触界，不能视为可靠支持；指数模型的低点位置仍会变化。')
sub('逐次删除空间块的影响检查')
p('在950、1100、1250、1400、1550米上，按中心所属5公里训练块逐次删除一个块并重新拟合。对950、1100、1250米都有记录的53个共同块，检查1100米是否同时低于两侧尺度。')
table(['拟合最大距离','保留1100米局部低点','解释'],[['25公里','29/53','原浅低点对删除局部样本敏感'],['45公里','52/53','此设定下邻近尺度排序更稳定'],['55公里','49/53','大部分保留，但整条曲线拟合变差']],[1.4,1.9,3.45])
p('这些次数是空间块删除影响诊断，不是独立重复实验、置信区间或“最佳概率”。不能因45公里设置更支持1100米，就追溯替换原主参数。该测试比原点平移更直接检查局部样本影响，但不取代正式的不确定性估计。')
sub('建议采用的研究表述')
p('在固定网格原点与主分析参数下，1100米对应NSR曲线的首个局部最小值。扩展距离与空间块删除检查提供额外支持，因此建议将其作为后续建模的工作尺度；该选择仍具有模型、距离范围与网格位置依赖性，未被证明为唯一或全局最优。')
p('原始配置final_scale_m仍为空，候选字段为1100；本报告不自动释放模型门槛。尺度诊断、数据准备与后续RF预测验证需分别报告。')
page('七 数据限制与后续建模衔接')
sub('事故记录与时间一致性')
table(['年份','接口记录数'],[['2017','57727'],['2018','57159'],['2019','56628'],['2020','42385'],['2021','18796']],[3.5,3.25])
p('上表为市界清理前的年度下载总数。2021年各月均有记录，但全年相对前期显著减少，尚未核实是报告覆盖、系统或真实变化所致。旧接口说明已迁移RMS且停止更新，不能仅据此断言2017—2021记录完整，也不能将2021下降直接解释为安全改善。公开坐标存在定位精度限制。')
sub('解释变量尚需的处理')
p('人口：取得2021 ACS5 B01003估计与误差界并核对GEOID；面积加权分配需披露人口均匀分布假设。交通：由位置报告取得实际计数、日期、单位，审计研究期覆盖；不得把报告位置数当作交通暴露量。土地利用与信号：核查研究期有效性，当前快照不能自动代表2017—2021。')
p('道路：已计算裁剪线长度及实际长度与端点直线距离之比，闭合或端点距≤1米时记缺失。该指标是线段曲折度代理，会受道路分段影响，不等同物理曲率。交叉口需拓扑和立交审计，不能将全部线端点计作交叉口。')
sub('下一阶段的分析边界')
p('先完成数据门槛，再构造基础交通流量、道路密度、交叉口密度、道路类型、人口密度和土地利用六类变量；增强特征加入可审计的道路曲折度、道路等级占比及信号密度。限速需覆盖合格后再加入；不构建人口衍生rurality或无可靠数据的视距。')
p('若需进一步统计确认平台模型，优先检查大尺度空间趋势与方向性，并对边界阈值开展敏感性分析。最终RF使用固定空间分割比较基础与增强特征，评价R²、RMSE、MAE及残差Moran’s I；最终测试集不得用于反选尺度或调参。')
sub('本阶段完成状态')
p('已完成下载快照、空间清理、31网格守恒与几何检查、初始NSR搜索、Moran诊断、原点检查、距离与模型比较及空间块删除分析。尚未完成完整特征表、RF训练、预测精度评估、正式尺度置信区间和研究期数据完整性证明。')
page('八 来源与复现索引')
p('来源访问与下载记录见00_admin/file_manifest.json；原始文件保留在01_data/raw，包含失败响应，不能把该目录所有文件都视为有效数据。以下URL与本地源元数据对应；引用[1]仅提供NSR尺度研究背景。',None)
refs=[
 '[1] Chen L, Gao Y, Zhu D, Yuan Y, Liu Y. 2019. Quantifying the scale effect in geospatial big data using semi-variograms. PLOS ONE 14(11): e0225139. https://doi.org/10.1371/journal.pone.0225139',
 '[2] LAPD Traffic Collision历史接口与说明 https://data.lacity.org/api/views/d5tf-ez2w.json；数据 https://data.lacity.org/resource/d5tf-ez2w.json',
 '[3] 洛杉矶市界 https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/7',
 '[4] Census TIGER 2021 Roads https://www2.census.gov/geo/tiger/TIGER2021/ROADS/tl_2021_06037_roads.zip',
 '[5] Census TIGER 2021 Block Groups https://www2.census.gov/geo/tiger/TIGER2021/BG/tl_2021_06_bg.zip',
 '[6] ACS 2021 5 year https://api.census.gov/data/2021/acs/acs5；请求变量NAME、B01003_001E、B01003_001M，state:06 county:037，block group:*。',
 '[7] General Plan Land Use https://maps.lacity.org/lahub/rest/services/City_Planning_Department/MapServer/7',
 '[8] LADOT Traffic Counts位置 https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/22',
 '[9] LADOT Signal Locations https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/30',
 '[10] Vision Zero Conventional Signals https://services1.arcgis.com/tp9wqSVX1AitKgjd/arcgis/rest/services/Vision_Zero__Improvements/FeatureServer/2']
for t in refs:
 par=p(t)
 for run in par.runs:run.font.size=Pt(8.5)
sub('可复现材料')
p('原计划书：00_admin/source/SSCI575_Project_Update.docx。数据校验：00_admin/file_manifest.json。主配置：02_config/analysis.json与spatial_holdout.json。Python依赖版本：requirements.txt。脚本须从项目根目录运行。')
p('主流程：01_download.py → 03_download_predictors.py → 02_clean_and_grid.py → 04_clean_predictors.py。验证：05_sensitivity.py、07_origin_sensitivity.py、08_finalize.py、09_verify.py、10_validate_range.py（均位于03_scripts）。人口API失败可能中止初始下载脚本，应先读取其状态说明。')
p('主要输出：04_outputs/grid_search下的scale_diagnostics.csv、fit_sensitivity.csv、origin_sensitivity.csv；04_outputs/range_validation下的extended_lag_fits.csv、leave_one_block_out.csv、empirical_*.csv与local_minima.json；清理与守恒审计见04_outputs/qa。')
page('附录 31种网格的主分析诊断')
p('主参数为25公里球状拟合。零事故率按全部市界相交格计算；训练格数为面积阈值及空间留出筛选后数量。表中“有效”仅代表脚本拟合筛查通过，不代表尺度统计最优；训练格不足100仍需谨慎。')
rows=[]
for r in csv.DictReader(open('04_outputs/grid_search/scale_diagnostics.csv',encoding='utf-8-sig')):
 nsr=float(r['nsr']) if r['nsr'] else float('nan');rows.append([r['scale_m'],str(int(float(r['n_all']))),r['n_fit'],f"{float(r['zero_rate'])*100:.1f}%",'—' if nsr!=nsr else f'{nsr:.4f}',{'ok':'有效','unstable_fit':'拟合不稳','too_few_cells':'样本不足'}[r['status']]])
t=table(['边长 m','全域格数','训练格数','零事故率','NSR','拟合状态'],rows,[1.0,1.1,1.1,1.1,1.1,1.35],8)
for row in t.rows:
 for c in row.cells:
  for e in c._tc.xpath('.//w:tcMar/w:top | .//w:tcMar/w:bottom'):e.set(qn('w:w'),'30')
  for par in c.paragraphs:par.paragraph_format.space_after=Pt(0);par.paragraph_format.space_before=Pt(0);par.paragraph_format.line_spacing=1.0
p('注：4100—4850米各尺度合格训练格不足30，未强行拟合。5000米仅30格，即使返回拟合值也不作为可靠最优候选。全部31种网格已生成并通过事故总量守恒检查。','Caption')
out=ROOT/'06_reports/SSCI575_Grid_Methods_and_Validation_Report.docx';d.save(out);print(out)


