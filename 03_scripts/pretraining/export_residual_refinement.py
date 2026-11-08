"""Visual and independent verification for exploratory residual refinement."""
import sys,pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,geopandas as gpd,joblib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from sklearn.metrics import mean_squared_error,r2_score
from pipeline_definition import feature_names
O=ROOT/'04_outputs/rf_residual_refinement_v2';M=ROOT/'05_models/rf_residual_refinement_v2';ev=json.loads((O/'evaluation.json').read_text());decision=ev['decision'];pr=pd.read_csv(O/'all_predictions.csv');df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');cols=feature_names('enhanced');test=df[df.eligible&(df.split=='test')];grids=gpd.read_file(ROOT/'01_data/processed/pretraining_1km/grid_1000.gpkg');g=grids[['grid_id','geometry']].merge(df,on='grid_id');F=O/'figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.dpi':180})
for label in ['v1_anchor','v2_frozen']:
 model=joblib.load(M/f'{label}_rf.joblib');p=model.predict(test[cols]);assert np.isclose(np.sqrt(mean_squared_error(test.count_2017_2021,p)),ev[label]['legacy_test']['rmse']);assert np.isclose(r2_score(test.count_2017_2021,p),ev[label]['legacy_test']['r2']);assert all(np.isclose(t.tree_.weighted_n_node_samples[0],886)for t in model.named_steps['rf'].estimators_);allp=pr[pr.model==label];assert len(allp)==1473;assert np.allclose(model.predict(df[cols]),allp.predicted);assert np.allclose(allp.residual,allp.count_2017_2021-allp.predicted)
 g=g.merge(allp[['grid_id','predicted','residual']].rename(columns={'predicted':label+'_pred','residual':label+'_resid'}),on='grid_id',validate='one_to_one')
protocol=json.loads((O/'protocol.json').read_text());assert hashlib.sha256((ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv').read_bytes()).hexdigest()==protocol['input_sha256'];old=joblib.load(ROOT/'05_models/rf_project_v1/enhanced_optimized_rf.joblib');assert np.allclose(old.predict(test[cols]),joblib.load(M/'v1_anchor_rf.joblib').predict(test[cols]));g['role']=np.where(~g.eligible,'boundary_extrapolation',np.where(g.split=='test','legacy_test_reuse','development_in_sample'));g.to_file(O/'grid_comparison_1000.gpkg',driver='GPKG');g.drop(columns='geometry').to_csv(O/'grid_comparison_1000.csv',index=False)
t=g[g.eligible&(g.split=='test')];maxabs=max(t.v1_anchor_resid.abs().max(),t.v2_frozen_resid.abs().max());fig,axes=plt.subplots(1,2,figsize=(9,8))
for ax,key,title in zip(axes,['v1_anchor_resid','v2_frozen_resid'],['V1 residuals','V2 frozen residuals'if decision['selected_candidate']else'V1 retained (no joint improvement)']):
 g.plot(ax=ax,color='#e9e9e9',edgecolor='white',linewidth=.08);t.plot(column=key,ax=ax,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-maxabs,vcenter=0,vmax=maxabs),legend=True,legend_kwds={'shrink':.4});ax.set_title(title);ax.set_axis_off()
fig.suptitle('Same legacy evaluation cells and color scale | observed minus predicted');fig.savefig(F/'01_legacy_test_residual_comparison.png',bbox_inches='tight');plt.close(fig)
# Full-city overview deliberately labels fitted versus legacy holdout roles.
e=g[g.eligible];maxabs=max(e.v1_anchor_resid.abs().max(),e.v2_frozen_resid.abs().max());fig,axes=plt.subplots(1,2,figsize=(10,8))
for ax,key,title in zip(axes,['v1_anchor_resid','v2_frozen_resid'],['V1 full-city residual overview','V2 full-city residual overview'if decision['selected_candidate']else'V1 retained full-city overview']):
 g.plot(ax=ax,color='#eeeeee');e.plot(column=key,ax=ax,cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-maxabs,vcenter=0,vmax=maxabs),legend=True,legend_kwds={'shrink':.4});t.boundary.plot(ax=ax,color='black',linewidth=.35);ax.set_axis_off();ax.set_title(title)
