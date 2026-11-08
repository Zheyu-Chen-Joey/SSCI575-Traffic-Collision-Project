"""Fixed geographic transfer diagnostics for selected local RF; no selection or model saving."""
import sys,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import numpy as np,pandas as pd
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from scipy.spatial import cKDTree
from rf_spatial_model import SpatialCoverageForest
from rf_local_weighted_model import LocalWeightedSpatialForest
P=ROOT/'04_outputs/rf_spatial_v5';M=ROOT/'05_models/rf_spatial_v5';d=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');tr=d[d.eligible&(d.split=='train')];va=d[d.eligible&(d.split=='validation')];dev=pd.concat([tr,va],ignore_index=True);dec=json.loads((P/'frozen_decision.json').read_text());cols=json.loads((M/'input_contract.json').read_text())['features'];rows=[]
for area,col in [('north20pct','cy'),('east20pct','cx')]:
 cut=float(dev[col].quantile(.8));b=np.flatnonzero(dev[col].to_numpy()>=cut);a=np.flatnonzero(dev[col].to_numpy()<cut);dx=np.maximum(abs(dev.iloc[a].cx.to_numpy()[:,None]-dev.iloc[b].cx.to_numpy()[None,:])-1000,0);dy=np.maximum(abs(dev.iloc[a].cy.to_numpy()[:,None]-dev.iloc[b].cy.to_numpy()[None,:])-1000,0);a=a[np.sqrt(dx*dx+dy*dy).min(axis=1)>1000]
 for label,cls,extra in [('previous_spatial',SpatialCoverageForest,{}),('local_weighted',LocalWeightedSpatialForest,dec['local_weighting_settings'])]:
  m=cls(**dec['settings'],seeds=(7,42,99),**extra).fit(dev.iloc[a][cols],dev.iloc[a].count_2017_2021);p=m.predict(dev.iloc[b][cols]);y=dev.iloc[b].count_2017_2021.to_numpy();r=y-p;z=r-r.mean();nn=cKDTree(dev.iloc[b][['cx','cy']]).query(dev.iloc[b][['cx','cy']],k=9)[1][:,1:];I=float((z[:,None]*z[nn]).sum()/8/(z@z));rows.append({'region':area,'model':label,'n_fit':len(a),'n_eval':len(b),'rmse':float(np.sqrt(mean_squared_error(y,p))),'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'moran_i':I})
pd.DataFrame(rows).to_csv(P/'local_rf_geographic_transfer.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
