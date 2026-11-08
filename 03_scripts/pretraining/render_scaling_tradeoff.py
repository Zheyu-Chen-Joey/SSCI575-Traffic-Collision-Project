"""Render the rejected scaling candidate comparison from frozen predictions."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'.runtime'))
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=R/'04_outputs/rf_spatial_v5/scaling_blend_v8';result=json.loads((P/'evaluation.json').read_text());x=pd.read_csv(P/'per_grid_tradeoff.csv');before=result['before'];after=result['after'];keys=['rmse','mae','p90_abs_error'];old=[before[k]for k in keys];new=[after[k]for k in keys];positions=np.arange(3)
fig,axes=plt.subplots(1,2,figsize=(11,4.6));axes[0].bar(positions-.18,old,.36,label='Retained model',color='#537aa3');axes[0].bar(positions+.18,new,.36,label='Rejected candidate',color='#bf6738');axes[0].set_xticks(positions,['RMSE','MAE','90th percentile']);axes[0].set_ylabel('Collisions per cell | lower is better');axes[0].set_ylim(0,max(old+new)*1.18);axes[0].legend(fontsize=8)
for offset,values in [(-.18,old),(.18,new)]:
 for index,value in enumerate(values):axes[0].text(index+offset,value,f'{value:.2f}',ha='center',va='bottom',fontsize=8)
for column,label,color in [('before_abs_error','Retained model','#537aa3'),('candidate_abs_error','Rejected candidate','#bf6738')]:
 values=np.sort(x[column]);axes[1].step(values,np.arange(1,len(values)+1)/len(values),where='post',label=label,color=color)
axes[1].axhline(.9,color='gray',linestyle='--',linewidth=.8);axes[1].set_xlabel('Absolute error per cell');axes[1].set_ylabel('Fraction of 227 cells');axes[1].legend(fontsize=8);axes[1].grid(alpha=.2);fig.suptitle('Exploratory reused region | lower average error but worse 90th percentile',fontsize=11);fig.tight_layout();fig.savefig(P/'error_tradeoff.png',dpi=180,bbox_inches='tight');plt.close(fig)
