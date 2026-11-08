"""Create a hotspot investigation using the current project report as style template."""
from pathlib import Path
import json,pandas as pd
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parents[1];P=R/'04_outputs/residual_investigation';S=P/'correction_study';audit=json.loads((P/'source_audit.json').read_text());source=json.loads((P/'landuse_download_audit.json').read_text());trial=json.loads((S/'evaluation.json').read_text());top=pd.read_csv(P/'top20_legacy_cells.csv').merge(pd.read_csv(P/'case_road_context.csv'),on='grid_id',how='left');D=Document(R/'06_reports/RF_Spatial_Extension_v5.docx')
for element in list(D.element.body):
 if element.tag!=qn('w:sectPr'):D.element.body.remove(element)
def p(text):D.add_paragraph(text)
def page(title):D.add_heading(title,1);D.paragraphs[-1].paragraph_format.page_break_before=True
def table(headers,rows,widths=None):
 t=D.add_table(rows=1,cols=len(headers));t.autofit=False
 if widths:
  for c,w in zip(t.columns,widths):c.width=Inches(w)
 for c,value in zip(t.rows[0].cells,headers):c.text=str(value)
 for row in rows:
  for c,value in zip(t.add_row().cells,row):c.text=str(value)
 for i,row in enumerate(t.rows):
  if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for column,cell in enumerate(row.cells):
   if widths:cell.width=Inches(widths[column])
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(5)
    for run in para.runs:run.font.size=Pt(10);run.bold=i==0
   if i==0:
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EEF5');cell._tc.get_or_add_tcPr().append(shade)
D.add_paragraph('高残差区域原因排查与纠错记录','Title');p('SSCI 575  |  2026年11月8日  |  City of Los Angeles  |  2017–2021事故记录')
p('本次逐格核查了事故、道路、人口、设施点和土地利用来源，未发现已核查聚合链的计数或拼接差异。主要线索是土地利用缺测分布差异、机场用地样本少以及部分密集城区的共同模型偏差；这些是描述性证据，不能直接认定为因果。')
p(f"在原227格中，绝对误差最大的23格贡献{audit['legacy_top23_share_squared_error']:.1%}的平方误差和{audit['legacy_top23_share_abs_error']:.1%}的绝对误差。以下均是已多次查看区域的探索性诊断，不能作为新的独立验证。")
D.add_picture(str(P/'error_hotspots_and_coverage.png'),width=Inches(6.8))
p('左图为实际减预测：红为低估、蓝为高估。中图为绝对误差，数字1–8对应第3页案例。右图为土地利用来源多边形覆盖率，黑框是原评估格。色彩表示不同量，不能跨图直接比较深浅。')
p('事故数属于回归目标，主要误差单位是起/格，不把R²当作准确率。诊断CSV另列对称相对误差sMAPE，仅作辅助；低事故格的相对误差容易放大，零事故格仍保留。')
page('独立重算与来源完整性核查')
table(['核查项','结果'],[['有效事故及唯一编号','230536条 唯一编号230536个'],['固定1km总量及2017至2021逐年重算','所有格计数差异均为0'],['设施点0.1m去重后归格','与既有计数差异为0'],['TIGER交叉口节点归格','与既有计数差异为0'],['道路长度及人口交叉表重新汇总','逐格差异为0 数值容差内一致'],['人口 道路 设施点 交叉口密度单位','均与数量除以实际市内面积一致'],['土地利用原始对象ID快照','50644个全部取得 无漏页 重复或额外ID']],widths=[2.8,4.0])
p('土地利用市内保留50643个要素；完全缺测的16个合格格与处理后图层均无多边形相交。其中训练集0格、验证集2格、原评估区14格。缺口已存在于该下载快照，不能据此填入住宅、工业等猜测类别。对象ID核对只证明快照下载完整，不证明源数据完整或符合2017–2021状况。')
table(['原227格土地覆盖情况','格数','MAE 起/格'],[['覆盖低于50%','22','119.32'],['覆盖至少50%','205','45.94'],['完全缺测 子集','14','111.23']],widths=[3.5,1.1,2.2])
p('开发区折外及验证预测也呈相同方向：覆盖低于50%的19格MAE86.88，其余867格为56.27。但土地覆盖、城市密度与事故规模有关，分组差异不等于土地缺测造成了全部误差；完全缺测的开发样本只有2格，证据尤其有限。')
p('每个事故编号唯一；许多事故使用相同地理坐标，可能是路口定位或位置精度所致，不能把同坐标记录直接当成重复并删除。2021记录减少仍是来源解释限制，本次未确认其为某个大残差格的具体原因。')
page('具体位置与可能机制')
rows=[]
for _,r in top.head(8).iterrows():rows.append([str(int(r.diagnostic_rank))+' '+r.grid_id,str(r.reference_road_names).split(';')[0],str(int(r.count_2017_2021)),f'{r.spatial_pred:.1f}',f'{r.residual:+.1f}'])
table(['图号及网格','位置参照道路','实际','预测','残差'],rows,widths=[1.65,2.1,.8,1.1,1.15])
p('道路名称来自既有TIGER道路裁切，只用于定位，不表示事故发生在该条道路或由其引起。原点评估格坐标及完整道路参照见top20_legacy_cells.csv与case_road_context.csv。')
p('机场特殊用地：1000_25_26的土地利用机场占比96.75%，人口估计为0，实际475起，预测234.6起。训练中机场占比超过50%的合格格只有6个，事故数范围0–260。居住人口不能代表机场的全部出行活动；该例支持样本稀少和解释变量不足的可能性，不支持把人口0改成任意正数。')
p('土地缺测与道路复杂区：1000_40_38土地利用全缺测，实际1042起，预测838.4起；1000_40_35覆盖率20.81%，实际553起，预测339.4起。缺测及道路活动可能相关，两例不足以区分各因素的作用。')
p('共同偏差：1000_38_41附近参照W Sunset Blvd及N Alvarado St，实际547起，三方向RF分别预测872.7、877.1、840.1起，均明显高估。机场格三个方向也都偏低。继续改旋转权重难以消除这些共同偏差，不能仅凭方向模型彼此接近就宣称预测可靠。')
p('开发折外及验证数据中，事故数至少500的格平均低估135.52起；事故数低于50的格平均高估15.55起，呈向中间水平收缩的模式。该分组使用了实际事故数，只能用于解释，不能在实际预测时用真实事故数选择纠偏规则。')
page('纠偏试验与未替换原因')
p('针对训练中没有土地利用全缺测格的问题，预设5%、10%、20%三种缺测比例。在训练副本中随机把七项土地利用比例置为缺失，同时将未覆盖比例设为1；事故标签、位置和其他变量不变，原始及处理后数据文件不改。固定随机种子575，仍为三方向RF。')
p('采用五折1km间隔空间CV、166格验证及开发区北侧、东侧留出。候选在比较原227格前冻结。另在开发数据中构造所有土地利用不可用的压力情景，它不是实际观测效果。最终10%方案进入原区域探索性比较。')
table(['检查','现有模型','10%训练缺测模拟'],[['五折平均RMSE','92.2924','92.2816'],['五折平均MAE','58.0446','57.5968'],['验证RMSE','82.4728','82.3196'],['验证MAE','52.0701','51.8426'],['缺测压力情景汇总RMSE','125.3923','102.7206'],['北侧连续留出RMSE','43.4298','42.6243'],['东侧连续留出RMSE','134.7356','138.1905'],['原227格RMSE','80.6253','81.8398'],['原227格MAE','53.0539','53.7067'],['真实全缺测14格RMSE','126.6136','126.7531']],widths=[3.2,1.5,2.1])
p('北侧改善、东侧退步，仍通过预设的两地域平均门槛，但原区域整体变差，真实缺测格的RMSE也未下降。因此候选不替换现有模型，不保存其模型实体。压力情景改善不能代替真实地区效果，土地缺测并不是这些误差的充分解释。')
p('当前唯一生产模型保持不变：原区域RMSE80.63、MAE53.05、R²0.8184、残差Moran I0.2808。没有把高误差格的实测值用于手工修改预测，也未平滑残差或剔除困难格。')
page('已完成纠错与后续核验')
p('已修正预测结果的呈现方式：预测CSV及GIS新增landuse_polygon_coverage、input_quality_flags和input_review_recommended。数值预测不变，输入仍为18字段。质量提示仅依据可观察输入，不读取事故标签。')
table(['需复核的输入类型','合格格数','提示用途'],[['土地利用全缺测','16','核查来源 不当作真实0'],['其他土地覆盖低于50%','25','提示来源信息不足'],['机场用地主导且人口为0','4','提醒居住人口代理有限'],['合计 互不重复','45','逐格复核 不是置信区间']],widths=[2.9,1.0,2.9])
p('其余1068个合格格没有选定的质量提示，不代表误差一定小。三个方向RF的预测差异也仅是模型敏感性，未经校准，不能当作95%区间。')
p('形成残差诊断GPKG、逐格绝对及相对误差、开发折外和原区域分组表、前20个案例、来源对象ID核对、坐标方向差异及纠偏验证记录。诊断残差图使用原区域固定±341.46色标；主模型全市图仍采用原固定色标。')
p('下一步应针对机场和大误差路口核查研究年份的道路功能、设施时间及事故定位精度；若未来获得可用活动或出行暴露资料，应先审核年份与覆盖，再明确修改变量设计并空间验证。当前不补造交通量、限速或土地类别，不增加未经验证的变量。')
p('复现排查：python 03_scripts/pretraining/investigate_residual_hotspots.py；归档和案例：python 03_scripts/pretraining/complete_residual_audit.py。后者需要本地保留的试验目录；冻结的最终证据已保存在04_outputs/residual_investigation/correction_study。')
p('预测接口：python 03_scripts/pretraining/predict_spatial_rf_v5.py --input 聚合特征.csv --output 新预测.csv。质量提示由rf_input_quality.py生成。地图、逐格表与本报告供人工核验，原因推断仍属探索性，所有原区域结果均非新的独立验证。')
D.save(R/'06_reports/RF_Residual_Hotspots_Investigation.docx');print('Wrote residual investigation report')
