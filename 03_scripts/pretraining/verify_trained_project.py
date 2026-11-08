"""Independent artifact checks; never fits or selects a model."""
import sys,pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import pandas as pd,numpy as np,joblib,geopandas as gpd
from sklearn.metrics import r2_score,mean_absolute_error,mean_squared_error
from pipeline_definition import feature_names
O=ROOT/'04_outputs/rf_project_v1';M=ROOT/'05_models/rf_project_v1';protocol=json.loads((O/'training_protocol.json').read_text());dfile=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';assert hashlib.sha256(dfile.read_bytes()).hexdigest()==protocol['input_sha256'];df=pd.read_csv(dfile);ev=json.loads((M/'evaluation.json').read_text());allpred=pd.read_csv(O/'all_predictions.csv');t=df[df.eligible&(df.split=='test')];dev=df[df.eligible&(df.split!='test')];checks=[]
for fold in protocol['folds']:
 a=df[df.grid_id.isin(fold['train_grid_ids'])];b=df[df.grid_id.isin(fold['valid_grid_ids'])];assert set(a.split)=={'train'}and set(b.split)=={'train'};assert not(set(a.block_id)&set(b.block_id))
checks.append('all5CVfolds_train_only_and_block_disjoint')
for v in ['baseline','enhanced']:
 cols=feature_names(v);assert not any(c.startswith('count_')or c in ['grid_id','split','block_id','cx','cy','i','j','hin_length_m'] for c in cols)
 for stage in ['initial','optimized']:
  key=v+'_'+stage;model=joblib.load(M/f'{key}_rf.joblib');p=model.predict(t[cols]);r=ev[key]['test'];assert np.isclose(r['rmse'],np.sqrt(mean_squared_error(t.count_2017_2021,p)));assert np.isclose(r['mae'],mean_absolute_error(t.count_2017_2021,p));assert np.isclose(r['r2'],r2_score(t.count_2017_2021,p));assert np.isfinite(p).all()and(p>=0).all();out=allpred[(allpred.variant==v)&(allpred.stage==stage)];assert len(out)==1473 and out.grid_id.is_unique;assert np.allclose(model.predict(df[cols]),out.predicted);assert np.allclose(out.residual,out.count_2017_2021-out.predicted);assert len(out[out.prediction_role=='heldout_test'])==227
  rf=model.named_steps['rf'];assert all(np.isclose(tree.tree_.weighted_n_node_samples[0],len(dev))for tree in rf.estimators_);assert len(rf.estimators_)==ev[key]['params']['rf__n_estimators'];checks.append(key+'_reload_metrics_predictions_and886fit_mass')
g=gpd.read_file(O/'grid_predictions_1000.gpkg',layer='grid_predictions');assert len(g)==1473 and g.crs.to_epsg()==26911;assert g.count_2017_2021.sum()==230536
for manifest in ['00_admin/file_manifest.json','00_admin/speed_download_manifest.json','00_admin/hin_manifest.json']:
 m=json.loads((ROOT/manifest).read_text());rows=m['files']if isinstance(m,dict)else m
 for row in rows:
  f=ROOT/(row.get('path')or row.get('file'));assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'],str(f)
checks.extend(['all1473GISrows_EPSG26911_conserved230536','old_speed_and_HIN_raw_hashes_verified','no_target_partition_HIN_in_model_features'])
files=[{'path':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}for f in sorted(M.glob('*'))if f.is_file()];(O/'verification.json').write_text(json.dumps({'status':'pass','checks':checks,'models_and_evaluation':files,'test_used_for_tuning':False},indent=2));print('PASS',len(checks),'checks')
