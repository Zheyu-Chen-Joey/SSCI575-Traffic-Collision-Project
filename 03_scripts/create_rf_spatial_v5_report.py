"""Current best-model report, generated from frozen comparisons and buffered diagnostics."""
from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path.cwd();P=R/'04_outputs/rf_spatial_v5';M=R/'05_models/rf_spatial_v5';ev=json.loads((P/'evaluation.json').read_text());study=json.loads((P/'local_rf_evaluation.json').read_text());change=json.loads((P/'local_rf_improvement_summary.json').read_text());contract=json.loads((M/'input_contract.json').read_text());ci=json.loads((P/'bootstrap_intervals.json').read_text());D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
for n in ['Normal','Title','Heading 1','Heading 2']:
 s=D.styles[n];s.font.name='Arial';s.font.color.rgb=RGBColor(0,0,0);s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
D.styles['Normal'].font.size=Pt(10.5);D.styles['Normal'].paragraph_format.line_spacing=1.1;D.styles['Normal'].paragraph_format.space_after=Pt(7)
for n,z in [('Title',21),('Heading 1',16),('Heading 2',12)]:D.styles[n].font.size=Pt(z)
for x in list(D.styles.element.iter(qn('w:pBdr'))):x.getparent().remove(x)
def p(t):D.add_paragraph(t)
def h(t):D.add_heading(t,1)
def page(t):h(t);D.paragraphs[-1].paragraph_format.page_break_before=True
def table(head,rows):
 t=D.add_table(rows=1,cols=len(head))
 for j,x in enumerate(head):t.rows[0].cells[j].text=str(x)
 for row in rows:
  cells=t.add_row().cells
  for j,x in enumerate(row):cells[j].text=str(x)
 for i,row in enumerate(t.rows):
  for cell in row.cells:
   pr=cell._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b)
   if i==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF5');pr.append(sh)
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(4)
    for run in para.runs:run.font.size=Pt(10);run.bold=i==0
