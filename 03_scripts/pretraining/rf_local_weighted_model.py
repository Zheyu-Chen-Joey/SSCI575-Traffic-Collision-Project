"""Geographically weighted RF ensemble; no neighboring observed outcomes at prediction."""
import numpy as np
from sklearn.base import clone
from rf_spatial_model import SpatialCoverageForest
class LocalWeightedSpatialForest(SpatialCoverageForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=20000.,anchor_spacing_m=20000.,local_strength=.5,local_trees=200,min_effective_samples=40,nearest_anchors=3):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position);self.bandwidth_m=bandwidth_m;self.anchor_spacing_m=anchor_spacing_m;self.local_strength=local_strength;self.local_trees=local_trees;self.min_effective_samples=min_effective_samples;self.nearest_anchors=nearest_anchors
 def fit(self,X,y):
  super().fit(X,y);xy=X[['cx','cy']].to_numpy();origin=np.array([345000.,3730000.]);cells=np.unique(np.floor((xy-origin)/self.anchor_spacing_m).astype(int),axis=0);anchors=origin+(cells+.5)*self.anchor_spacing_m;z=self.forests_[0].named_steps['preprocess'].transform(self._X(X));target=np.asarray(y)/self._scale(X);self.local_forests_=[];self.local_anchors_=[];self.local_effective_n_=[];self.training_rows_=len(X)
  for anchor in anchors:
   dist2=np.sum((xy-anchor)**2,axis=1);w=np.exp(-(dist2-dist2.min())/(2*self.bandwidth_m**2));neff=float(w.sum()**2/(w@w))
   if neff<self.min_effective_samples:continue
   w=w/w.mean();rf=clone(self.forests_[0].named_steps['rf']).set_params(n_estimators=self.local_trees,random_state=575,n_jobs=2);rf.fit(z,target,sample_weight=w);self.local_forests_.append(rf);self.local_anchors_.append(anchor);self.local_effective_n_.append(neff)
  self.local_anchors_=np.asarray(self.local_anchors_);return self
 def predict_components(self,X):
  global_prediction=super().predict(X)
  if not self.local_forests_:return global_prediction,global_prediction
  xy=X[['cx','cy']].to_numpy();z=self.forests_[0].named_steps['preprocess'].transform(self._X(X));dist2=np.sum((xy[:,None,:]-self.local_anchors_[None,:,:])**2,axis=2);k=min(self.nearest_anchors,len(self.local_forests_));ix=np.argsort(dist2,axis=1)[:,:k];weights=np.exp(-(np.take_along_axis(dist2,ix,axis=1)-dist2.min(axis=1,keepdims=True))/(2*self.bandwidth_m**2));weights/=weights.sum(axis=1,keepdims=True);pred=np.column_stack([m.predict(z)for m in self.local_forests_]);local=np.sum(np.take_along_axis(pred,ix,axis=1)*weights,axis=1)*self._scale(X);return global_prediction,np.maximum(0,local)
 def predict(self,X):
  g,l=self.predict_components(X);return np.maximum(0,(1-self.local_strength)*g+self.local_strength*l)
