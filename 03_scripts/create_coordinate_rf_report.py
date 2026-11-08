"""Five-page report for the frozen coordinate-blended RF champion."""
from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parents[1];P=R/'04_outputs/rf_spatial_v5';C=P/'orientation_optimization';ev=json.loads((P/'evaluation.json').read_text());change=json.loads((C/'improvement_summary.json').read_text());ci=json.loads((P/'bootstrap_intervals.json').read_text());contract=json.loads((R/'05_models/rf_spatial_v5/input_contract.json').read_text());metrics=list(csv.DictReader((P/'comparison_metrics.csv').open()));old=next(x for x in metrics if x['model']=='Previous coordinate RF');new=next(x for x in metrics if x['model']=='Current best RF')
D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
for name in ['Normal','Title','Heading 1']:
 s=D.styles[name];s.font.name='Arial';s.font.color.rgb=RGBColor(0,0,0);s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
D.styles['Normal'].font.size=Pt(10.5);D.styles['Normal'].paragraph_format.line_spacing=1.1;D.styles['Normal'].paragraph_format.space_after=Pt(7);D.styles['Title'].font.size=Pt(21);D.styles['Heading 1'].font.size=Pt(16)
for x in list(D.styles.element.iter(qn('w:pBdr'))):x.getparent().remove(x)
def p(t):D.add_paragraph(t)
def page(t):
 D.add_heading(t,1);D.paragraphs[-1].paragraph_format.page_break_before=True
def table(head,rows):
 t=D.add_table(rows=1,cols=len(head))
 for j,x in enumerate(head):t.rows[0].cells[j].text=str(x)
 for row in rows:
  for cell,x in zip(t.add_row().cells,row):cell.text=str(x)
 for i,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader')
  if i==0:pr.append(repeat)
  for cell in row.cells:
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(4)
    for run in para.runs:run.font.size=Pt(10);run.bold=i==0
   if i==0:
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EEF5');cell._tc.get_or_add_tcPr().append(shade)
D.add_paragraph('随机森林多方向组合优化结果报告','Title')
p('SSCI 575  |  City of Los Angeles  |  2017–2021记录事故  |  固定1km网格')
p('本轮保留0度、45度、60度坐标表达的局部加权RF组合，权重为25%、25%、50%。固定候选通过开发空间检查后，在原227格探索性比较区将RMSE从81.02降至80.63、MAE从53.24降至53.05。区域已反复使用，收益很小，不能称为新的独立验证或稳定泛化改善。')
table(['原区域指标','前两方向RF','当前三方向RF'],[[label,f'{float(old[key]):.{digits}f}',f'{float(new[key]):.{digits}f}']for label,key,digits in [('RMSE 起/格','rmse',2),('MAE 起/格','mae',2),('R²','r2',4),('残差 Moran I','moran_i',4),('绝对误差90分位','p90_abs_error',2)]])
D.add_picture(str(P/'figures/01_metric_comparison.png'),width=Inches(6.8))
p(f"RMSE下降{change['rmse_reduction_pct']:.2f}%，MAE下降{change['mae_reduction_pct']:.2f}%。123格绝对误差下降、104格上升。中位绝对误差29.03→29.69、平均预测减实际9.79→10.29均退步。残差仍显著聚集，Moran置换p=0.0001。")
page('数据与模型计算')
p('研究目标为2017–2021公开记录的网格事故总数。输入表、事故清理版本、固定原点及1km网格均不变：1473个市界相交格、1113个合格格、230536条有效事故。保留零事故格，人口及土地缺失不填成真实0。')
p('沿用18个输入：道路、人口、土地利用、道路设计及设施代理16字段，加EPSG:26911米制中心cx/cy。没有新增外部数据，不读取邻格真实事故数、HIN、交通流量、限速、视距或rurality。')
p('坐标旋转只改变位置特征表达。原点仍为E345000/N3730000；以公里表示东向e和北向n，固定角度θ使用e′=e cosθ−n sinθ，n′=e sinθ+n cosθ。事故归格、市界、局部模型锚点及高斯距离始终用原坐标，不旋转分析网格。')
table(['设置','当前固定值'],[['方向及权重','0度25% 45度25% 60度50%'],['每方向全局RF','种子7 42 99 各500树'],['每方向局部RF',f"{contract['local_anchor_count']}个局部模型 各200树 种子575"],['RF共同限制','深度16 叶最少5 分裂最少10 特征比例0.5'],['每方向空间权重','10km高斯带宽 20km锚点间距 最近3中心'],['每方向内部组合','25%全局 加75%局部 有效样本数至少40'],['目标处理','按设施密度加1的平方根缩放并还原'],['最终拟合','886个开发格 原227格不参与拟合']])
p('所有组件均为Random Forest，最终为固定凸组合，非新增学习算法。单一joblib文件包含三套RF组件，训练样本相同。10km和20km是权重和中心布局参数，不是分析格大小或半变异range。')
page('开发验证与固定门槛')
p('预设12种方向权重组合，以现有两方向RF为对照。使用0、30、45、60、75度，组合与门槛在拟合前写入protocol.json。同一训练子集共享方向RF预测，各空间折独立拟合。')
p('训练720格沿用固定5km分组五折，并剔除与评估完整方格边界距离不超过1km的训练格，每折保留452–481格。预处理和所有方向RF只拟合折内训练数据。平均折RMSE和MAE均下降后，选最多3项进入166格验证。')
p('验证要求RMSE、MAE均下降且90分位误差不得上升超过2%，再以最低RMSE冻结。入围候选为7、5、8，只有候选8通过，固定为0/45/60度及0.25/0.25/0.5权重。随后才做连续地域留出检查。')
table(['开发检查','前两方向RF','当前三方向RF'],[['五折平均RMSE','92.9041','92.2924'],['五折平均MAE','58.4437','58.0446'],['166格验证RMSE','82.4950','82.4728'],['166格验证MAE','52.3508','52.0701'],['北侧留出RMSE','43.6904','43.4298'],['北侧留出MAE','33.7376','33.6188'],['东侧留出RMSE','135.9205','134.7356'],['东侧留出MAE','87.1665','84.7845']])
p('地域检查只用886个开发格，分别留出北侧和东侧20%范围，并保留完整方格大于1km的间隔。每地域RMSE、MAE不得退步超过5%，两地域比值均值不得超过1.01；本轮两地域两项指标均略改善。验证区RMSE只改善0.0222起/格，不能夸大。')
p('之后拟合886格并对原227格评估冻结候选；保留仍要求该复用区域RMSE、MAE下降且90分位误差不明显退步。因此研究方向和接受规则仍有自适应影响。这些开发地域和原评估格均不再是新的独立测试。')
page('实际预测与残差地图')
D.add_picture(str(P/'figures/03_full_city_comparison.png'),width=Inches(6.8))
p('有色区域为1113个合格格；黑框是原227个评估格，其余为开发区拟合结果，灰色边界格不计指标。实际减预测为残差：红为低估、蓝为高估，白色附近为接近0。全图不能当作全部独立测试。')
D.add_picture(str(P/'figures/02_legacy_residual_comparison.png'),width=Inches(4.7))
p('左为前两方向RF，右为当前三方向RF，前后同格同色标。原区域残差界限保持±341.46，全市保持±517.82，当前结果均在范围内。未平滑残差、修改真实计数或删除困难格。')
page('不确定性与复现')
for metric,label in [('rmse','RMSE'),('mae','MAE')]:
 interval=ci['Previous coordinate RF_delta_'+metric];p(f"2000次成对5km空间块重采样，当前减前两方向RF的{label}差异95%分位区间为[{interval['lower']:.2f}, {interval['upper']:.2f}]起/格。区间包含0，条件于当前模型和已查看区域，不包含选模及重新训练不确定性。")
