"""Audit high-error cells against processed sources; descriptive, not causal."""
import pathlib,sys,json,hashlib,collections
R=pathlib.Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'.runtime'),str(R/'03_scripts/pretraining')]
import numpy as np,pandas as pd,geopandas as gpd,joblib
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from pipeline_definition import LANDUSE
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
O=R/'04_outputs/residual_investigation';O.mkdir(exist_ok=True);P=R/'01_data/processed/pretraining_1km';Q=R/'04_outputs/rf_spatial_v5';source=P/'model_table_1000_final.csv';df=pd.read_csv(source);contract=json.loads((R/'05_models/rf_spatial_v5/input_contract.json').read_text());cols=contract['features'];model=joblib.load(R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib');assert type(model).__name__=='OrientationEnsembleForest'
pred=pd.read_csv(Q/'spatial_predictions_1000.csv')[['grid_id','spatial_pred','spatial_resid']];d=df.merge(pred,on='grid_id',validate='one_to_one');assert np.allclose(d.spatial_pred,model.predict(d[cols]));d['residual']=d.count_2017_2021-d.spatial_pred;d['abs_error']=abs(d.residual);d['smape_pct']=np.where(d.count_2017_2021+d.spatial_pred>0,200*d.abs_error/(d.count_2017_2021+d.spatial_pred),0);d['squared_error']=d.residual**2
# Independent target/point-feature recount using the exact half-open square rule.
origin=np.array([345000.,3730000.]);pts=gpd.read_file(R/'01_data/processed/collisions_2017_2021.gpkg');assert pts.crs.to_epsg()==26911;xy=np.c_[pts.geometry.x,pts.geometry.y];ij=np.floor((xy-origin)/1000).astype(int);pts['grid_id']=[f'1000_{i}_{j}'for i,j in ij];counts=pts.grid_id.value_counts();target_diff=d.count_2017_2021-d.grid_id.map(counts).fillna(0);years=pd.to_datetime(pts.date_occ).dt.year;annual=pd.crosstab(pts.grid_id,years);annual_diffs={str(year):int((d[f'count_{year}']-d.grid_id.map(annual[year]).fillna(0)).abs().sum())for year in range(2017,2022)}
def recount(path,unique=False):
 g=gpd.read_file(path);assert g.crs.to_epsg()==26911
 if unique:g['xykey']=[(round(p.x,1),round(p.y,1))for p in g.geometry];g=g.drop_duplicates('xykey')
 keys=np.floor((np.c_[g.geometry.x,g.geometry.y]-origin)/1000).astype(int);return collections.Counter(f'1000_{i}_{j}'for i,j in keys)
sig=recount(R/'01_data/processed/signal_locations.gpkg',True);nodes=recount(P/'intersection_tiger_topology.gpkg');roads=pd.read_csv(P/'road_crosswalk.csv').groupby('grid_id').part_length_m.sum();pop=pd.read_csv(P/'population_crosswalk.csv').groupby('grid_id').pop_part.sum();check={'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256((R/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib').read_bytes()).hexdigest(),'collision_rows':len(pts),'unique_collision_ids':int(pts.dr_no.nunique()),'target_total':int(d.count_2017_2021.sum()),'total_recount_abs_difference':float(target_diff.abs().sum()),'annual_recount_abs_differences':annual_diffs,'signal_recount_abs_difference':float((d.signal_point_count-d.grid_id.map(sig).fillna(0)).abs().sum()),'intersection_recount_abs_difference':float((d.intersection_count-d.grid_id.map(nodes).fillna(0)).abs().sum()),'road_length_crosswalk_max_abs_diff_m':float((d.road_length_m-d.grid_id.map(roads).fillna(0)).abs().max()),'population_crosswalk_max_abs_diff':float((d.population-d.grid_id.map(pop)).abs().max()),'density_checks':{name:bool(np.allclose(d[density],d[count]/d.city_area_km2,equal_nan=True))for name,density,count in [('population','population_density_km2','population'),('roads','road_density_km_per_km2','road_length_m'),('signals','signal_density_snapshot_km2','signal_point_count'),('intersections','intersection_density_km2','intersection_count')]if name!='roads'},'road_density_check':bool(np.allclose(d.road_density_km_per_km2,d.road_length_m/1000/d.city_area_km2,equal_nan=True))}
assert len(pts)==230536 and check['unique_collision_ids']==230536 and not target_diff.any()and not any(annual_diffs.values());assert check['signal_recount_abs_difference']==0 and check['intersection_recount_abs_difference']==0;assert check['road_length_crosswalk_max_abs_diff_m']<1e-5 and check['population_crosswalk_max_abs_diff']<1e-5;assert all(check['density_checks'].values())and check['road_density_check']
# Verify the recorded land-use ID snapshot, not real-world or historical completeness.
expected=json.loads((R/'01_data/raw/landuse_ids.json').read_text())['objectIds'];downloaded=[];bad_batches=[]
for file in (R/'01_data/raw').glob('landuse_batch_*.json'):
 response=json.loads(file.read_text())
 if response.get('error')or response.get('exceededTransferLimit'):bad_batches.append(file.name)
 assert isinstance(response.get('features'),list)
 downloaded += [f.get('properties',f.get('attributes',{}))['OBJECTID']for f in response['features']]
