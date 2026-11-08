"""Independent data integrity checks, with no preprocessing fit or RF fit."""
import sys,pathlib,json,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd,numpy as np,geopandas as gpd
from scipy.spatial import cKDTree
from pipeline_definition import make_pipeline,feature_names
P=ROOT/'01_data/processed/pretraining_1km';df=pd.read_csv(P/'model_table_1000_final.csv');pts=gpd.read_file(ROOT/'01_data/processed/collisions_2017_2021.gpkg');assert pts.dr_no.is_unique
# Independent nearest-full-square-center assignment checks the half-open grid count output.
_,ind=cKDTree(df[['cx','cy']].to_numpy()).query(np.c_[pts.geometry.x,pts.geometry.y]);counts=np.bincount(ind,minlength=len(df));assert np.array_equal(counts,df.count_2017_2021.to_numpy())
assert (df[[f'count_{y}' for y in range(2017,2022)]].sum(axis=1)==df.count_2017_2021).all();assert df.count_2017_2021.sum()==230536
assert not(df.groupby('block_id').split.nunique()>1).any();assert (df.eligible==(df.city_area_fraction>=.8)).all()
base=json.loads((ROOT/'00_admin/file_manifest.json').read_text());base=base['files'] if isinstance(base,dict) else base;n_checked=0
for row in base:
 f=ROOT/row['file']
 if f.exists():assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'],str(f);n_checked+=1
for v in ['baseline','enhanced']:
 columns=feature_names(v);assert not any(c.startswith('traffic_') for c in columns),'Excluded traffic input leaked into pipeline';assert not any(c.startswith('count_') or c in ['grid_id','split','i','j','block_id','cx','cy','eligible'] for c in columns);pipe=make_pipeline(v);assert not hasattr(pipe.named_steps['rf'],'estimators_');assert not hasattr(pipe.named_steps['preprocess'],'transformers_')
qa={'status':'pass','checks':['point_counts_independent_center_assignment','target_year_sum','unique_event_ids','no_split_block_overlap','eligibility_rule','raw_baseline_hashes_unchanged','no_target_or_split_features','pipelines_remain_unfitted'],'n_old_raw_snapshots_verified':n_checked,'n_grid_rows':len(df),'count_sum':int(df.count_2017_2021.sum()),'model_fit_executed':False};(ROOT/'04_outputs/pretraining/verification.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
