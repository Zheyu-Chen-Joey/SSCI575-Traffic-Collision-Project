"""Verify and promote a frozen development-selected coordinate RF blend."""
import pathlib,sys,json,hashlib,shutil,datetime
R=pathlib.Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'.runtime'),str(R/'03_scripts/pretraining')]
import numpy as np,pandas as pd,joblib
from sklearn.metrics import mean_squared_error,mean_absolute_error
P=R/'04_outputs/rf_spatial_v5';M=R/'05_models/rf_spatial_v5';S=R/'06_reports/_qa/orientation_ensemble'
result=json.loads((S/'evaluation.json').read_text());protocol=json.loads((S/'protocol.json').read_text());assert result['promote']and result['geographic_gate_pass']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(M/'spatial_frozen_rf.joblib')==protocol['reference_sha256']
src=R/'01_data/processed/pretraining_1km/model_table_1000_final.csv';assert sha(src)==protocol['input_sha256'];df=pd.read_csv(src);cols=json.loads((M/'input_contract.json').read_text())['features'];dev=df[df.eligible&df.split.isin(['train','validation'])];test=df[df.eligible&(df.split=='test')];old=joblib.load(M/'spatial_frozen_rf.joblib');new=joblib.load(S/'candidate.joblib');assert len(dev)==886 and len(test)==227 and df.count_2017_2021.sum()==230536
assert set(dev.block_id).isdisjoint(test.block_id)
for component in [new]+new.orientation_models_:
 assert component.training_rows_==886
 for pipeline in component.forests_:
  assert all(np.isclose(tree.tree_.weighted_n_node_samples[0],886)for tree in pipeline.named_steps['rf'].estimators_)
 assert all(np.isclose(forest.estimators_[0].tree_.weighted_n_node_samples[0],886)for forest in component.local_forests_)
before=old.predict(df[cols]);after=new.predict(df[cols]);assert np.isfinite(after).all()and(after>=0).all();mask=(df.eligible&(df.split=='test')).to_numpy();y=test.count_2017_2021.to_numpy()
assert np.isclose(np.sqrt(mean_squared_error(y,after[mask])),result['after']['rmse']);assert np.isclose(mean_absolute_error(y,after[mask]),result['after']['mae'])
ref=pd.read_csv(P/'reference_predictions.csv');assert 'Previous coordinate RF'not in ref
ref=ref.merge(pd.DataFrame({'grid_id':df.grid_id,'Previous coordinate RF':before}),on='grid_id',validate='one_to_one');ref.to_csv(P/'reference_predictions.csv',index=False)
meta=json.loads((P/'reference_predictions_metadata.json').read_text());meta['sha256']=sha(P/'reference_predictions.csv');meta['references'].append({'label':'Previous coordinate RF','original_model_sha256':protocol['reference_sha256'],'role':'frozen previous champion predictions; model entity replaced by coordinate RF blend'});(P/'reference_predictions_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
for study in ['orientation_ensemble']:
 source=R/'06_reports/_qa'/study;dest=P/'orientation_optimization'/study;dest.mkdir(parents=True,exist_ok=True)
 for file in source.iterdir():
  if file.suffix in ['.csv','.json']:shutil.copy2(file,dest/file.name)
decision=json.loads((P/'frozen_decision.json').read_text());decision.update(model_id='orientation_RF_0_45_60_025_025_050',model_class='rf_orientation_ensemble.OrientationEnsembleForest',comparison_anchor_label='Previous coordinate RF',orientation_settings={'orientation_angles':result['decision']['angles'],'orientation_weights':result['decision']['weights']},frozen_utc=result['decision']['frozen_utc'],optimization_audit='04_outputs/rf_spatial_v5/orientation_optimization',exploratory_promotion_after_legacy_gate=True)
decision.pop('coordinate_blend_settings',None)
(P/'frozen_decision.json').write_text(json.dumps(decision,indent=2),encoding='utf-8');ev=json.loads((P/'evaluation.json').read_text());ev['decision']=decision;ev['spatial_v5']['legacy_evaluation']=result['after'];ev['orientation_ensemble_study']=result;(P/'evaluation.json').write_text(json.dumps(ev,indent=2),encoding='utf-8')
details=pd.DataFrame({'grid_id':test.grid_id,'observed':y,'previous_pred':before[mask],'current_pred':after[mask],'previous_abs_error':abs(y-before[mask]),'current_abs_error':abs(y-after[mask])});details['delta_abs_error']=details.current_abs_error-details.previous_abs_error;details.to_csv(P/'orientation_optimization/per_grid_improvement.csv',index=False)
summary={'improved_cells':int((details.delta_abs_error<0).sum()),'worsened_cells':int((details.delta_abs_error>0).sum()),'unchanged_cells':int((details.delta_abs_error==0).sum()),'rmse_reduction_pct':100*(1-result['after']['rmse']/result['before']['rmse']),'mae_reduction_pct':100*(1-result['after']['mae']/result['before']['mae']),'p90_reduction_pct':100*(1-result['after']['p90_abs_error']/result['before']['p90_abs_error'])}
(P/'orientation_optimization/improvement_summary.json').write_text(json.dumps(summary,indent=2))
shutil.copyfile(S/'candidate.joblib',M/'spatial_frozen_rf.joblib');assert sha(M/'spatial_frozen_rf.joblib')==sha(S/'candidate.joblib')
verification={'source_sha256':sha(src),'previous_model_sha256':protocol['reference_sha256'],'new_model_sha256':sha(M/'spatial_frozen_rf.joblib'),'development_rows':886,'legacy_rows':227,'both_components_global_and_local_root_weights_match886':True,'finite_nonnegative1473predictions':True,'reloaded_metrics_match':True,'grid_count_conserved':230536,'production_model_count':len(list((R/'05_models').rglob('*.joblib'))),'promoted_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};assert verification['production_model_count']==1
(P/'orientation_optimization/promotion_verification.json').write_text(json.dumps(verification,indent=2));print(json.dumps(summary));print(json.dumps(verification))