assert set(downloaded)==set(expected)and len(downloaded)==len(set(downloaded))and not bad_batches
lu=gpd.read_file(R/'01_data/processed/landuse.gpkg');geoms=gpd.read_file(P/'grid_1000.gpkg');missing_cells=d[d.eligible&d[LANDUSE].isna().all(axis=1)]
lu_audit={'expected_snapshot_objects':len(expected),'downloaded_objects':len(downloaded),'duplicate_object_ids':0,'missing_object_ids':0,'unexpected_object_ids':0,'error_or_transfer_limit_batches':bad_batches,'processed_city_features':len(lu),'eligible_all_missing_landuse_grid_count':len(missing_cells),'processed_polygon_intersections_at_missing_cells':{gid:int(len(lu.sindex.query(geoms.loc[geoms.grid_id==gid,'geometry'].iloc[0],predicate='intersects')))for gid in missing_cells.grid_id},'interpretation':'Matches recorded ID snapshot; does not prove source completeness or historical validity.'}
(O/'landuse_download_audit.json').write_text(json.dumps(lu_audit,indent=2))
# Use frozen out-of-fold/validation predictions to explore development errors.
T=Q/'orientation_optimization/orientation_ensemble';oo=pd.read_csv(T/'oof_predictions.csv')[['grid_id','8']].rename(columns={'8':'development_prediction'});vv=pd.read_csv(T/'validation_predictions.csv')[['grid_id','8']].rename(columns={'8':'development_prediction'});oo['prediction_role']='training_1km_gap_OOF';vv['prediction_role']='validation_fit720';d=d.merge(pd.concat([oo,vv]),on='grid_id',how='left',validate='one_to_one');d['diagnostic_prediction']=np.where(d.split=='test',d.spatial_pred,d.development_prediction);d['diagnostic_residual']=d.count_2017_2021-d.diagnostic_prediction;d['diagnostic_abs_error']=abs(d.diagnostic_residual);d['all_missing_landuse']=d[LANDUSE].isna().all(axis=1);d['low_landuse_coverage']=d.landuse_coverage<.5;d['population_moe_relative']=d.population_moe90_approx/d.population.replace(0,np.nan);d['report_2021_share']=d.count_2021/d.count_2017_2021.replace(0,np.nan);d['most_concentrated_year_share']=d[[f'count_{y}'for y in range(2017,2022)]].max(axis=1)/d.count_2017_2021.replace(0,np.nan);d['top10_coordinate_share']=np.nan
for gid,group in pts.groupby('grid_id'):
 frequencies=group.groupby(['lon','lat']).size().sort_values(ascending=False);d.loc[d.grid_id==gid,'top10_coordinate_share']=frequencies.head(10).sum()/len(group)
dev=d[d.eligible&(d.split!='test')].copy();legacy=d[d.eligible&(d.split=='test')].copy();subgroups=[]
for role,frame in [('development_OOF_or_validation',dev),('legacy_reused_exploratory',legacy)]:
 threshold=frame.diagnostic_abs_error.quantile(.9);high=frame.diagnostic_abs_error>=threshold;frame['high_error']=high
 groups={'all':np.ones(len(frame),bool),'top10pct_absolute_error':high,'all_missing_landuse':frame.all_missing_landuse,'landuse_coverage_below50pct':frame.low_landuse_coverage,'landuse_coverage_atleast50pct':~frame.low_landuse_coverage,'freeway_share_above20pct':frame.freeway_share_functional>.2,'population_zero':frame.population==0,'observed_count_ge500':frame.count_2017_2021>=500,'observed_count_lt50':frame.count_2017_2021<50}
 for name,mask in groups.items():
  s=frame.loc[mask]
  if len(s):subgroups.append({'role':role,'group':name,'n':len(s),'rmse':float(np.sqrt(np.mean(s.diagnostic_residual**2))),'mae':float(s.diagnostic_abs_error.mean()),'mean_observed_minus_predicted':float(s.diagnostic_residual.mean()),'high_error_fraction':float(s.high_error.mean()),'median_landuse_coverage':float(s.landuse_coverage.median()),'median_observed':float(s.count_2017_2021.median())})
