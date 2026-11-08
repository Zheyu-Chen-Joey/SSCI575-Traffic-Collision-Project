"""Project-style report of training-only cluster diagnosis and targeted RF validation."""
from pathlib import Path
import json,pandas as pd
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parents[1];O=R/'04_outputs/cluster_targeted_optimization';meta=json.loads((O/'cluster_diagnostic_protocol.json').read_text());summary=json.loads((O/'decision_summary.json').read_text());clusters=pd.read_csv(O/'training_cluster_summary.csv').sort_values('n_cells',ascending=False);roads=pd.read_csv(O/'cluster_road_context.csv');D=Document(R/'06_reports/RF_Spatial_Extension_v5.docx')
for element in list(D.element.body):
 if element.tag!=qn('w:sectPr'):D.element.body.remove(element)
def p(text):D.add_paragraph(text)
def page(text):D.add_heading(text,1);D.paragraphs[-1].paragraph_format.page_break_before=True
def table(headers,rows,widths=None,size=10):
 t=D.add_table(rows=1,cols=len(headers));t.autofit=False
 if widths:
  for col,w in zip(t.columns,widths):col.width=Inches(w)
 for cell,text in zip(t.rows[0].cells,headers):cell.text=str(text)
 for row in rows:
  for cell,text in zip(t.add_row().cells,row):cell.text=str(text)
 for i,row in enumerate(t.rows):
  if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for j,cell in enumerate(row.cells):
   if widths:cell.width=Inches(widths[j])
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(4)
    for run in para.runs:run.font.size=Pt(size);run.bold=i==0
   if i==0:
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EEF5');cell._tc.get_or_add_tcPr().append(shade)
D.add_paragraph('大误差与残差聚集区域优化验证','Title');p('SSCI 575  |  2026年11月8日  |  City of Los Angeles  |  固定1km网格')
p('本轮先用训练集折外残差定位大误差和同方向聚集，再测试训练样本加权。部分候选减少了开发区的大误差格及残差聚集，但未通过连续地域稳定性门槛。因此保留现有正式模型，本轮没有再次评估原227格。')
p('720个训练格中，41格绝对误差超过200起。局部Moran的9999次位置标签置换，经720项Benjamini–Hochberg校正后，有21格q≤0.05，其中19格属于高残差及高邻域残差类型。最大两个相连低估片分别为10格、5格。')
D.add_picture(str(O/'training_residual_clusters.png'),width=Inches(6.8))
p('图仅使用训练格的固定五折带1km间隔折外预测，不使用验证格或原评估格的真实事故数。左图是实际减预测；中图标出误差超过200起的格；右图为校正后的局部聚集类型。灰色不代表没有事故或误差为0。')
p('这些是反复使用开发数据后的探索性结果。显著聚集不说明原因已查明，也不保证加权后能推广到新的连续地区。')
page('重点区域与数据特征')
table(['重点低估连通片','格数','平均低估','最大绝对误差'],[['I-110及Harbor Fwy周边','10','344.35','744.96'],['Hollywood Blvd及Franklin Ave周边','5','312.25','509.16']],widths=[3.2,.6,1.4,1.6])
p('第一个连通片包括1000_33_30、1000_34_31、1000_35_32、1000_36_31、1000_36_30等10格，道路参照还包括S Vermont Ave及W Gage Ave。第二个连通片包括1000_30_44、1000_31_44、1000_32_44、1000_32_43、1000_31_43，道路参照还包括Vine St及N Highland Ave。')
p('道路名称由既有TIGER几何裁切得到，只作区域定位，不表示事故发生在该条道路或由道路引起。完整网格清单及参考道路见training_cluster_summary.csv和cluster_road_context.csv。')
table(['区域特征','10格连通片','5格连通片'],[['土地来源平均覆盖率','71.14%','76.32%'],['人口密度中位数 人/平方公里','7832.77','6608.26'],['道路密度中位数 公里/平方公里','17.38','17.33'],['设施点密度中位数 个/平方公里','10.00','17.00']],widths=[3.4,1.7,1.7])
p('两个片区都不是土地利用完全缺测区，先前的缺测问题不足以解释这里的全部误差。较大的事故规模、密集道路及未观测活动差异均可能有关，目前只能作为核验线索，不能判定因果。')
p('按相同1500m邻接计算，原始折外残差Moran I约0.3837；将残差除以预测数平方根后约0.3269，仍呈正相关。该缩放只用于计数尺度敏感性检查，不是已校准的不确定性模型，未用于候选选择。')
p('21个校正后显著格形成7个同类型连通分量；除最大两片外，其余分量为1–2格，不把孤立显著格夸大成大型区域。')
page('只在训练数据内生成权重')
p('不能拿完整720格的折外误差直接给每个外层训练模型加权，因为外层评估格的标签可能间接参与这些误差的计算。本轮在每个外层训练子集内重新做3折分组预测，且再次排除距离评估完整方格不超过1km的训练格。')
table(['设置','固定规则'],[['外层评价','原固定5折 训练720格 每折完整方格间隔大于1km'],['内层权重探测','3折5km分组 同样保持大于1km间隔'],['内层轻量RF','种子42 每方向全局200树 局部100树'],['正式候选RF','3方向权重25% 25% 50% 全局500树 局部200树'],['难例程度','内层绝对残差除以其90分位 截断至0到2'],['同方向程度','1500m内至少2个其他训练邻格的残差同号比例'],['训练权重','基础1 加强度乘难例程度及同方向因子 上限3 后归一化'],['预测输入','仍为18字段 不读取邻格真实事故数']],widths=[1.8,5.0])
p('第一阶段测试强度0.25、0.5、1的聚集加权及强度0.5的纯难例加权，作用于全局和局部RF。第二阶段测试同样三档聚集强度，但只改变局部RF，全局预测与未加权对照经单独实现检查保持一致。共7种新配置。')
p('局部阶段只有在网格ID和顺序与先前训练子集完全一致时，才复用已生成的内层折外残差；否则重新计算。不同外层折间不共享训练模型。输入快照、标签、零事故格、网格和事故总数均不改。')
p('按强度1审计，显著低估格的跨折平均训练权重约1.90，显著高估格约2.09，其他格约0.97；权重确实聚焦于难例。它不是新的预测特征，也不是按原227格真实误差进行人工补偿。')
page('开发验证收益与地域退步')
gc=pd.read_csv(O/'global_and_local/cv_scores.csv').set_index('candidate');lc=pd.read_csv(O/'local_only/cv_scores.csv').set_index('candidate');gv=pd.read_csv(O/'global_and_local/validation_scores.csv').set_index('candidate');lv=pd.read_csv(O/'local_only/validation_scores.csv').set_index('candidate')
def metric_rows(frames):
 return [[name,f'{r["mean_fold_rmse"]if "mean_fold_rmse"in r.index else r.rmse:.2f}',f'{r.mae:.2f}',f'{r.p90_abs_error:.2f}',str(int(r.error_gt200_count)),f'{r.moran_i:.4f}']for name,r in frames]
