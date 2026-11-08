"""Refined local RF with optional geometry-only support attenuation."""
import numpy as np
from sklearn.base import clone
from scipy.spatial import cKDTree
from rf_spatial_model import SpatialCoverageForest
from rf_local_weighted_model import LocalWeightedSpatialForest
class RefinedLocalSpatialForest(LocalWeightedSpatialForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,local_leaf=5,local_depth=16,local_features=.5,support_attenuation=False,support_start_m=5000.,support_decay_m=5000.):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors);self.local_leaf=local_leaf;self.local_depth=local_depth;self.local_features=local_features;self.support_attenuation=support_attenuation;self.support_start_m=support_start_m;self.support_decay_m=support_decay_m
 def fit(self,X,y):
  SpatialCoverageForest.fit(self,X,y);return self._fit_locals(X,y)
 def fit_with_global(self,X,y,global_model):
  assert len(X)==int(global_model.forests_[0].named_steps['rf'].estimators_[0].tree_.weighted_n_node_samples[0]);self.forests_=global_model.forests_;self.factor_medians_=dict(global_model.factor_medians_);self.feature_names_in_=global_model.feature_names_in_.copy();return self._fit_locals(X,y)
 def _fit_locals(self,X,y):
  xy=X[['cx','cy']].to_numpy();self.training_xy_=xy.copy();self.training_rows_=len(X);origin=np.array([345000.,3730000.]);cells=np.unique(np.floor((xy-origin)/self.anchor_spacing_m).astype(int),axis=0);anchors=origin+(cells+.5)*self.anchor_spacing_m;z=self.forests_[0].named_steps['preprocess'].transform(self._X(X));target=np.asarray(y)/self._scale(X);self.local_forests_=[];self.local_anchors_=[];self.local_effective_n_=[]
  for anchor in anchors:
   d2=((xy-anchor)**2).sum(axis=1);w=np.exp(-(d2-d2.min())/(2*self.bandwidth_m**2));neff=float(w.sum()**2/(w@w))
   if neff<self.min_effective_samples:continue
   w/=w.mean();rf=clone(self.forests_[0].named_steps['rf']).set_params(n_estimators=self.local_trees,random_state=575,n_jobs=2,min_samples_leaf=self.local_leaf,max_depth=self.local_depth,max_features=self.local_features);rf.fit(z,target,sample_weight=w);self.local_forests_.append(rf);self.local_anchors_.append(anchor);self.local_effective_n_.append(neff)
  self.local_anchors_=np.asarray(self.local_anchors_);return self
 def support_factor(self,X):
  if not self.support_attenuation:return np.ones(len(X))
  distance=cKDTree(self.training_xy_).query(X[['cx','cy']].to_numpy())[0];outside=np.maximum(distance-self.support_start_m,0);return np.exp(-(outside/self.support_decay_m)**2)
 def predict(self,X):
  g,l=self.predict_components(X);s=self.local_strength*self.support_factor(X);return np.maximum(0,g+s*(l-g))
