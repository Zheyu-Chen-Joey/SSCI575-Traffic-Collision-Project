"""Offline count prediction for the v4b exploratory RF candidate; never fits."""
import sys,pathlib,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'));sys.path.insert(0,str(ROOT/'03_scripts/pretraining'))
import joblib,pandas as pd
from rf_fixed_blend import FixedForestBlend
from rf_coverage_scaled_model import CoverageScaledForest
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args();dest=pathlib.Path(a.output)
if dest.exists():raise FileExistsError('Choose a new output path')
df=pd.read_csv(a.input);m=joblib.load(ROOT/'05_models/rf_stability_blend_v4b/blend_frozen.joblib');missing=set(m.feature_names)-set(df)
if missing:raise ValueError('Missing fields '+','.join(sorted(missing)))
out=pd.DataFrame({'predicted_2017_2021_recorded_count':m.predict(df)});
if 'grid_id'in df:out.insert(0,'grid_id',df.grid_id)
out.to_csv(dest,index=False);print('Predicted',len(out),'rows; exploratory historical-count model')
