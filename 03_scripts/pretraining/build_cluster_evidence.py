"""Reproduce weight audit, scale sensitivity and location context from frozen evidence."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'.runtime'))
import pandas as pd,numpy as np,geopandas as gpd
from scipy.spatial import cKDTree
O=R/'04_outputs/cluster_targeted_optimization';folds=json.loads((R/'04_outputs/rf_spatial_v5/cv_fold_ids.json').read_text());rows=[]
for fi,fold in enumerate(folds):
 expected=set(fold['buffered_fit_ids']);selected=None
 for file in (O/'global_and_local').glob(f'inner_diagnostics_{len(expected)}_*.csv'):
  d=pd.read_csv(file)
  if set(d.grid_id)==expected:selected=d;break
 assert selected is not None;d=selected.copy();w=np.minimum(1+d.hard_score*(.5+.5*d.same_sign_neighbor_fraction),3);d['weight']=w/w.mean();d['outer_fold']=fi;assert set(d.grid_id).isdisjoint(fold['eval_ids']);rows.append(d)
weights=pd.concat(rows);weights[['outer_fold','grid_id','weight','hard_score','same_sign_neighbor_fraction']].to_csv(O/'nested_training_weights.csv',index=False);means=weights.groupby('grid_id').weight.agg(['mean','count']).reset_index().rename(columns={'mean':'mean_training_weight','count':'fit_occurrences'});d=pd.read_csv(O/'training_oof_cluster_cells.csv');cells=d.merge(means,on='grid_id',how='left',validate='one_to_one');cells.to_csv(O/'training_cells_with_weight_audit.csv',index=False);cells.groupby('cluster_type').agg(n=('grid_id','size'),mean_weight=('mean_training_weight','mean'),mean_abs_error=('abs_error','mean')).to_csv(O/'weights_by_diagnostic_cluster.csv')
neighbors=cKDTree(d[['cx','cy']]).query_ball_point(d[['cx','cy']],1500);values={}
for name,residual in [('raw_residual',d.residual.to_numpy()),('count_scale_standardized_diagnostic',d.residual.to_numpy()/np.sqrt(np.maximum(d.oof_prediction.to_numpy(),1)))]:
 z=residual-residual.mean();numerator=0.;nrows=0
 for i,near in enumerate(neighbors):
  near=[j for j in near if j!=i]
  if near:numerator+=z[i]*np.mean(z[near]);nrows+=1
 values[name]=float(len(d)/nrows*numerator/(z@z))
(O/'residual_scale_sensitivity.json').write_text(json.dumps({'MoranI_queen1500m':values,'standardization':'residual/sqrt(max(prediction,1)), sensitivity only, not verified Poisson uncertainty','not_used_for_candidate_selection':True},indent=2))
roads=gpd.read_file(R/'01_data/processed/roads_2021.gpkg');grid=gpd.read_file(R/'01_data/processed/pretraining_1km/grid_1000.gpkg');clusters=pd.read_csv(O/'training_cluster_summary.csv').sort_values('n_cells',ascending=False).head(2);out=[]
for row in clusters.itertuples():
 geom=grid[grid.grid_id.isin(row.grid_ids.split(';'))].geometry.union_all();part=roads.iloc[roads.sindex.query(geom,predicate='intersects')].copy();part['clip_length_m']=part.geometry.intersection(geom).length;names=part.groupby('FULLNAME').clip_length_m.sum().sort_values(ascending=False).head(5).index.tolist();out.append({'cluster_id':row.cluster_id,'n_cells':row.n_cells,'reference_road_names':'; '.join(names),'only_location_context_not_cause':True})
pd.DataFrame(out).to_csv(O/'cluster_road_context.csv',index=False);print('Reproduced nested-weight audit, residual-scale sensitivity and road context')
