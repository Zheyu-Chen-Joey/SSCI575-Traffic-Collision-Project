"""Convex blend of two RF models using original and rotated position features."""
import numpy as np
from rf_local_weighted_model import LocalWeightedSpatialForest
from rf_rotated_local_model import RotatedLocalSpatialForest

class CoordinateBlendForest(LocalWeightedSpatialForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,rotation_degrees=60.,rotated_weight=.5):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors)
  self.rotation_degrees=rotation_degrees;self.rotated_weight=rotated_weight
 def fit(self,X,y):
  super().fit(X,y)
  kw={k:v for k,v in self.get_params(deep=False).items()if k not in ['rotation_degrees','rotated_weight']}
  self.rotation_model_=RotatedLocalSpatialForest(**kw,rotation_degrees=self.rotation_degrees).fit(X,y)
  return self
 def predict(self,X):
  if not 0<=self.rotated_weight<=1:raise ValueError('Convex weight required')
  return np.maximum(0,(1-self.rotated_weight)*super().predict(X)+self.rotated_weight*self.rotation_model_.predict(X))
