from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path.cwd();O=R/'04_outputs/rf_spatial_v5';ev=json.loads((O/'evaluation.json').read_text());ci=json.loads((O/'bootstrap_intervals.json').read_text());D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
for n in ['Normal','Title','Heading 1','Heading 2']:
 s=D.styles[n];s.font.name='Arial';s.font.color.rgb=RGBColor(0,0,0);s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
D.styles['Normal'].font.size=Pt(10.5);D.styles['Normal'].paragraph_format.line_spacing=1.1;D.styles['Normal'].paragraph_format.space_after=Pt(7)
for n,z in [('Title',21),('Heading 1',16),('Heading 2',12)]:D.styles[n].font.size=Pt(z)
for e in list(D.styles.element.iter(qn('w:pBdr'))):e.getparent().remove(e)
def p(t):D.add_paragraph(t)
def h(t):D.add_heading(t,1)
def page(t):h(t);D.paragraphs[-1].paragraph_format.page_break_before=True
def table(head,rows):
 t=D.add_table(rows=1,cols=len(head))
 for j,x in enumerate(head):t.rows[0].cells[j].text=str(x)
 for r in rows:
  c=t.add_row().cells
  for j,x in enumerate(r):c[j].text=str(x)
 for i,r in enumerate(t.rows):
  for c in r.cells:
   pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b)
   if i==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF5');pr.append(sh)
   for para in c.paragraphs:
    para.paragraph_format.space_after=Pt(4)
    for run in para.runs:run.font.size=Pt(10);run.bold=i==0
