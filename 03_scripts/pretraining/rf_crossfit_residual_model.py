"""Signed RF correction trained on nested OOF residuals, not neighboring observed outcomes."""
import numpy as np
from scipy.spatial import ConvexHull
from sklearn.model_selection import GroupKFold
from rf_orientation_ensemble import OrientationEnsembleForest
from rf_spatial_model import SpatialCoverageForest
from rf_cluster_weighted_model import BASE_KEYS,polygon_gap_keep
from rf_supported_cluster_model import SupportedClusterForest

def full_oof_residuals(X,y,params):
 xy=X[['cx','cy']].to_numpy();ij=np.floor((xy-np.array([345000,3730000]))/5000).astype(int);groups=np.array([f'{i}_{j}'for i,j in ij]);pred=np.full(len(X),np.nan);records=[]
 for fold,(fit,ev)in enumerate(GroupKFold(3).split(X,y,groups)):
  fit=fit[polygon_gap_keep(xy[fit],xy[ev])];assert len(fit)>40 and set(groups[fit]).isdisjoint(groups[ev]);m=OrientationEnsembleForest(**params).fit(X.iloc[fit],np.asarray(y)[fit]);pred[ev]=m.predict(X.iloc[ev]);records.append({'fold':fold,'fit_rows':len(fit),'eval_rows':len(ev),'fit_xy':xy[fit].tolist(),'eval_xy':xy[ev].tolist()})
 assert np.isfinite(pred).all();return np.asarray(y)-pred,pred,records

class SignedResidualForest(SpatialCoverageForest):
 def predict(self,X):return np.mean([m.predict(self._X(X))for m in self.forests_],axis=0)

class CrossFitResidualForest(OrientationEnsembleForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,orientation_angles=(0.,45.,60.),orientation_weights=(.25,.25,.5),residual_depth=4,residual_leaf=20,correction_strength=.25,correction_cap=200.,support_taper_m=2000.,max_support_distance_m=5000.,support_distance_start_m=2000.):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors,orientation_angles,orientation_weights);self.residual_depth=residual_depth;self.residual_leaf=residual_leaf;self.correction_strength=correction_strength;self.correction_cap=correction_cap;self.support_taper_m=support_taper_m;self.max_support_distance_m=max_support_distance_m;self.support_distance_start_m=support_distance_start_m
 def base_parameters(self):return {k:getattr(self,k)for k in BASE_KEYS+['orientation_angles','orientation_weights']}
 def fit(self,X,y):
  params=self.base_parameters();r,p,folds=full_oof_residuals(X,y,params);base=OrientationEnsembleForest(**params).fit(X,y);self.__dict__.update(base.__dict__);self.residual_model_=SignedResidualForest(landuse_mode=self.landuse_mode,scale_mode='none',include_position=True,seeds=(575,),rf_params={'rf__n_estimators':400,'rf__max_depth':self.residual_depth,'rf__min_samples_leaf':self.residual_leaf,'rf__min_samples_split':2*self.residual_leaf,'rf__max_features':.7}).fit(X,r);self.training_support_xy_=X[['cx','cy']].to_numpy();self.support_equations_=ConvexHull(self.training_support_xy_).equations.copy();self.residual_inner_folds_=folds;return self
 def support_gate(self,X):return SupportedClusterForest.support_gate(self,X)
 def predict(self,X):
  primary=OrientationEnsembleForest.predict(self,X);gate=self.support_gate(X)*self.correction_strength
  if not np.any(gate):return primary
  residual=np.clip(self.residual_model_.predict(X),-self.correction_cap,self.correction_cap);return np.maximum(0,primary+gate*residual)
