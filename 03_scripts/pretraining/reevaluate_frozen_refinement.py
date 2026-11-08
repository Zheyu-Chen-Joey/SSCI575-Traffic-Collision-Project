"""Exploratory RF refinement: train-only CV, residual-autocorrelation objective, validation gate."""
import sys,pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd,joblib
from sklearn.model_selection import GroupKFold,ParameterSampler
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from pipeline_definition import make_pipeline,feature_names
O=ROOT/'04_outputs/rf_residual_refinement_v2';M=ROOT/'05_models/rf_residual_refinement_v2';O.mkdir(exist_ok=True);M.mkdir(exist_ok=True)
def write(v,name): (O/name).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if hasattr(x,'item')else str(x)),encoding='utf-8')
def metrics(y,p):return {'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'bias':float(np.mean(p-y))}
def moran(res,xy,perm=0):
 z=np.asarray(res)-np.mean(res);n=len(z);k=min(8,n-1);ix=cKDTree(xy).query(xy,k=k+1)[1][:,1:];den=z@z;I=float((z[:,None]*z[ix]).sum()/k/den);result={'I':I,'n':n,'k':k}
 if perm:
  rng=np.random.default_rng(575);v=[]
  for _ in range(perm):
   q=rng.permutation(z);v.append(float((q[:,None]*q[ix]).sum()/k/den))
  result['p_two_sided']=float((1+sum(np.abs(np.array(v)+1/(n-1))>=abs(I+1/(n-1))))/(perm+1));result['permutations']=perm
 return result

src=ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv';df=pd.read_csv(src);e=df[df.eligible];tr=e[e.split=='train'].copy();va=e[e.split=='validation'].copy();dev=pd.concat([tr,va],ignore_index=True);cols=feature_names('enhanced');candidates=json.loads((O/'protocol.json').read_text())['candidates'];decision=json.loads((O/'frozen_decision.json').read_text());selected=decision['selected_candidate']
def pipe(params):return make_pipeline('enhanced').set_params(rf__n_jobs=4,**params)
# No further optimization after freezing; legacy test is descriptive re-use only.
test=e[e.split=='test'];y=test.count_2017_2021.to_numpy();ev={};allrows=[]
for label,ci in [('v1_anchor',0),('v2_frozen',selected)]:
 fit=pipe(candidates[ci]);fit.fit(dev[cols],dev.count_2017_2021);p=fit.predict(test[cols]);ev[label]={'legacy_test':metrics(y,p),'moran':moran(y-p,test[['cx','cy']],9999),'candidate':ci};joblib.dump(fit,M/f'{label}_rf.joblib');out=df[['grid_id','split','eligible','count_2017_2021','cx','cy']].copy();out['model']=label;out['predicted']=fit.predict(df[cols]);out['residual']=out.count_2017_2021-out.predicted;out['prediction_role']=np.where(~out.eligible,'boundary_extrapolation_not_evaluated',np.where(out.split=='test','legacy_test_reuse','development_in_sample'));allrows.append(out)
ev['decision']=decision;ev['interpretation']='Exploratory legacy-test comparison; prior test performance influenced the decision to start follow-up. It cannot re-establish untouched-test generalization.';write(ev,'evaluation.json');pd.concat(allrows,ignore_index=True).to_csv(O/'all_predictions.csv',index=False);print('COMPLETE',json.dumps(ev),flush=True)
