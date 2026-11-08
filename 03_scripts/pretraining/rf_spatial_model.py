"""Authorized spatial RF extension; fixed grid centers become metric trend features."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from rf_coverage_scaled_model import CoverageScaledForest
from pipeline_definition import BASE_NUM,EXTRA_NUM,BASE_CAT
class SpatialCoverageForest(CoverageScaledForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds);self.include_position=include_position
 def _X(self,X):
  z=super()._X(X)
  if self.include_position:
   z['position_east_km']=(z.cx-345000)/1000;z['position_north_km']=(z.cy-3730000)/1000
  return z.drop(columns=['cx','cy'],errors='ignore')
 def fit(self,X,y):
  if self.include_position and (X[['cx','cy']].isna().any().any()or not np.isfinite(X[['cx','cy']]).all().all()):raise ValueError('Known EPSG26911 grid centers required')
  self.factor_medians_={c:float(X[c].median())for c in ['road_density_km_per_km2','signal_density_snapshot_km2','population_density_km2']};z=self._X(X);target=np.asarray(y)/self._scale(X);self.forests_=[];numeric=BASE_NUM+EXTRA_NUM+(['position_east_km','position_north_km']if self.include_position else [])
  for seed in self.seeds:
   pre=ColumnTransformer([('numeric',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),numeric),('categorical',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),BASE_CAT)],remainder='drop')
   rf=RandomForestRegressor(n_estimators=300,max_depth=12,min_samples_split=10,min_samples_leaf=5,max_features='sqrt',bootstrap=True,random_state=seed,n_jobs=4);p=Pipeline([('preprocess',pre),('rf',rf)]).set_params(**(self.rf_params or {}));p.fit(z,target);self.forests_.append(p)
  self.feature_names_in_=np.array(X.columns);return self
