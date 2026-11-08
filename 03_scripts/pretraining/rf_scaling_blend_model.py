"""Convex RF combination across two statistical covariate normalizations."""
import numpy as np
from rf_orientation_ensemble import OrientationEnsembleForest

class ScalingBlendForest(OrientationEnsembleForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,orientation_angles=(0.,45.,60.),orientation_weights=(.25,.25,.5),secondary_scale_mode='signal_065',secondary_weight=.25):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors,orientation_angles,orientation_weights)
  self.secondary_scale_mode=secondary_scale_mode;self.secondary_weight=secondary_weight
 def fit(self,X,y):
  params={k:v for k,v in self.get_params(deep=False).items()if k not in ['secondary_scale_mode','secondary_weight']};base=OrientationEnsembleForest(**params).fit(X,y);self.__dict__.update(base.__dict__);params['scale_mode']=self.secondary_scale_mode;self.secondary_model_=OrientationEnsembleForest(**params).fit(X,y);return self
 def predict(self,X):
  if not 0<=self.secondary_weight<=1:raise ValueError('Convex weight required')
  primary=super().predict(X)
  if self.secondary_weight==0:return primary
  return np.maximum(0,(1-self.secondary_weight)*primary+self.secondary_weight*self.secondary_model_.predict(X))
