"""Fixed rotation of authorized position features; original grid remains unchanged."""
import numpy as np
from rf_local_weighted_model import LocalWeightedSpatialForest

class RotatedLocalSpatialForest(LocalWeightedSpatialForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,rotation_degrees=0.):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors)
  self.rotation_degrees=rotation_degrees
 def _X(self,X):
  z=super()._X(X)
  if self.include_position:
   theta=np.deg2rad(self.rotation_degrees);east=z.position_east_km.copy();north=z.position_north_km.copy()
   z['position_east_km']=east*np.cos(theta)-north*np.sin(theta)
   z['position_north_km']=east*np.sin(theta)+north*np.cos(theta)
  return z
