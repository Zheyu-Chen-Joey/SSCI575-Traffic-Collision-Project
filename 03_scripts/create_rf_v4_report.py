from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path.cwd();O=R/'04_outputs/rf_stability_blend_v4b';V=R/'04_outputs/rf_coverage_v4';ev=json.loads((O/'evaluation.json').read_text());v4=json.loads((V/'evaluation.json').read_text());ci=json.loads((O/'bootstrap_intervals.json').read_text());D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
for n in ['Normal','Title','Heading 1','Heading 2']:
 s=D.styles[n];s.font.name='Arial';s.font.color.rgb=RGBColor(0,0,0);s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
D.styles['Normal'].font.size=Pt(10.5);D.styles['Normal'].paragraph_format.line_spacing=1.1;D.styles['Normal'].paragraph_format.space_after=Pt(7)
for n,z in [('Title',21),('Heading 1',16),('Heading 2',12)]:D.styles[n].font.size=Pt(z)
for el in list(D.styles.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
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
D.add_paragraph('随机森林持续优化阶段报告','Title');p('SSCI 575  |  1 km工作网格  |  覆盖率感知建模与保守RF组合')
p('本轮在不增加位置或邻格事故特征的条件下，评估84种覆盖率处理与目标缩放配置，并比较固定随机种子平均和保守RF组合。原模型与目标缩放RF各占一半的组合，使旧测试区RMSE由97.98降至97.53，MAE由64.96降至63.84；但残差空间聚集没有改善，空间块重采样的差异区间跨0。结果属于小幅、尚不稳健的探索性收益。')
rows=[]
for n,d,i in [('原RF',ev['v1']['legacy_evaluation'],ev['v1']['moran_i']),('覆盖率与缩放RF',v4['v4']['legacy_evaluation'],v4['v4']['moran']['I']),('保守RF组合',ev['blend']['legacy_evaluation'],ev['blend']['moran_i'])]:rows.append([n,f"{d['rmse']:.2f}",f"{d['mae']:.2f}",f"{d['r2']:.3f}",f'{i:.4f}'])
table(['旧测试区对照','RMSE','MAE','R²','残差Moran I'],rows);D.add_picture(str(O/'figures/metric_comparison.png'),width=Inches(6.8))
p('这些227个网格自第一轮起已经被查看；本轮没有用其目标拟合组合权重，但研究方向已经受到早期结果启发，因此不再是全新独立验证。正式项目v1模型与报告不覆盖；新组合保留为候选模型，不宣称已普遍优于原模型。')
p(f"成对5km空间块bootstrap共2000次，组合减原模型RMSE差异95%分位区间为[{ci['delta_rmse']['lower']:.2f}, {ci['delta_rmse']['upper']:.2f}]，MAE差异为[{ci['delta_mae']['lower']:.2f}, {ci['delta_mae']['upper']:.2f}]。均跨0，仅表示固定划分与固定模型下的不确定性，不包含重新训练变异。组合残差Moran置换p=0.0001，聚集仍明显。")
page('输入核查与优化方法')
p('土地利用完全缺失的合格格：训练0个、验证2个、旧测试14个；覆盖率不足50%的格分别为11、8、22个。这是输入分布差异，不直接证明原始记录错误。所有事故和网格均保留，没有依据残差删除困难样本。')
p('比较四种土地利用处理：原始占市界裁切格面积的比例；按已映射面积计算条件组成；对覆盖不足50%或80%的格将条件组成置为缺失。未覆盖比例始终保留，缺失插补只在相应训练折学习，不填成无依据的0。最终缩放模型选中条件组成，未选中两个覆盖阈值屏蔽方案。')
p('目标缩放比较原始事故数量、按道路密度、设施点密度或人口密度构建的已知正因子。RF拟合缩放后的目标，预测时乘回因子，所有选模与评估均使用原始事故数量。选中方案使用“设施点密度加1”的平方根作因子；这是统计尺度处理，不是实际车辆暴露、事故率或风险。')
p('每种配置在训练720格上做按固定5km块分组的5折CV，共84配置。开发验证166格评估入围方案及种子7/42/99的等权平均。先冻结覆盖率/缩放候选，再做保守组合：至少一半权重保留原RF，权重只按训练折外分数和验证结果选取。最终选中原RF50%与缩放RF50%，无额外算法。所有最终成员均只拟合886个开发格。')
p('缩放RF沿用500树、深度8、叶最少5、分裂最少10、max_features0.7、平方误差和种子42。原模型结构不变；改进来自输入组成的定义与目标尺度，而非单纯增加树深。开发CV与验证已多轮复用，只能作为后续开发诊断。')
D.add_heading('设施变量语义更正',2)
p('官方LADOT MapServer30名为Signal Locations，但说明包含Signals and Speed Feedback Sign locations，字段没有明确设施类型分类。因此原signal_density_snapshot_km2应解释为该混合设施点快照的密度代理，不能称为已核验的纯信号交叉口密度。此次没有根据名称猜测类型或删除点，旧数值仍可复现；旧报告需连同本更正阅读。')
p('官方来源 https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/30?f=pjson 。此前“0.1m坐标去重”和“距拓扑节点30m的匹配”均不能证明设施类型或2017–2021历史存在。')
page('全市残差与后续验证')
D.add_picture(str(O/'figures/full_city_residual_comparison.png'),width=Inches(6.8))
p('全图显示1113个合格格；黑框标记原测试区，其余颜色为开发区拟合残差，不能把全图颜色变浅当作独立精度。残差为实际减预测，红色表示低估、蓝色表示高估；前后使用同一色标。')
p('当前剩余问题是空间误差规律没有稳定迁移，而不是尚未把树数调得足够大。下一步若加入网格位置，需要明确记录为原计划的空间趋势扩展，并在更严格空间隔离及新的时空外部数据上验证；在用户明确选择前不运行该扩展。位置不等于因果解释，邻格真实事故数仍不能作为部署时不可获得的输入。')
p('模型：05_models/rf_stability_blend_v4b/blend_frozen.joblib。协议、预测、CV与验证得分、空间块区间和GIS：04_outputs/rf_stability_blend_v4b与04_outputs/rf_coverage_v4。独立验证入口：03_scripts/pretraining/export_rf_coverage_v4.py。加载组合需将03_scripts/pretraining加入模块路径，使用rf_fixed_blend.py和rf_coverage_scaled_model.py。原数据快照及v1模型均保留。')
f=sec.footer.paragraphs[0];f.alignment=2;f.add_run('SSCI 575  |  ');e=OxmlElement('w:fldSimple');e.set(qn('w:instr'),'PAGE');f._p.append(e)
out=R/'06_reports/RF_Continuous_Optimization_v4.docx';D.save(out);(R/'06_reports/RF_Continuous_Optimization_v4.txt').write_text('\n'.join(x.text for x in D.paragraphs),encoding='utf-8');print(out)