head=['配置','RMSE','MAE','90分位','超200格','Moran I'];width=[1.6,1.0,1.0,1.1,1.0,1.1]
p('CV表的RMSE是平均折RMSE，其余为汇总折外指标。表中Moran I使用8近邻行标准化，第1页局部聚集使用1500m邻接。')
table(head,metric_rows([('对照',gc.loc[0]),('全局及局部 强1',gc.loc[3]),('仅局部 强1',lc.loc[3]),('仅局部 弱0.25',lc.loc[1])]),widths=width,size=9)
p('166格开发验证')
table(head,metric_rows([('对照',gv.loc[0]),('全局及局部 强1',gv.loc[3]),('仅局部 强1',lv.loc[3]),('仅局部 弱0.25',lv.loc[1])]),widths=width,size=9)
p('连续地域留出 RMSE与MAE')
table(['配置','北侧RMSE','北侧MAE','东侧RMSE','东侧MAE'],[['对照','43.43','33.62','134.74','84.78'],['全局及局部 强1','45.29','35.10','137.41','87.36'],['仅局部 强1','44.82','34.65','136.81','86.61'],['仅局部 弱0.25','44.00','34.08','135.23','85.42']],widths=[2.0,1.2,1.2,1.2,1.2],size=9)
p('CV要求平均RMSE、MAE下降，90分位、超200起误差格数及绝对Moran I不退步。验证区要求RMSE、MAE下降，超200格数及绝对Moran I不增，90分位允许最多2%退步。地域门槛是各地RMSE、MAE比值不超过1.05，两地比值均值不超过1.01。弱局部方案的MAE均值比1.0106，未通过。')
p('强候选冻结后地域检查失败，才提出弱候选的开发区保守复核；所有步骤均发生在本轮原227格比较之前。结果说明当前开发插值收益尚未稳定延伸至连续留出区域，不能仅凭验证区改善就替换。')
page('保留结果与可复核交付')
p('正式模型不变，仍为单一生产文件05_models/rf_spatial_v5/spatial_frozen_rf.joblib。原227格已知探索性指标保持RMSE80.63、MAE53.05、R²0.8184、残差Moran I约0.2808；本轮没有再次计算这227格的候选表现，也未修改主结果图的真实数值或色标。')
D.add_picture(str(O/'validation_targeted_comparison.png'),width=Inches(6.8))
p('本轮交付包括训练折外聚集诊断CSV与GPKG、两个重点连通片清单、嵌套训练权重审计、七配置CV与验证结果、连续地域检查及固定协议。地图与图表中的改善均属于开发证据，不是独立测试结论。')
p('复现诊断使用03_scripts/pretraining/diagnose_development_clusters.py。权重实现见rf_cluster_weighted_model.py，全局及局部试验见study_rf_cluster_weighting.py，仅局部试验见study_rf_local_cluster_weighting.py，保守复核见check_conservative_cluster_candidate.py。重跑应指定新的运行目录，避免覆盖已冻结证据。')
p('后续优先核查重点片区在研究年份的道路功能、设施时间、事故定位和活动差异；补充数据须先验证来源、年份与覆盖。不能使用原评估格的已知事故数生成权重或修正预测后宣称测试改善，也不能填造交通量。')
p('局部置换检验采用可交换的随机位置标签假设；开发地区及基础模型已经多轮复用，选模不确定性未纳入显著性。权重法未通过本轮地域门槛不等于所有区域都一定退步，仍需新数据独立确认。')
D.save(R/'06_reports/RF_Cluster_Targeted_Optimization.docx');print('Wrote cluster-targeted optimization report')
