"""Convex RF ensemble over fixed coordinate representations, no grid rotation."""
import numpy as np
from rf_local_weighted_model import LocalWeightedSpatialForest
from rf_rotated_local_model import RotatedLocalSpatialForest

class OrientationEnsembleForest(LocalWeightedSpatialForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,orientation_angles=(0.,60.,75.),orientation_weights=(.5,.25,.25)):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors)
  self.orientation_angles=orientation_angles;self.orientation_weights=orientation_weights
 def fit(self,X,y):
  angles=np.asarray(self.orientation_angles);weights=np.asarray(self.orientation_weights)
  if len(angles)!=len(weights)or angles[0]!=0 or(weights<0).any()or not np.isclose(weights.sum(),1):raise ValueError('First direction must be zero and weights must form a convex combination')
  super().fit(X,y);kw={k:v for k,v in self.get_params(deep=False).items()if k not in ['orientation_angles','orientation_weights']}
  self.orientation_models_=[RotatedLocalSpatialForest(**kw,rotation_degrees=float(angle)).fit(X,y)for angle in angles[1:]]
  return self
 def predict(self,X):
  predictions=[super().predict(X)]+[m.predict(X)for m in self.orientation_models_]
  return np.maximum(0,np.sum(np.array(predictions)*np.array(self.orientation_weights)[:,None],axis=0))
