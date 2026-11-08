"""Fixed convex blend of trained RF members, with no fitted second algorithm."""
import numpy as np
class FixedForestBlend:
 def __init__(self,members,weights,feature_names):self.members=members;self.weights=weights;self.feature_names=feature_names
 def predict(self,X):return np.maximum(0,sum(w*m.predict(X[self.feature_names])for w,m in zip(self.weights,self.members)if w>0))
