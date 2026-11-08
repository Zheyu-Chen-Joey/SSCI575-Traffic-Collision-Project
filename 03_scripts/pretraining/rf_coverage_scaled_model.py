"""RF covariate-scaled count prediction; no vehicle-exposure interpretation."""
import numpy as np
from sklearn.base import BaseEstimator,RegressorMixin
from pipeline_definition import make_pipeline,LANDUSE
class CoverageScaledForest(RegressorMixin,BaseEstimator):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,)):
  self.landuse_mode=landuse_mode;self.scale_mode=scale_mode;self.rf_params=rf_params;self.seeds=seeds
 def _X(self,X):
  z=X.copy();cov=(1-z.landuse_uncovered_fraction).clip(0,1)
  if self.landuse_mode!='raw':
   z[LANDUSE]=z[LANDUSE].div(cov.replace(0,np.nan),axis=0)
   if self.landuse_mode in ['mask50','mask80']:z.loc[cov <(.5 if self.landuse_mode=='mask50'else .8),LANDUSE]=np.nan
  return z
 def _scale(self,X):
  if self.scale_mode=='none':return np.ones(len(X))
  field,power,unit={'road_sqrt':('road_density_km_per_km2',.5,1),'road':('road_density_km_per_km2',1,1),'signal_sqrt':('signal_density_snapshot_km2',.5,1),'signal':('signal_density_snapshot_km2',1,1),'population_quarter':('population_density_km2',.25,1000),'population_sqrt':('population_density_km2',.5,1000)}[self.scale_mode]
  values=X[field].fillna(self.factor_medians_[field]).clip(lower=0).to_numpy();return (1+values/unit)**power
 def fit(self,X,y):
  self.factor_medians_={c:float(X[c].median())for c in ['road_density_km_per_km2','signal_density_snapshot_km2','population_density_km2']};z=self._X(X);self.forests_=[];target=np.asarray(y)/self._scale(X)
  for seed in self.seeds:
   m=make_pipeline('enhanced').set_params(rf__n_jobs=4,rf__random_state=seed,**(self.rf_params or {}));m.fit(z,target);self.forests_.append(m)
  self.feature_names_in_=np.array(X.columns);return self
 def predict(self,X):return np.maximum(0,np.mean([m.predict(self._X(X))for m in self.forests_],axis=0)*self._scale(X))
