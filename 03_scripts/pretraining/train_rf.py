"""Future training entry point. This task does NOT execute it with --execute-training."""
import sys,pathlib,json,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))

def main():
 parser=argparse.ArgumentParser(description='Requires explicit execution and passing data gate. Default is no training.');parser.add_argument('--execute-training',action='store_true');args=parser.parse_args()
 if not args.execute_training:
  print('No training executed. Use prepare_training.py --check-only for data checks. A later explicitly authorized run can use --execute-training after the data gate passes.');return 0
 import numpy as np,pandas as pd,joblib
 from sklearn.model_selection import GridSearchCV
 from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
 from scipy.spatial import cKDTree
 from pipeline_definition import make_pipeline,feature_names,training_cv,PARAM_GRID
 gate=json.loads((ROOT/'04_outputs/pretraining/readiness.json').read_text())
 if gate.get('blocking_items'):raise RuntimeError('Data readiness blocked: '+json.dumps(gate['blocking_items']))
 df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');df=df[df.eligible];train=df[df.split=='train'];val=df[df.split=='validation'];test=df[df.split=='test'];assert len(set(train.block_id)&set(test.block_id))==0;assert len(set(val.block_id)&set(test.block_id))==0
 out=ROOT/'05_models/trained';out.mkdir(exist_ok=True);report={}
 # Each full pipeline is fitted within training-only group CV. No test access in selection.
 for variant in ['baseline','enhanced']:
  cols=feature_names(variant)
  if train[cols].isna().all().any():raise RuntimeError('A complete training covariate is missing')
  search=GridSearchCV(make_pipeline(variant),PARAM_GRID,cv=training_cv(),scoring='neg_root_mean_squared_error',n_jobs=1,refit=True);search.fit(train[cols],train.count_2017_2021,groups=train.block_id)
  pred_val=search.predict(val[cols]);validation={'rmse':float(np.sqrt(mean_squared_error(val.count_2017_2021,pred_val))),'mae':float(mean_absolute_error(val.count_2017_2021,pred_val)),'r2':float(r2_score(val.count_2017_2021,pred_val))}
  # Freeze tuned parameters, refit only on development rows, then evaluate the test once.
  development=pd.concat([train,val],ignore_index=True);model=make_pipeline(variant).set_params(**search.best_params_);model.fit(development[cols],development.count_2017_2021);pred=model.predict(test[cols]);res=test.count_2017_2021.to_numpy()-pred
  xy=test[['cx','cy']].to_numpy();k=min(8,len(test)-1);_,nn=cKDTree(xy).query(xy,k=k+1);nn=nn[:,1:];z=res-res.mean();den=np.sum(z*z);I=float(np.sum(z[:,None]*z[nn])/k/den) if den>0 else None
  rng=np.random.default_rng(575);perms=[]
  if I is not None:
   for _ in range(999):
    q=rng.permutation(z);perms.append(np.sum(q[:,None]*q[nn])/k/den)
  mp=float((1+np.sum(abs(np.array(perms)+1/(len(z)-1))>=abs(I+1/(len(z)-1))))/1000) if I is not None else None
  report[variant]={'best_parameters':search.best_params_,'training_group_cv_rmse':float(-search.best_score_),'validation_before_refit':validation,'test_after_refit':{'rmse':float(np.sqrt(mean_squared_error(test.count_2017_2021,pred))),'mae':float(mean_absolute_error(test.count_2017_2021,pred)),'r2':float(r2_score(test.count_2017_2021,pred)),'residual_moran_i_knn8':I,'residual_moran_p_999':mp},'features':cols,'limitations':gate.get('review_items',[])}
  joblib.dump(model,out/f'{variant}_rf.joblib');pd.DataFrame({'grid_id':test.grid_id,'observed':test.count_2017_2021,'predicted':pred,'residual':res}).to_csv(out/f'{variant}_test_predictions.csv',index=False)
 (out/'evaluation.json').write_text(json.dumps(report,indent=2));print('Training complete. No deployment performed.');return 0
if __name__=='__main__':sys.exit(main())