fig.suptitle('1113 eligible cells | black outlines = legacy test cells\nOther colored cells are development fitted residuals, not independent evaluation',fontsize=11);fig.savefig(F/'02_full_city_residual_overview.png',bbox_inches='tight');plt.close(fig)
s=pd.read_csv(O/'cv_candidate_scores.csv');fig,ax=plt.subplots(figsize=(7,4.8));ax.scatter(s.rmse,s.moran_i.abs(),color='#8d9eb0',label='RF candidates');a=s.iloc[0];ax.scatter([a.rmse],[abs(a.moran_i)],color='#537aa3',s=80,label='V1 anchor');b=s[s.candidate==decision['selected_candidate']].iloc[0];ax.scatter([b.rmse],[abs(b.moran_i)],marker='*',color='#bf6738',s=180,label='Frozen selection');ax.set(xlabel='Training pooled out-of-fold RMSE',ylabel='Absolute pooled OOF residual Moran I',title='Lower left is preferred | training-only screening');ax.legend();fig.savefig(F/'03_cv_tradeoff.png',bbox_inches='tight');plt.close(fig)
val=pd.read_csv(O/'validation_scores.csv');met=pd.DataFrame([{'model':k,**ev[k]['legacy_test'],'moran_i':ev[k]['moran']['I']}for k in ['v1_anchor','v2_frozen']]);met.to_csv(O/'legacy_test_metrics.csv',index=False)
text=f'''残差优化复核报告

性质：第一轮测试结果已被查看后启动的探索性研究。旧测试区没有参与本轮选择或拟合，但再次评估不构成全新独立验证。原v1所有文件保留。

方法：沿用1km、现有16字段和RF回归，未加入坐标、邻居事故数或HIN；避免目标空间泄漏。原500树/深度8模型为候选0，另抽取24组参数，训练720格按原5km块做5折CV。用训练区折外残差Moran与RMSE联合筛选；折外残差来自不同折模型，空间诊断仅作开发筛选代理。
只把折外RMSE不超过原模型2%、且绝对Moran下降的候选按Moran排序，最多3个进入原166格验证区。验证RMSE不得升高且绝对Moran必须下降，才可采用；否则保留v1。决策在旧测试评估前冻结。

开发决策：{decision['reason']}
选中候选：{decision['selected_candidate']}
参数：{json.dumps(decision['parameters'],ensure_ascii=False)}

训练区CV汇总：
{s.to_string(index=False)}

验证区结果：
{val.to_string(index=False)}

旧测试区探索性对照：
{met.to_string(index=False)}
原模型p={ev['v1_anchor']['moran']['p_two_sided']}，本轮冻结模型p={ev['v2_frozen']['moran']['p_two_sided']}；9999次双侧置换。残差=实际−预测。红=低估，蓝=高估，深色代表绝对误差较大。所有对比使用相同格和同一色标；不得通过色标变化制造改善。

地图：01图仅为原227测试格对照；02图显示全市1113合格格，黑色边界标出旧测试区，其余有色格为开发区拟合残差，不能用全图更浅来证明独立精度提高。边界不足80%的格为灰色。

解释：降低RMSE不保证降低残差空间自相关，反之亦然。本轮不平滑真实残差、不删除高误差格、不把训练残差当独立精度。即使通过开发门槛，旧测试区仍可能出现不同方向变化。没有新空间或时间外部数据，不能重新获得完全独立验证；原始快照时间一致性、2021记录问题和缺少交通暴露仍限制模型。

复现：03_scripts/pretraining/refine_rf_residuals.py；导出与独立重载校验：export_residual_refinement.py。模型与中间CSV均以v2目录保存，旧v1模型和报告不覆盖。推荐状态依据开发门槛记录，不使用旧测试分数反复调整。
''';(ROOT/'06_reports/Residual_Refinement_v2.txt').write_text(text,encoding='utf-8');(O/'verification.json').write_text(json.dumps({'status':'pass','reloaded_model_metrics_match':True,'v1_anchor_reproduces_frozen_v1':True,'input_hash_unchanged':True,'development_fit_rows':886,'legacy_test_not_fit':True,'legacy_test_is_not_new_independent_validation':True,'grid_rows':1473,'selected_candidate':decision['selected_candidate']},indent=2));print(text[-2600:])
