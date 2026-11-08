"""Project-style report for geometry-protected RF correction and internal holdout checks."""
from pathlib import Path
import json,pandas as pd
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parents[1];O=R/'04_outputs/support_protection_optimization';summary=json.loads((O/'decision_summary.json').read_text());regions=pd.read_csv(O/'regional_comparison.csv');D=Document(R/'06_reports/RF_Spatial_Extension_v5.docx')
for element in list(D.element.body):
 if element.tag!=qn('w:sectPr'):D.element.body.remove(element)
def p(text):D.add_paragraph(text)
def page(title):D.add_heading(title,1);D.paragraphs[-1].paragraph_format.page_break_before=True
def table(headers,rows,widths,size=10):
 t=D.add_table(rows=1,cols=len(headers));t.autofit=False
 for col,w in zip(t.columns,widths):col.width=Inches(w)
 for cell,value in zip(t.rows[0].cells,headers):cell.text=str(value)
 for row in rows:
  for cell,value in zip(t.add_row().cells,row):cell.text=str(value)
 for i,row in enumerate(t.rows):
  if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for j,cell in enumerate(row.cells):
   cell.width=Inches(widths[j])
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(4)
    for run in para.runs:run.font.size=Pt(size);run.bold=i==0
   if i==0:
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EEF5');cell._tc.get_or_add_tcPr().append(shade)
D.add_paragraph('连续地域留出保护与残差优化试验','Title');p('SSCI 575  |  2026年11月8日  |  City of Los Angeles  |  固定1km网格')
p('本轮用训练位置支持范围控制加权RF修正，测试12种几何保护配置。候选在北侧、东侧连续留出中回退至原RF，避免此前加权带来的退步；但新增内部连续留出仍未通过联合门槛。因此正式模型保持不变，本轮没有评估原227格候选表现。')
D.add_picture(str(O/'development_support_gate_map.png'),width=Inches(5.3))
p('颜色是修正权重，不是事故数或误差。紫色0表示沿用原RF；黄色1表示完全采用加权RF。黑框是本轮开发留出区域，不是原227格。边界不退步来自回退保护，不说明外推预测变得更准确。')
page('训练覆盖保护如何计算')
p('保持原18个输入和三方向RF。第一条分支为现有RF配方，第二条为上一轮的强度1局部加权RF；其训练权重仅由对应训练子集内部带间隔折外残差生成。预测阶段不读取邻格真实事故数。')
p('只用该次训练格的EPSG:26911中心坐标建立凸包。包外修正为0；包内按到边界的距离逐步增加修正。随后加入最近训练中心距离限制：2km以内保留支持，超过2km逐步衰减，达到指定上限后修正为0。')
table(['项目','预设设置'],[['第一阶段 凸包保护','包内边缘衰减宽度0 2 5km 修正强度0.5或1 共6项'],['第二阶段 邻近距离保护','凸包边缘宽度固定2km 邻近距离上限3 4 5km 强度0.5或1 共6项'],['预测公式','原RF预测 加几何权重乘两分支预测差'],['分支训练','原RF不变 加权只作用于第二分支局部RF'],['统计网格','始终1km 原点E345000/N3730000'],['几何限制含义','修正保护参数 不是新的网格尺度或半变异range']],widths=[2.0,4.8])
p('凸包可能覆盖内部空洞，不能仅凭位于包内就认定有充分训练支持。为此增加两个内部5km留出块，并测试最近训练距离衰减。几何权重仍不是经过校准的置信度，也不保证土地利用等变量完整。')
p('第二阶段复用第一阶段已保存的原RF与凸包内完整修正预测。新权重不超过完整凸包权重，所以可精确重构候选预测，无需重复训练。独立重训一个外层折后，重构与真实模型预测最大差约1.14×10⁻¹³，核验一致。')
p('第二阶段根据第一阶段内部留出失败提出，属于适应性开发。所有模型、参数选择和四类地域检查均发生在本轮原227格比较之前。')
page('空间交叉验证与验证区表现')
hc=pd.read_csv(O/'hull_only/cv_scores.csv').set_index('candidate');dc=pd.read_csv(O/'distance_guard/cv_scores.csv').set_index('candidate');hv=pd.read_csv(O/'hull_only/validation_scores.csv').set_index('candidate');dv=pd.read_csv(O/'distance_guard/validation_scores.csv').set_index('candidate')
def metric_rows(items,cv=False):return [[name,f'{r.mean_fold_rmse if cv else r.rmse:.2f}',f'{r.mae:.2f}',f'{r.p90_abs_error:.2f}',str(int(r.error_gt200_count)),f'{r.moran_i:.4f}']for name,r in items]
headers=['配置','RMSE','MAE','90分位','超200格','Moran I'];widths=[1.6,1.0,1.0,1.1,1.0,1.1]
p('训练720格五折空间CV 每折完整方格间隔大于1km')
table(headers,metric_rows([('原RF',hc.loc[0]),('凸包2km 强1',hc.loc[4]),('距离5km 强1',dc.loc[6])],True),widths,9)
p('166格开发验证 使用原固定训练及验证分组')
table(headers,metric_rows([('原RF',hv.loc[0]),('凸包2km 强1',hv.loc[4]),('距离5km 强1',dv.loc[6])]),widths,9)
D.add_picture(str(O/'validation_support_comparison.png'),width=Inches(6.8))
p('表中CV的RMSE为平均折RMSE，其他指标为汇总折外指标；Moran I沿用8近邻行标准化。验证区没有新增距离缓冲，带大于1km间隔的检查来自CV及四个地域留出。')
p('距离5km候选在验证区约86.1%的格接受非零修正，RMSE、MAE、90分位、大误差格数及残差Moran I均改善。其平均预测偏差10.25→11.87起/格有所退步，不能称为所有指标都改善。')
p('距离上限3km与4km的候选未通过CV双指标要求。全部通过CV的距离候选均继续接受验证及四个地域检查，不根据原评估区结果挑选配置。')
page('边界与内部连续地域检验')
p('北侧和东侧各留出20%开发格，另设内部5km块6_6和6_8，覆盖I-110及Hollywood周边。四类检查均保持完整方格距离大于1km。内部块按既有训练诊断选择，属于困难开发检查集。')
names={'north20pct':'北侧','east20pct':'东侧','interior_6_6':'I-110内部块','interior_6_8':'Hollywood内部块'}
rows=[]
for r in regions.itertuples():rows.append([names[r.region],str(r.n_eval),f'{r.reference_rmse:.2f}',f'{r.candidate_rmse:.2f}',f'{r.reference_mae:.2f}',f'{r.candidate_mae:.2f}'])
table(['留出区域','格数','原RMSE','候选RMSE','原MAE','候选MAE'],rows,[1.6,.6,1.15,1.15,1.15,1.15],9)
p('北侧192格、东侧180格修正权重均为0，候选预测与原RF逐格相同，避免了加权退步。I-110内部块略有改善，Hollywood内部块仍有小幅退步。')
before=summary['reference_interior'];after=summary['candidate_interior'];table(['内部42格合并指标','原RF','距离保护候选'],[[label,f'{before[key]:.{digits}f}',f'{after[key]:.{digits}f}']for label,key,digits in [('RMSE','rmse',2),('MAE','mae',2),('绝对误差90分位','p90_abs_error',2),('超200起误差格数','error_gt200_count',0),('残差Moran I','moran_i',4)]],[3.4,1.7,1.7])
p('内部联合门槛要求各块RMSE及MAE至多退步2%，且合并RMSE、MAE、90分位、大误差格数和绝对Moran I均不退步。候选的合并平均误差及聚集指标未满足要求，因此不采用。90分位虽下降，不能替代其余目标。')
p('这42格来自特意选择的困难区域，数据构成与原227格不同，不能把187.28与原区域80.63直接比较。这里的指标仅用于同一内部留出样本的前后对照。')
p('第一阶段只有凸包保护时，内部合并RMSE187.28→190.34、Moran I0.1746→0.1852；新增邻近距离限制后退步幅度缩小，但仍未实现联合改善。')
page('保留决定与复现证据')
p('正式模型文件仍为05_models/rf_spatial_v5/spatial_frozen_rf.joblib。其哈希与1473格正式预测均未变化。原227格已知探索性指标保持RMSE80.63、MAE53.05、R²0.8184。本轮未再次评估该区域，也未保存失败候选模型实体。')
table(['核查','结果'],[['边界回退','所有北侧 东侧留出点权重为0 原RF与候选预测完全相同'],['预测复用','独立重训外层折与离线重构差约1.14×10⁻¹³'],['原模型及数据','模型和输入表SHA256保持不变 230536条事故守恒'],['模型保留','只保留1个生产模型'],['未完成目标','内部连续区域平均误差与聚集尚未同时下降']],widths=[1.7,5.1])
p('完整协议、候选逐折预测、验证预测、四地域逐格预测、保护权重及失败门槛，保存在04_outputs/support_protection_optimization。模型实现见rf_supported_cluster_model.py；两阶段试验分别见study_supported_cluster_rf.py及study_distance_supported_rf.py。')
p('第一阶段支持从已完成的预测检查点使用--resume恢复指标计算。复现时需保留固定输入和分区，并指定新的运行目录，避免覆盖冻结证据。内层权重仅在训练子集内部生成；离线复用仅在原RF分支和训练集合一致时成立。')
p('本轮推进了边界退步保护，但尚未证明内部未见区域更准确。后续应重点核查Hollywood块的活动、道路功能和研究年份差异；新增数据须验证来源、时间和覆盖。不能直接使用该块已知事故数修正预测，也不把回退当作外推准确度提升。')
p('这些地区及基础模型已经反复参与开发，内部块又按既有训练误差选定，结果不属于新的独立测试。小样本地域指标存在不确定性；门槛失败是当前保留决策，不等同于因果或显著性结论。')
D.save(R/'06_reports/RF_Support_Protection_Optimization.docx');print('Wrote support-protection optimization report')
