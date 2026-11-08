"""Define unfitted RF pipelines. Importing this module never reads targets or calls fit."""
import sys,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold

LANDUSE=['landuse_share_residential','landuse_share_commercial','landuse_share_industrial','landuse_share_open_space_public_facilities','landuse_share_lax_airport','landuse_share_port_of_la','landuse_share_parking']
BASE_NUM=['road_density_km_per_km2','intersection_density_km2','population_density_km2',*LANDUSE,'landuse_uncovered_fraction']
DESIGN=json.loads((ROOT/'02_config/feature_design.json').read_text())
if DESIGN['include_traffic_volume']:BASE_NUM=['traffic_volume_2017_2021',*BASE_NUM]
BASE_CAT=['road_type_dominant']
EXTRA_NUM=['road_sinuosity_length_weighted','freeway_share_functional','arterial_share_functional','signal_density_snapshot_km2']

def feature_names(variant='baseline'):
 if variant not in ['baseline','enhanced']:raise ValueError('variant must be baseline or enhanced')
 return BASE_NUM+(EXTRA_NUM if variant=='enhanced' else [])+BASE_CAT

def make_pipeline(variant='baseline'):
 numeric=BASE_NUM+(EXTRA_NUM if variant=='enhanced' else [])
 pre=ColumnTransformer([('numeric',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True))]),numeric),('categorical',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),BASE_CAT)],remainder='drop')
 return Pipeline([('preprocess',pre),('rf',RandomForestRegressor(n_estimators=300,max_depth=12,min_samples_split=10,min_samples_leaf=5,max_features='sqrt',bootstrap=True,oob_score=False,random_state=42,n_jobs=-1))])

def training_cv():
 # Apply to training rows only, using block_id as groups. The holdout remains untouched.
 return GroupKFold(n_splits=5)

PARAM_GRID={'rf__n_estimators':[300,500],'rf__max_depth':[8,12],'rf__min_samples_leaf':[5,10]}
# Future fitting must put the complete pipeline inside group CV. Never fit imputers on full data.

