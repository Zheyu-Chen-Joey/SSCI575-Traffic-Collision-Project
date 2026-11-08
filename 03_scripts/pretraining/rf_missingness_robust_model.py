"""RF training-only missingness simulation; original input snapshots are untouched."""
import numpy as np
from rf_orientation_ensemble import OrientationEnsembleForest
from pipeline_definition import LANDUSE

class MissingnessRobustForest(OrientationEnsembleForest):
 def __init__(self,landuse_mode='raw',scale_mode='none',rf_params=None,seeds=(42,),include_position=True,bandwidth_m=10000.,anchor_spacing_m=20000.,local_strength=.75,local_trees=200,min_effective_samples=40,nearest_anchors=3,orientation_angles=(0.,45.,60.),orientation_weights=(.25,.25,.5),landuse_dropout=0.,mask_seed=575):
  super().__init__(landuse_mode,scale_mode,rf_params,seeds,include_position,bandwidth_m,anchor_spacing_m,local_strength,local_trees,min_effective_samples,nearest_anchors,orientation_angles,orientation_weights)
  self.landuse_dropout=landuse_dropout;self.mask_seed=mask_seed
 def fit(self,X,y):
  if not 0<=self.landuse_dropout<1:raise ValueError('Dropout probability outside [0,1)')
  augmented=X.copy(deep=True);rng=np.random.default_rng(self.mask_seed);n=int(round(len(X)*self.landuse_dropout));mask=rng.choice(len(X),n,replace=False);augmented.iloc[mask,augmented.columns.get_indexer(LANDUSE)]=np.nan;augmented.iloc[mask,augmented.columns.get_loc('landuse_uncovered_fraction')]=1.
  kwargs={k:v for k,v in self.get_params(deep=False).items()if k not in ['landuse_dropout','mask_seed']};base=OrientationEnsembleForest(**kwargs).fit(augmented,y);self.__dict__.update(base.__dict__);self.augmentation_mask_xy_=X.iloc[mask][['cx','cy']].to_numpy();self.augmentation_row_count_=n
  return self