pd.DataFrame(subgroups).to_csv(O/'subgroup_diagnostics.csv',index=False)
features=['road_density_km_per_km2','intersection_density_km2','population_density_km2','landuse_coverage','freeway_share_functional','signal_density_snapshot_km2','population_moe_relative','report_2021_share','top10_coordinate_share'];assoc=[]
for role,frame in [('development_OOF_or_validation',dev),('legacy_reused_exploratory',legacy)]:
 for f in features:
  valid=frame[[f,'diagnostic_abs_error']].dropna();rho,p=spearmanr(valid[f],valid.diagnostic_abs_error);assoc.append({'role':role,'feature':f,'spearman_abs_error':float(rho),'descriptive_p':float(p),'n':len(valid)})
pd.DataFrame(assoc).to_csv(O/'descriptive_associations.csv',index=False)
# Feature-range flags are defined by development features, never by legacy outcomes.
training=d[d.eligible&(d.split=='train')];numeric=[c for c in cols if c!='road_type_dominant'];qlo=training[numeric].quantile(.01);qhi=training[numeric].quantile(.99);d['feature_extreme_count']=((d[numeric]<qlo)|(d[numeric]>qhi)).sum(axis=1);d['feature_missing_count']=d[cols].isna().sum(axis=1)
center=gpd.GeoDataFrame(d[['grid_id']],geometry=gpd.points_from_xy(d.cx,d.cy),crs=26911).to_crs(4326);d['center_longitude']=center.geometry.x;d['center_latitude']=center.geometry.y
for role,mask in [('legacy',d.eligible&(d.split=='test')),('development',d.eligible&(d.split!='test'))]:
 top=d.loc[mask].sort_values('diagnostic_abs_error',ascending=False).head(20).copy();top['diagnostic_rank']=np.arange(1,len(top)+1);top['error_direction']=np.where(top.diagnostic_residual>0,'underprediction','overprediction');top.to_csv(O/f'top20_{role}_cells.csv',index=False)
top=legacy.nlargest(23,'diagnostic_abs_error');check['legacy_top23_share_squared_error']=float((top.diagnostic_residual**2).sum()/(legacy.diagnostic_residual**2).sum());check['legacy_top23_share_abs_error']=float(top.diagnostic_abs_error.sum()/legacy.diagnostic_abs_error.sum());check['legacy_all_missing_landuse_n']=int(legacy.all_missing_landuse.sum());check['train_all_missing_landuse_n']=int(training.all_missing_landuse.sum());check['validation_all_missing_landuse_n']=int(d.loc[d.eligible&(d.split=='validation'),'all_missing_landuse'].sum());check['no_confirmed_recount_or_join_error']=True
(O/'source_audit.json').write_text(json.dumps(check,indent=2));d.drop(columns=['traffic_volume_2017_2021']).to_csv(O/'per_grid_diagnostics.csv',index=False)
grid=gpd.read_file(P/'grid_1000.gpkg')[['grid_id','geometry']].merge(d,on='grid_id',validate='one_to_one');grid.to_file(O/'residual_diagnostics.gpkg',driver='GPKG');eligible=grid[grid.eligible];test=eligible[eligible.split=='test'];limit=341.457935510193
fig,axes=plt.subplots(1,3,figsize=(14,7))
for ax in axes:grid.plot(ax=ax,color='#eeeeee');ax.set_axis_off()
test.plot(column='residual',ax=axes[0],cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),legend=True,legend_kwds={'shrink':.45});axes[0].set_title('Legacy residuals | observed minus predicted')
test.plot(column='abs_error',ax=axes[1],cmap='YlOrRd',vmin=0,vmax=limit,legend=True,legend_kwds={'shrink':.45});axes[1].set_title('Absolute error | units: collisions per cell')
eligible.assign(coverage_display=eligible.landuse_coverage.clip(0,1)).plot(column='coverage_display',ax=axes[2],cmap='viridis',vmin=0,vmax=1,legend=True,legend_kwds={'shrink':.45});test.boundary.plot(ax=axes[2],color='black',linewidth=.25);axes[2].set_title('Land-use source polygon coverage')
for rank,(_,row)in enumerate(test.nlargest(8,'abs_error').iterrows(),1):axes[1].annotate(str(rank),(row.cx,row.cy),fontsize=7,xytext=(3,3),textcoords='offset points')
fig.suptitle('1 km cells | descriptive error audit, not causal attribution or independent validation');fig.tight_layout();fig.savefig(O/'error_hotspots_and_coverage.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(json.dumps(check,indent=2));print(pd.DataFrame(subgroups).to_string(index=False));print('TOP DEV',dev.nlargest(5,'diagnostic_abs_error')[['grid_id','diagnostic_abs_error','landuse_coverage']].to_string(index=False))
