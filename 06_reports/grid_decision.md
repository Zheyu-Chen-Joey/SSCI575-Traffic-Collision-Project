# 2026年11月7日工作尺度更新

用户选定1000米作为实践工作尺度。新网格及独立诊断见04_outputs/pretraining/feature_build_qa.json。NSR约0.25868，Range约37.13km（仍为外推）；未宣称NSR唯一最优。以下保留此前1100米候选分析的历史记录。

# 2026年11月7日工作尺度更新

用户选定1000米作为实践工作尺度。新网格及独立诊断见04_outputs/pretraining/feature_build_qa.json。NSR约0.25868，Range约37.13km（仍为外推）；未宣称NSR唯一最优。以下保留此前1100米候选分析的历史记录。

# 网格尺度判定报告

## 当前结论

主参数下的首个候选为 **1,100 × 1,100 米**。目前不能确认唯一稳定的最佳尺度，最终尺度字段保持 null。候选网格已实际生成，可在GIS打开；不能把候选当作通过完整审计的最终建模尺度。

## 已完成的分析

按计划书生成 500–5000 米、步长150米的全部31种网格。坐标为NAD83 / UTM zone 11N（EPSG:26911），单位米；原点统一对齐5km。保留市界相交网格，包含零事故格，每个尺度的事故总数均验证等于230,536。

下载旧版LAPD事故232,695条，按dr_no去重无重复；无效/研究区外粗坐标403条，市界外1,756条，保留230,536条。未因坐标重合删除事故。事故日期采用date_occ。原始坐标具有公开数据定位精度限制。

预先以5km地理块的固定哈希规则预留测试区域。凡网格与测试块相交，均排除于尺度拟合。以市界覆盖面积>=80%的格拟合，避免边界碎格的面积差异主导count变异。城市内全部格保存，原始count不做面积归一化。该80%阈值和空间留出规则属于本次实现选择，不是计划书既定结论。

主拟合使用球状半变异模型、0–25km的25箱、每箱至少30对、按配对数加权最小二乘、多初值。最多抽样2500格，种子575；细尺度抽样会影响估计。NSR分母为总sill。另输出8近邻行标准化Moran's I及199次置换诊断。粗尺度训练样本过少者记录too_few_cells，不强行拟合；这是31个尺度均已评估，并非31个尺度都有可靠拟合。

## 为什么不直接确认1100米

主模型下950m、1100m和1250m的NSR约为0.2704、0.2240和0.2259。局部下降后回升只有约0.0019，缺乏不确定性证据支持其为稳定极小值。

15/20/25/30km最大距离与球状/指数模型的敏感性分析显示局部低点随设定改变，指数拟合在多处nugget接近参数下界。近零nugget不等于可靠最优。四种网格原点在800–1850m范围比较：1100m在三种原点下存在局部低点，仅Y方向平移半格时低点移至1700m。尚未达到“第一个稳定低点”的要求。

完整31尺度表见04_outputs/grid_search/scale_diagnostics.csv；拟合敏感性见fit_sensitivity.csv；原点敏感性见origin_sensitivity.csv；机器可读决定见selection.json。

## 数据门槛与限制

旧事故接口2017–2021年度总数分别为57,727、57,159、56,628、42,385、18,796。2021年全年均有记录，但相对前期显著减少，原因尚未核实，不断言其缺失或真实下降。官方说明旧接口已停止更新并迁移RMS；必须进一步核查研究期完整性。新版s2yz-yg2p接口测试未提供可用记录。

已下载2021 TIGER/Line洛杉矶县道路、加州block groups、市界、General Plan Land Use、LADOT Traffic Counts位置和Signal Locations。道路清理输出是几何曲折度代理，不是完整物理曲率测量；MTFCC不自动等同于城市主干道等级。

ACS2021 API返回Missing Key网页，人口数值尚未取得，失败响应保留为.failed.html，不能替代为0。交通图层提供位置和NavigateLA报告链接，缺少计数日期/数值字段；位置覆盖只能作为潜在数据覆盖指标，不能用于证明2017–2021交通流量覆盖充分。当前土地利用与信号图层是访问时快照，需审计时间一致性。计划书的Vision Zero信号接口当前仅60对象，因此改用官方LADOT Signal Locations作为全市候选，但仍需审计。

Speed limit与视距没有纳入本次成品特征表；计划书将其设为覆盖审计后可选。尚未构建完整RF predictor table，也未训练RF。

## 后续确认条件

核实事故研究期记录；获得带日期与单位的交通数值并评估覆盖；完成拟合不确定性和边界阈值敏感性。如果仍无稳定唯一低点，应如实报告“无唯一稳定最优尺度”，选定并说明工作尺度及邻近尺度敏感性，不以测试集R²反选尺度。具体交接见07_agents/tasks。

## 来源

- 研究依据：00_admin/source/SSCI575_Project_Update.docx。
- LAPD元数据与数据：https://data.lacity.org/api/views/d5tf-ez2w.json 和 https://data.lacity.org/resource/d5tf-ez2w.json。
- 官方市界：https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/7。
- Census道路：https://www2.census.gov/geo/tiger/TIGER2021/ROADS/tl_2021_06037_roads.zip。
- Census BG：https://www2.census.gov/geo/tiger/TIGER2021/BG/tl_2021_06_bg.zip。
- ACS：https://api.census.gov/data/2021/acs/acs5。
- 土地利用：https://maps.lacity.org/lahub/rest/services/City_Planning_Department/MapServer/7。
- 交通位置：https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/22。
- 信号：https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/30。
- 方法参考：https://doi.org/10.1371/journal.pone.0225139；本次实现是针对项目的操作化方案，不声称逐项复现原论文。
## 已落盘的数据量

市界裁剪后：道路28,364条，block group几何2,941个，土地利用50,643个对象，交通计数位置6,800个对象，信号点5,506个。原始下载快照与清理结果分开保存。1,100m网格的交通位置覆盖率约68.86%，不代表具有2017–2021有效计数值的覆盖率。31尺度网格均通过事故总量守恒和几何有效性检查。

## 后续Range验证

已完成扩展距离和空间块删除诊断，详见06_reports/range_validation.md。1100m作为工作尺度的局部低点证据增强（45km球状拟合下52/53次空间块删除保留该低点），但经验曲线在约35–36km后下降，没有持续平台。不得把原39.3km Range表述为已证实；原主参数和最终尺度状态未自动更改。
