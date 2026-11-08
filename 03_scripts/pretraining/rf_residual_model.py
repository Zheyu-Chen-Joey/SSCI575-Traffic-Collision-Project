"""Random-forest-only residual correction with nested spatial cross-fitting."""
import numpy as np
from sklearn.base import BaseEstimator,RegressorMixin
from sklearn.model_selection import GroupKFold
from pipeline_definition import make_pipeline
class CrossFittedResidualForest(RegressorMixin,BaseEstimator):
 def __init__(self,base_params=None,correction_params=None,strength=.5,inner_splits=3):
  self.base_params=base_params;self.correction_params=correction_params;self.strength=strength;self.inner_splits=inner_splits
 def _base(self):return make_pipeline('enhanced').set_params(rf__n_jobs=4,**(self.base_params or {}))
 def _correction(self):return make_pipeline('enhanced').set_params(rf__n_jobs=4,rf__n_estimators=300,rf__criterion='squared_error',**(self.correction_params or {}))
 def fit(self,X,y,groups):
  y=np.asarray(y);oof=np.zeros(len(y));coverage=np.zeros(len(y),dtype=int);self.crossfit_splits_=[]
  for a,b in GroupKFold(self.inner_splits).split(X,groups=groups):
   assert not(set(np.asarray(groups)[a])&set(np.asarray(groups)[b]));m=self._base();m.fit(X.iloc[a],y[a]);oof[b]=m.predict(X.iloc[b]);coverage[b]+=1;self.crossfit_splits_.append((a,b))
  assert np.all(coverage==1);self.oof_base_prediction_=oof;self.base_=self._base().fit(X,y);self.correction_=self._correction().fit(X,y-oof);self.feature_names_in_=np.array(X.columns);return self
 def predict(self,X):return np.maximum(0,self.base_.predict(X)+self.strength*self.correction_.predict(X))
