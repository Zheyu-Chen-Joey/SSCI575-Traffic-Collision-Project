"""RF correction attenuated by geometry-only training support; no labels at inference."""
import numpy as np
from scipy.spatial import ConvexHull,cKDTree
from rf_orientation_ensemble import OrientationEnsembleForest
from rf_cluster_weighted_model import ClusterWeightedOrientationForest,BASE_KEYS,training_residual_diagnostics

class SupportedClusterForest(OrientationEnsembleForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,orientation_angles=(0.,45.,60.),orientation_weights=(.25,.25,.5),error_weight_strength=1.,support_taper_m=2000.,correction_strength=1.,max_support_distance_m=None,support_distance_start_m=2000.):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors,orientation_angles,orientation_weights);self.error_weight_strength=error_weight_strength;self.support_taper_m=support_taper_m;self.correction_strength=correction_strength;self.max_support_distance_m=max_support_distance_m;self.support_distance_start_m=support_distance_start_m
 def base_parameters(self):return {k:getattr(self,k)for k in BASE_KEYS+['orientation_angles','orientation_weights']}
 def fit(self,X,y):
  diagnostics=training_residual_diagnostics(X,y,self.base_parameters());return self.fit_with_diagnostics(X,y,diagnostics)
 def fit_with_diagnostics(self,X,y,diagnostics):
  params=self.base_parameters();primary=OrientationEnsembleForest(**params).fit(X,y);self.__dict__.update(primary.__dict__);self.correction_model_=ClusterWeightedOrientationForest(**params,error_weight_strength=self.error_weight_strength,cluster_emphasis=True,weight_global=False).fit_with_diagnostics(X,y,diagnostics);self.training_support_xy_=X[['cx','cy']].to_numpy();self.support_equations_=ConvexHull(self.training_support_xy_).equations.copy();return self
 def support_gate(self,X):
  xy=X[['cx','cy']].to_numpy();a=self.support_equations_[:,:2];b=self.support_equations_[:,2];margin=np.min(-(xy@a.T+b)/np.linalg.norm(a,axis=1),axis=1)
  if self.support_taper_m<0:raise ValueError('Nonnegative taper distance required')
  gate=(margin>=-1e-6).astype(float)if self.support_taper_m==0 else np.clip(margin/self.support_taper_m,0,1)
  if self.max_support_distance_m is not None:
   if self.max_support_distance_m<=self.support_distance_start_m:raise ValueError('Maximum support distance must exceed taper start')
   distance=cKDTree(self.training_support_xy_).query(xy)[0];gate*=np.clip((self.max_support_distance_m-distance)/(self.max_support_distance_m-self.support_distance_start_m),0,1)
  return gate
 def prediction_branches(self,X):return OrientationEnsembleForest.predict(self,X),self.correction_model_.predict(X)
 def predict(self,X):
  if not 0<=self.correction_strength<=1:raise ValueError('Convex correction strength required')
  primary=OrientationEnsembleForest.predict(self,X);gate=self.support_gate(X)*self.correction_strength
  if not np.any(gate):return primary
  correction=self.correction_model_.predict(X);return np.maximum(0,primary+gate*(correction-primary))
