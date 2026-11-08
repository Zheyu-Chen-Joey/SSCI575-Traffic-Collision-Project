"""Nested train-only residual weighting; neighboring outcomes are not prediction features."""
import numpy as np
from sklearn.base import clone
from sklearn.model_selection import GroupKFold
from scipy.spatial import cKDTree
from rf_spatial_model import SpatialCoverageForest
from rf_local_weighted_model import LocalWeightedSpatialForest
from rf_orientation_ensemble import OrientationEnsembleForest

BASE_KEYS=['landuse_mode','scale_mode','rf_params','seeds','include_position','bandwidth_m','anchor_spacing_m','local_strength','local_trees','min_effective_samples','nearest_anchors']
def polygon_gap_keep(a,b):
 dx=np.maximum(abs(a[:,None,0]-b[None,:,0])-1000,0);dy=np.maximum(abs(a[:,None,1]-b[None,:,1])-1000,0);return np.sqrt(dx*dx+dy*dy).min(axis=1)>1000

def training_residual_diagnostics(X,y,params):
 """Each weight detector label is predicted without its own block or <=1km neighbors."""
 xy=X[['cx','cy']].to_numpy();blocks=np.floor((xy-np.array([345000,3730000]))/5000).astype(int);groups=np.array([f'{i}_{j}'for i,j in blocks]);prediction=np.full(len(X),np.nan);fold_records=[]
 light=dict(params);light['rf_params']=dict(light['rf_params']);light['rf_params']['rf__n_estimators']=200;light['local_trees']=100;light['seeds']=(42,)
 for fold,(fit,ev)in enumerate(GroupKFold(3).split(X,y,groups)):
  fit=fit[polygon_gap_keep(xy[fit],xy[ev])];assert len(fit)>40 and set(groups[fit]).isdisjoint(groups[ev]);model=OrientationEnsembleForest(**light).fit(X.iloc[fit],np.asarray(y)[fit]);prediction[ev]=model.predict(X.iloc[ev]);fold_records.append({'fold':fold,'fit_rows':len(fit),'eval_rows':len(ev),'fit_xy':xy[fit].tolist(),'eval_xy':xy[ev].tolist()})
 assert np.isfinite(prediction).all();residual=np.asarray(y)-prediction;hard=np.clip(abs(residual)/max(np.quantile(abs(residual),.9),1),0,2);neighbors=cKDTree(xy).query_ball_point(xy,1500);consistency=np.zeros(len(X))
 for i,near in enumerate(neighbors):
  near=[j for j in near if j!=i]
  if len(near)>=2:consistency[i]=np.mean(np.sign(residual[near])==np.sign(residual[i]))
 return {'oof_prediction':prediction,'residual':residual,'hard_score':hard,'same_sign_neighbor_fraction':consistency,'inner_folds':fold_records}

class WeightedLocalForest(LocalWeightedSpatialForest):
 def fit(self,X,y,sample_weight,weight_global=True):
  w0=np.asarray(sample_weight);assert len(w0)==len(X)and(w0>0).all();SpatialCoverageForest.fit(self,X,y,sample_weight=w0 if weight_global else None);xy=X[['cx','cy']].to_numpy();origin=np.array([345000.,3730000.]);cells=np.unique(np.floor((xy-origin)/self.anchor_spacing_m).astype(int),axis=0);anchors=origin+(cells+.5)*self.anchor_spacing_m;z=self.forests_[0].named_steps['preprocess'].transform(self._X(X));target=np.asarray(y)/self._scale(X);self.local_forests_=[];self.local_anchors_=[];self.local_effective_n_=[];self.training_rows_=len(X)
  for anchor in anchors:
   dist2=((xy-anchor)**2).sum(axis=1);w=np.exp(-(dist2-dist2.min())/(2*self.bandwidth_m**2))*w0;neff=float(w.sum()**2/(w@w))
   if neff<self.min_effective_samples:continue
   w/=w.mean();rf=clone(self.forests_[0].named_steps['rf']).set_params(n_estimators=self.local_trees,random_state=575,n_jobs=2);rf.fit(z,target,sample_weight=w);self.local_forests_.append(rf);self.local_anchors_.append(anchor);self.local_effective_n_.append(neff)
  self.local_anchors_=np.asarray(self.local_anchors_);return self

class WeightedRotatedLocalForest(WeightedLocalForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,rotation_degrees=45.):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors);self.rotation_degrees=rotation_degrees
 def _X(self,X):
  z=super()._X(X)
  if self.include_position:
   t=np.deg2rad(self.rotation_degrees);e=z.position_east_km.copy();n=z.position_north_km.copy();z['position_east_km']=e*np.cos(t)-n*np.sin(t);z['position_north_km']=e*np.sin(t)+n*np.cos(t)
  return z

class ClusterWeightedOrientationForest(OrientationEnsembleForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,orientation_angles=(0.,45.,60.),orientation_weights=(.25,.25,.5),error_weight_strength=.5,cluster_emphasis=True,weight_global=True):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors,orientation_angles,orientation_weights);self.error_weight_strength=error_weight_strength;self.cluster_emphasis=cluster_emphasis;self.weight_global=weight_global
 def fit(self,X,y):
  params={k:v for k,v in self.get_params(deep=False).items()if k not in ['error_weight_strength','cluster_emphasis','weight_global']};diagnostics=training_residual_diagnostics(X,y,params);return self.fit_with_diagnostics(X,y,diagnostics)
 def fit_with_diagnostics(self,X,y,diagnostics):
  h=diagnostics['hard_score'];consistency=diagnostics['same_sign_neighbor_fraction'];multiplier=(.5+.5*consistency)if self.cluster_emphasis else np.ones(len(X));weights=np.minimum(1+self.error_weight_strength*h*multiplier,3);weights/=weights.mean();params={k:getattr(self,k)for k in BASE_KEYS};base=WeightedLocalForest(**params).fit(X,y,weights,weight_global=self.weight_global);self.__dict__.update(base.__dict__);self.orientation_models_=[WeightedRotatedLocalForest(**params,rotation_degrees=float(angle)).fit(X,y,weights,weight_global=self.weight_global)for angle in self.orientation_angles[1:]];self.sample_weights_=weights;self.weight_training_xy_=X[['cx','cy']].to_numpy();self.weight_inner_folds_=diagnostics['inner_folds'];return self
