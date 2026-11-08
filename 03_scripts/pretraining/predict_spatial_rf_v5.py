"""Offline spatial RF inference for known EPSG26911 centers on the fixed1km LA grid."""
import sys,pathlib,argparse,json
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import pandas as pd,numpy as np,joblib
from rf_spatial_model import SpatialCoverageForest
from rf_coverage_scaled_model import CoverageScaledForest
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=pathlib.Path(a.output)
if out.exists():raise FileExistsError('Choose a new output path')
contract=json.loads((ROOT/'05_models/rf_spatial_v5/input_contract.json').read_text());df=pd.read_csv(a.input);missing=set(contract['features'])-set(df)
if missing:raise ValueError('Missing aggregated columns: '+','.join(sorted(missing)))
for c,origin in [('cx',345500),('cy',3730500)]:
 z=pd.to_numeric(df[c],errors='raise').to_numpy();idx=(z-origin)/1000
 if not np.isfinite(z).all()or not np.allclose(idx,np.round(idx),atol=1e-7,rtol=0):raise ValueError('Coordinates must be EPSG26911 fixed1km grid centers, not longitude/latitude')
m=joblib.load(ROOT/'05_models/rf_spatial_v5/spatial_frozen_rf.joblib');pred=m.predict(df[contract['features']]);assert np.isfinite(pred).all()and(pred>=0).all();result=pd.DataFrame({'predicted_recorded_collisions_2017_2021':pred});
if 'grid_id'in df:result.insert(0,'grid_id',df.grid_id)
result.to_csv(out,index=False);print('Predicted',len(result),'rows; position-augmented historical-count candidate, not a future crash forecast')