D.add_paragraph('随机森林空间位置扩展与验证报告','Title');p('SSCI 575  |  City of Los Angeles  |  2017–2021记录事故  |  1 km网格')
p('用户已明确允许将网格中心坐标加入增强随机森林。本轮在原16个协变量之外增加2个位置字段，比较直接坐标RF与位置专用RF残差校正，并加入实际网格间距1km的缓冲验证。开发区选出的直接坐标RF在已被查看的旧测试区域上，将RMSE由97.98降至92.89、MAE由64.96降至59.86，分别降低5.20%和7.86%，R²由0.732升至0.759。')
rows=list(csv.DictReader((O/'comparison_metrics.csv').open()))
table(['旧区域探索性对照','RMSE','MAE','R²','残差Moran I'],[[{'Original V1':'原RF','V4b blend':'前轮RF组合','Matched no XY':'同参数无坐标','Spatial V5':'新空间版'}[r['model']],f"{float(r['rmse']):.2f}",f"{float(r['mae']):.2f}",f"{float(r['r2']):.3f}",f"{float(r['moran_i']):.4f}"]for r in rows]);D.add_picture(str(O/'figures/01_metric_comparison.png'),width=Inches(6.8))
p('误差大小下降不等于空间聚集下降。新模型残差Moran’s I=0.3317，高于原0.2996，9999次置换双侧p=0.0001，仍有显著聚集。本轮不能宣称同时解决了空间误差，也不能把已反复查看的旧区域重新包装成独立测试。')
p(f"对固定模型及旧测试5km块作2000次成对重采样，新减原的RMSE差异95%分位区间为[{ci['Original V1_delta_rmse']['lower']:.2f}, {ci['Original V1_delta_rmse']['upper']:.2f}]起/格，MAE差异为[{ci['Original V1_delta_mae']['lower']:.2f}, {ci['Original V1_delta_mae']['upper']:.2f}]。当前块重采样中下降方向一致，但区间条件于已选模型和已查看区域，不包含重复训练或选模不确定性，不能替代新的外部验证。")
page('模型设计与选择过程')
p('位置是已知网格几何，不是邻格实际事故数。使用EPSG:26911中心坐标，将东坐标减345000、北坐标减3730000后换算为公里，形成东向和北向位置趋势字段。没有引入目标空间滞后、HIN、交通流量、限速、视距或rurality。固定网格、原始事故与全体零事故格不变。')
p('直接位置分支评估36种配置：4个无坐标对照，以及土地利用原始/条件组成、原计数/设施密度平方根缩放与8组RF参数形成的32个位置配置。使用原训练720格的5km分组5折CV，同时计算普通CV和缓冲CV。选模以缓冲CV与验证区为依据，不使用旧测试目标。')
p('缓冲不是中心点距离。对1km完整方格计算最短边界距离，凡训练格距评估格不超过1000m均剔除。各折保留481、466、477、455、452个训练格；评估格不变。原市界裁切碎格不能使完整方格间距更小，因此此规则保守地保证真实空间间隔。')
p('训练CV筛选后最多5个位置候选进入166格验证区，同时检查单种子42和种子7/42/99的固定等权RF平均。要求验证RMSE改善，MAE和绝对残差Moran不劣于原模型；按事先记录的RMSE与Moran综合目标选择。模型17_ensemble在旧区域评估前冻结。两分支的汇总推荐只读取开发区指标。')
table(['新模型项目','设置'],[['RF集成','3个种子7 42 99 等权平均'],['每个森林','500树 最大深度16 叶最少5 分裂最少10'],['特征抽样与准则','max_features0.5 平方误差'],['土地组成','原始市界裁切格面积比例'],['目标缩放','除以设施点密度加1的平方根 拟合后乘回计数'],['输入','原16字段 加cx和cy 共18字段'],['最终拟合','886个开发格 旧区域227格从未拟合']])
p('设施点变量沿用已记录的混合信号/速度反馈位置快照代理，并非纯历史信号交叉口清单。目标缩放是统计处理，不是车辆暴露调整后的事故率。当前模型仍是RF算法的多种子平均，没有引入其他机器学习算法。')
page('空间验证与坐标消融')
D.add_picture(str(O/'figures/04_coordinate_ablation.png'),width=Inches(6.8))
p('消融严格匹配RF参数、目标缩放、土地处理和3个随机种子，仅切换坐标。旧区域RMSE从无坐标95.49降至有坐标92.89，验证区从93.04降至91.38；但1km缓冲训练折外RMSE从96.43升至99.61。坐标的帮助依赖评估场景，不能说其普遍改善空间泛化。旧区域同参数对照的成对块区间也不构成全新独立验证。')
transfer=list(csv.DictReader((O/'geographic_transfer_checks.csv').open()))
table(['开发区地域留出','模型','训练/评估格','RMSE','MAE'],[[{'north20pct':'北侧20%','east20pct':'东侧20%'}[r['region']],{'no_position_anchor':'原RF','selected_spatial':'新空间版'}[r['model']],r['n_fit']+'/'+r['n_eval'],f"{float(r['rmse']):.2f}",f"{float(r['mae']):.2f}"]for r in transfer])
p('上述地域检查完全排除原测试区；以开发区坐标的80%分位点划出连续北侧或东侧区域，再保证1km完整方格间隔。新模型在东侧明显改善，在北侧略有退步。北侧与东侧目标规模不同，不能跨区域直接比较绝对RMSE大小。')
p('另一路位置专用残差RF评估48个校正配置及原模型对照：基础RF仅用原16字段，校正RF仅用位置，并用外层缓冲CV及内层3折残差标签避免外层评估目标泄漏。没有配置通过预先规定的训练RMSE、MAE与Moran联合门槛，因此未替换原模型，也未依据旧区域分数重新调节该分支。')
p('土地利用完全缺失的14个旧区域格，原RMSE167.34，新模型167.42，几乎未变；其余213格RMSE从91.61降至85.75。这表明位置没有补齐缺失土地利用数据，输入质量问题仍需实质修复。')
page('全市实际值预测值与残差')
D.add_picture(str(O/'figures/03_full_city_comparison.png'),width=Inches(6.8))
p('图示1113个合格网格；黑框标出原227个评估格，其余有色格为开发区拟合预测。灰色表示不进入评估的边界格。完整城市地图便于展示格局，但不能用开发区颜色较浅来证明独立预测准确。实际与预测使用同一计数色标；残差为实际减预测，红为低估，蓝为高估。')
D.add_picture(str(O/'figures/02_legacy_residual_comparison.png'),width=Inches(5.6))
page('交付复现与使用边界')
p('本轮是用户明确授权的原研究设计扩展。原方案v1及历史报告不覆盖；空间版保存为当前扩展候选。它适合当前城市覆盖内的历史负担回溯建模，尚不支持新的城市、未覆盖地区或未来年份的无条件外推，也不是因果模型。')
p('完整结果：04_outputs/rf_spatial_v5。包括36配置CV、缓冲折ID、验证预测、冻结选择、同参数消融、地域留出、邻居数4/8/12的Moran检查、成对空间块区间、预测表、GPKG和WGS84 GeoJSON。位置残差分支：04_outputs/rf_spatial_residual_v5b。')
p('扩展模型：05_models/rf_spatial_v5/spatial_frozen_rf.joblib。输入契约：同目录input_contract.json。加载前需把03_scripts/pretraining加入Python模块路径，以找到rf_spatial_model.py和rf_coverage_scaled_model.py。模型包含训练内插补、编码、固定坐标变换、目标缩放与3个RF。')
p('独立校验：python 03_scripts/pretraining/export_rf_spatial_v5.py。重载模型预测、指标、位置换算、886格拟合样本权重以及所有1km缓冲间隔已通过检查。全部1473格事故总数仍为230536。原始下载快照没有被覆盖或删格。')
p('由于旧区域已被多轮查看，下一项关键验证是新时段或尚未参与研究的空间区域，而非继续在同一区域追逐分数。新的外部验证还需核实事故报告规则和道路/设施/土地利用的时间一致性。即使新的块重采样区间不跨0，也不能消除已有的研究选择与复用影响。')
p('方法与数据说明：02_config/spatial_extension_v5.json记录用户授权及研究扩展；06_reports/Signal_Source_Semantics_Clarification.txt记录设施点语义。官方设施图层：https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/30?f=pjson 。所有性能数字由当前JSON/CSV结果生成。')
f=sec.footer.paragraphs[0];f.alignment=2;f.add_run('SSCI 575  |  ');e=OxmlElement('w:fldSimple');e.set(qn('w:instr'),'PAGE');f._p.append(e)
out=R/'06_reports/RF_Spatial_Extension_v5.docx';D.save(out);(R/'06_reports/RF_Spatial_Extension_v5.txt').write_text('\n'.join(x.text for x in D.paragraphs),encoding='utf-8');print(out)
