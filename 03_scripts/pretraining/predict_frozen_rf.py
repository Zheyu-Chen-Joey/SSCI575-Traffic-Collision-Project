"""Predict with the frozen selected RF using already aggregated1km features; no fitting."""
import sys,pathlib,argparse,json
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd,numpy as np,joblib
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();m=ROOT/'05_models/rf_project_v1';s=json.loads((ROOT/'04_outputs/rf_project_v1/frozen_selection.json').read_text());v=s['preferred_variant_by_validation'];cols=s[v]['features'];df=pd.read_csv(a.input);missing=set(cols)-set(df)
if missing:raise ValueError('Required aggregated features missing: '+','.join(sorted(missing)))
if pathlib.Path(a.output).exists():raise FileExistsError('Choose a new output path; existing files are not overwritten')
model=joblib.load(m/f'{v}_optimized_rf.joblib');p=model.predict(df[cols]);assert np.isfinite(p).all()and(p>=0).all();out=pd.DataFrame({'predicted_recorded_collisions_2017_2021':p});
if 'grid_id'in df:out.insert(0,'grid_id',df.grid_id)
out.to_csv(a.output,index=False);print('Predicted',len(out),'rows. This model estimates historical recorded burden; it does not forecast future years.')
