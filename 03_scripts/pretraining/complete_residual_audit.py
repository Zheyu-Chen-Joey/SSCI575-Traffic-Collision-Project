"""Publish descriptive hotspot findings and correction evidence without replacing RF."""
from pathlib import Path
import json,hashlib,shutil,datetime,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'.runtime'),str(R/'03_scripts/pretraining')]
import pandas as pd,numpy as np,geopandas as gpd,joblib
from rf_input_quality import input_quality_flags
from rf_local_weighted_model import LocalWeightedSpatialForest
O=R/'04_outputs/residual_investigation';S=R/'06_reports/_qa/missingness_correction';result=json.loads((S/'evaluation.json').read_text());assert not result['promote'];mp=R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib';assert hashlib.sha256(mp.read_bytes()).hexdigest()=='9378d2b1ced357e6b0e2329a9c485aa62475a2041077caee201d2b22dc150357'
audit=O/'correction_study';audit.mkdir(exist_ok=True)
for file in S.iterdir():
 if file.suffix in ['.csv','.json']:shutil.copy2(file,audit/file.name)
d=pd.read_csv(O/'per_grid_diagnostics.csv');flags=input_quality_flags(d);pd.concat([d[['grid_id','eligible','split']],flags],axis=1).to_csv(O/'input_quality_flags.csv',index=False)
model=joblib.load(mp);cols=list(model.feature_names_in_);parts=[LocalWeightedSpatialForest.predict(model,d[cols])]+[x.predict(d[cols])for x in model.orientation_models_];pd.DataFrame({'grid_id':d.grid_id,'prediction_0deg':parts[0],'prediction_45deg':parts[1],'prediction_60deg':parts[2],'orientation_prediction_range':np.ptp(parts,axis=0)}).to_csv(O/'orientation_disagreement.csv',index=False)
roads=gpd.read_file(R/'01_data/processed/roads_2021.gpkg');grid=gpd.read_file(R/'01_data/processed/pretraining_1km/grid_1000.gpkg');top=pd.read_csv(O/'top20_legacy_cells.csv');records=[]
for gid in top.grid_id.head(12):
 geom=grid.loc[grid.grid_id==gid,'geometry'].iloc[0];r=roads.iloc[roads.sindex.query(geom,predicate='intersects')].copy();r['clip_length_m']=r.geometry.intersection(geom).length;agg=r.groupby('FULLNAME').clip_length_m.sum().sort_values(ascending=False).head(4);records.append({'grid_id':gid,'reference_road_names':'; '.join(agg.index.astype(str)),'road_names_are_location_context_not_causes':True})
pd.DataFrame(records).to_csv(O/'case_road_context.csv',index=False)
x=pd.read_csv(audit/'legacy_comparison.csv').merge(d[['grid_id','all_missing_landuse','landuse_coverage']],on='grid_id',validate='one_to_one');rows=[]
for name,mask in [('all',np.ones(len(x),bool)),('all_missing_landuse',x.all_missing_landuse),('coverage_below50pct',x.landuse_coverage<.5),('coverage_atleast50pct',x.landuse_coverage>=.5)]:
 a=x.loc[mask]
 for prediction in ['before','after']:rows.append({'group':name,'model':prediction,'n':len(a),'rmse':float(np.sqrt(np.mean((a.observed-a[prediction])**2))),'mae':float(np.mean(abs(a.observed-a[prediction])))})
pd.DataFrame(rows).to_csv(O/'correction_subgroup_results.csv',index=False)
verification={'model_sha256_unchanged':hashlib.sha256(mp.read_bytes()).hexdigest(),'model_count':len(list((R/'05_models').rglob('*.joblib'))),'correction_promoted':False,'correction_reason':'Higher overall RMSE and MAE in exploratory reused region; no improvement in real missing-landuse RMSE','input_review_eligible_cells':int(flags.loc[d.eligible,'input_review_recommended'].sum()),'point_predictions_unchanged':True,'labels_changed':False,'source_snapshot_files_changed':False,'flags_are_calibrated_uncertainty':False,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};assert verification['model_count']==1;(O/'verification.json').write_text(json.dumps(verification,indent=2))
for rel in ['00_admin/latest_results.json','07_agents/status.json']:
 p=R/rel;state=json.loads(p.read_text(encoding='utf-8-sig'));state['residual_investigation']={'report':'06_reports/RF_Residual_Hotspots_Investigation.docx','outputs':'04_outputs/residual_investigation','recount_errors_found':False,'missingness_model_promoted':False,'input_quality_flags_added':True,'eligible_cells_flagged':verification['input_review_eligible_cells'],'limits':'Descriptive associations, no causal attribution; original region remains exploratory'};p.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'README.md';text=p.read_text(encoding='utf-8');note='''
## 高误差区域排查与纠错

已完成[高残差调查报告](06_reports/RF_Residual_Hotspots_Investigation.docx)及[诊断地图与逐格证据](04_outputs/residual_investigation)。独立重算事故、设施点、交叉口、道路与人口聚合未发现计数或拼接差异；土地利用50644个下载对象匹配ID快照。原227格中最差23格贡献64.7%的平方误差。训练集无土地利用全缺测格，原评估区有14格；机场用地主导训练格仅6个。两项均是解释线索，不能作为因果结论。

训练缺测模拟虽改善压力情景，但真实原区域RMSE80.63→81.84、MAE53.05→53.71，未替换当前模型。现有预测接口与GIS新增土地利用缺测、覆盖不足、机场零居住人口代理的输入提示，共标记45个合格格。提示不是置信区间，未标记也不保证准确。未修改事故数、补造土地利用或人工修正高误差格的预测。

'''
if '## 高误差区域排查与纠错'not in text:text=text.replace('## 使用与复现',note+'## 使用与复现')
p.write_text(text,encoding='utf-8');print(json.dumps(verification))