p('人口面积分配、土地利用缺失、协变量快照年份和事故报告完整性仍有限制。设施密度来自混合信号及速度反馈标志点，不能视为纯历史信号交叉口覆盖。目标缩放不是车辆暴露调整事故率；结果为历史记录负担拟合，不是未来风险或因果效应。')
p('唯一生产模型为05_models/rf_spatial_v5/spatial_frozen_rf.joblib，类型OrientationEnsembleForest。旧冠军只保留哈希校验的冻结预测，模型实体不重复保留，旧版本通过Git历史追溯。原始快照、230536事故记录和固定1km格保持不变。')
p('预测入口：python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 聚合特征.csv --output 新预测.csv。输入仍为18字段，坐标必须为EPSG:26911固定1km网格中心。')
p('固定复现：python 03_scripts/pretraining/train_best_spatial_rf.py --execute-training --output 新模型.joblib。只拟合886开发格，不重新搜索或覆盖现有文件。导出复核：python 03_scripts/pretraining/export_rf_spatial_v5.py。')
p('必要模块包括pipeline_definition、rf_coverage_scaled_model、rf_spatial_model、rf_local_weighted_model、rf_rotated_local_model及rf_orientation_ensemble。逐折指标、折外预测、验证预测、冻结决定、地域检查及逐格改善见04_outputs/rf_spatial_v5/orientation_optimization。')
p('后续优化必须继续把现有区域视为开发证据。可信确认仍需尚未参与研究的新时期或新空间数据，并核实记录规则与变量时间一致性。')
f=sec.footer.paragraphs[0];f.alignment=2;f.add_run('SSCI 575  |  ');field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');f._p.append(field)
D.save(R/'06_reports/RF_Spatial_Extension_v5.docx');print('Wrote current three-direction RF report')
