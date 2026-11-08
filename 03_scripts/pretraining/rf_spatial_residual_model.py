"""RF spatial residual trend; base model has original covariates, correction uses location only."""
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.ensemble import RandomForestRegressor
from rf_residual_model import CrossFittedResidualForest

def position_array(X):
 a=X[['cx','cy']].to_numpy()
 if not np.isfinite(a).all():raise ValueError('EPSG26911 grid centers required')
 return (a-np.array([345000.,3730000.]))/1000
class SpatialResidualForest(CrossFittedResidualForest):
 def _correction(self):
  p=Pipeline([('position',FunctionTransformer(position_array)),('rf',RandomForestRegressor(n_estimators=300,random_state=575,n_jobs=2,min_samples_split=10))])
  return p.set_params(**(self.correction_params or {}))