D.add_paragraph('随机森林局部加权优化结果报告','Title');p('SSCI 575  |  City of Los Angeles  |  2017–2021记录事故  |  固定1km网格')
p('本轮使用局部加权随机森林降低真实残差，而不是调整色标或平滑误差图。经过开发区筛选的固定方案，在已多次查看的原227格评估区域上，将RMSE由92.89降至83.51、MAE由59.86降至54.57，分别下降10.10%和8.83%，R²由0.759升至0.805。残差Moran’s I由0.3317降至0.3134，仍显著聚集。新方案已通过重载复算并替换唯一保留的模型文件。')
table(['原区域探索性比较','RMSE','MAE','R²','残差Moran I'],[['前空间RF','92.89','59.86','0.759','0.3317'],['当前局部加权RF','83.51','54.57','0.805','0.3134']]);D.add_picture(str(P/'figures/01_metric_comparison.png'),width=Inches(6.8))
p(f"在227格中，{change['improved_cells']}格的绝对误差减小，{change['worsened_cells']}格增大，改善比例为{change['improved_fraction']:.1%}。因此不能要求每个格都变白，也不能把全图颜色变浅当作独立泛化证据。当前Moran置换p=0.0001，剩余空间误差仍需解释。")
p(f"2000次成对5km空间块重采样中，新减前空间RF的RMSE差异95%分位区间为[{ci['Previous Spatial V5_delta_rmse']['lower']:.2f}, {ci['Previous Spatial V5_delta_rmse']['upper']:.2f}]起/格，MAE差异为[{ci['Previous Spatial V5_delta_mae']['lower']:.2f}, {ci['Previous Spatial V5_delta_mae']['upper']:.2f}]。区间条件于当前固定模型与已查看区域，不包含选模或重新训练的不确定性，不能替代新的独立验证。")
page('当前模型如何计算')
p('模型保持用户已授权的18个输入：原道路、人口、土地利用、道路设计与设施代理16字段，加EPSG:26911网格中心cx/cy。不使用邻格真实事故数、HIN、交通流量、限速或视距作为输入。原始事故、固定1km格、230536总记录和零事故格均不变。')
p('在全局空间RF之外，按固定20km位置布局建立局部RF。训练样本的权重随其到局部模型中心的距离按高斯核衰减；只有有效样本数至少40的中心才保留。预测时由最近3个局部模型按位置计算加权结果，再与全局预测组合。所有RF仅拟合开发格的事故标签，预测阶段不读取任何邻格的实测事故数。')
table(['参数','当前固定设置'],[['全局部分','3个种子7 42 99 每个RF500树'],['局部部分',f"{contract['local_anchor_count']}个局部RF 每个200树 种子575"],['共享树限制','最大深度16 叶最少5 分裂最少10 max_features0.5'],['空间加权','高斯带宽10km 锚点布局20km 最近3中心'],['预测组合','25%全局RF 加75%局部加权预测'],['目标处理','设施点密度加1的平方根缩放 拟合后乘回原计数'],['最终拟合','仅886个开发格 原评估227格不参与拟合']])
p('分析网格始终为1km。10km是训练权重衰减带宽，20km是局部模型中心的布局间距，二者都不是新的事故统计网格，也不是半变异模型的range。全局与局部部分均为随机森林，没有增加其他机器学习算法。')
p('设施点字段来自混合信号及速度反馈标志快照，应解释为设施密度代理，不能称为经过历史核验的纯信号交叉口密度。目标缩放只是统计处理，不是车辆暴露调整事故率。人口、土地利用、设施快照和2021报告覆盖等数据限制继续保留。')
page('筛选过程与严格空间检查')
p('本轮预先记录3个带宽10/20/35km、5个局部权重0.1/0.25/0.5/0.75/1，共15种组合，保留前空间RF作对照。训练720格采用原固定5km分组5折，并剔除与评估完整方格距离不超过1km的训练格。每折保留452–481个训练格，候选中心与权重只由该折训练位置决定。')
p('以缓冲CV平均RMSE和MAE筛选，最多4项进入166格开发验证；验证RMSE与MAE必须同时改善。候选带宽10km、局部权重0.75在原区域比较前冻结。最终替换还要求该固定候选在已复用区域的RMSE和MAE同时低于前模型，因此当前优选包含自适应选择影响，不能称为一次全新的独立测试。')
table(['开发指标','前空间RF','当前局部方案'],[['缓冲CV平均折RMSE','95.76','95.59'],['缓冲CV汇总MAE','59.71','59.93'],['验证RMSE','91.38','82.70'],['验证MAE','56.86','52.82'],['验证残差Moran I','0.1247','0.0595']])
p('缓冲CV的RMSE仅小幅改善，MAE略有退步，不能把验证区和旧区域的较大收益推广到所有空间设置。整体平均偏差也未改善：原区域预测减实际的均值从9.47变为10.40起/格。')
geo=list(csv.DictReader((P/'local_rf_geographic_transfer.csv').open()))
table(['连续地域留出','模型','RMSE','MAE'],[[{'north20pct':'北侧20%','east20pct':'东侧20%'}[r['region']],{'previous_spatial':'前空间RF','local_weighted':'局部方案'}[r['model']],f"{float(r['rmse']):.2f}",f"{float(r['mae']):.2f}"]for r in geo])
p('连续地域检查只使用开发区，排除原评估区并保持1km间隔。新方案在北侧和东侧均退步，说明它更适合当前城市覆盖内的插值，尚不能支持更稳健的区域外推。该检查未用于进一步修改已冻结参数。')
page('固定色标的实际预测与残差')
D.add_picture(str(P/'figures/03_full_city_comparison.png'),width=Inches(6.8));p('全图显示1113个合格格。黑框为原评估格，其余有色格为开发区拟合预测；灰色边界格不计入指标。残差为实际减预测，红为低估，蓝为高估，接近白色表示接近0。全图不能当作全部独立测试。')
D.add_picture(str(P/'figures/02_legacy_residual_comparison.png'),width=Inches(5.0));p('前后采用相同格与相同残差色标。部分格的误差仍大，局部区域仍有同方向误差；没有修改真实事故数、删除困难格或平滑残差。')
page('使用与复现')
p('当前仅保留05_models/rf_spatial_v5/spatial_frozen_rf.joblib一个模型文件。文件夹名称用于兼容已有入口，当前模型类型为LocalWeightedSpatialForest；参数与依赖见同目录input_contract.json和environment.json。旧冠军只保存冻结参考预测，实体不再重复保留，历史版本可通过Git追溯。')
p('离线预测入口：python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 已聚合特征.csv --output 新预测.csv。坐标必须是EPSG:26911固定1km网格中心，不能用经纬度。输入仍是18字段，局部权重和目标还原由模型内部处理。')
p('只复现固定最优设置：python 03_scripts/pretraining/train_best_spatial_rf.py --execute-training --output 新模型.joblib。该入口只拟合886个开发格，不搜索候选或覆盖现有模型。导出与验证：python 03_scripts/pretraining/export_rf_spatial_v5.py。')
p('rf_spatial_v5输出目录保留候选CV/验证摘要、冻结决定、原区域比较、逐格误差改善、地域留出、空间块区间和GIS结果。局部森林样本权重已按开发位置独立重建，重拟合其中一棵完整局部森林并复现预测，证明没有用原评估标签拟合。')
p('这些结果是对当前2017–2021公开记录负担的回溯建模，不是未来事故预测、车辆暴露风险或因果效应。多轮复用原区域已影响研究方向和优选，后续可信确认需要新时段或尚未参与研究的新空间区域，并核实报告规则及协变量时间一致性。')
p('原始快照不覆盖，不缺失填0，位置特征的使用已经用户明确授权。原计划的尺度诊断和数据来源说明保留；模型的新增局部空间加权方法在本报告中明确记录，不把残差降低等同于空间问题已解决。')
f=sec.footer.paragraphs[0];f.alignment=2;f.add_run('SSCI 575  |  ');e=OxmlElement('w:fldSimple');e.set(qn('w:instr'),'PAGE');f._p.append(e);D.save(R/'06_reports/RF_Spatial_Extension_v5.docx');print('Updated current-model report')
