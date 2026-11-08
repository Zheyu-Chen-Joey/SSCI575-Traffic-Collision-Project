"""Training-OOF residual cluster diagnostics; never uses legacy or validation targets."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'.runtime'))
import numpy as np,pandas as pd,geopandas as gpd
from scipy.spatial import cKDTree
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Patch
O=R/'04_outputs/cluster_targeted_optimization';O.mkdir(exist_ok=True);P=R/'01_data/processed/pretraining_1km';data=pd.read_csv(P/'model_table_1000_final.csv');pred=pd.read_csv(R/'04_outputs/rf_spatial_v5/orientation_optimization/orientation_ensemble/oof_predictions.csv')[['grid_id','8']].rename(columns={'8':'oof_prediction'});d=data[data.eligible&(data.split=='train')].merge(pred,on='grid_id',validate='one_to_one');assert len(d)==720 and set(d.split)=={'train'};d['residual']=d.count_2017_2021-d.oof_prediction;d['abs_error']=abs(d.residual);d['error_gt200']=d.abs_error>200;xy=d[['cx','cy']].to_numpy();neighbors=cKDTree(xy).query_ball_point(xy,1500);neighbors=[[j for j in near if j!=i]for i,near in enumerate(neighbors)];n=len(d);width=max(map(len,neighbors));ix=np.zeros((n,width),dtype=int);w=np.zeros((n,width))
for i,near in enumerate(neighbors):
 if near:ix[i,:len(near)]=near;w[i,:len(near)]=1/len(near)
z=(d.residual.to_numpy()-d.residual.mean())/d.residual.std(ddof=0);lag=(z[ix]*w).sum(axis=1);stat=z*lag;expected=np.where(w.sum(axis=1)>0,-1/(n-1),0);observed=abs(stat-expected);counts=np.zeros(n,dtype=int);rng=np.random.default_rng(575);perms=9999
for _ in range(perms):
 q=rng.permutation(z);sim=q*(q[ix]*w).sum(axis=1);counts+=abs(sim-expected)>=observed
p=(1+counts)/(perms+1);order=np.argsort(p);adjusted=np.minimum.accumulate((p[order]*n/np.arange(1,n+1))[::-1])[::-1];qvalue=np.empty(n);qvalue[order]=np.clip(adjusted,0,1);d['local_moran_i']=stat;d['permutation_p_two_sided']=p;d['BH_q']=qvalue;d['neighbor_count']=[len(x)for x in neighbors];d['significant_FDR05']=(qvalue<=.05)&(d.neighbor_count>0);labels=np.where(z>=0,np.where(lag>=0,'HH_underprediction','HL_outlier'),np.where(lag<0,'LL_overprediction','LH_outlier'));d['cluster_type']=np.where(d.significant_FDR05,labels,'not_significant');d['connected_cluster_id']='';seen=set();clusters=[]
for i in range(n):
 kind=d.cluster_type.iloc[i]
 if i in seen or kind not in ['HH_underprediction','LL_overprediction']:continue
 todo=[i];component=[];seen.add(i)
 while todo:
  j=todo.pop();component.append(j)
  for k in neighbors[j]:
   if k not in seen and d.cluster_type.iloc[k]==kind:seen.add(k);todo.append(k)
 identifier=f'{kind}_{len(clusters)+1}';d.loc[component,'connected_cluster_id']=identifier;part=d.iloc[component];clusters.append({'cluster_id':identifier,'n_cells':len(part),'grid_ids':';'.join(part.grid_id),'mean_residual':float(part.residual.mean()),'mae':float(part.abs_error.mean()),'max_abs_error':float(part.abs_error.max()),'errors_gt200':int(part.error_gt200.sum()),'mean_landuse_coverage':float(part.landuse_coverage.mean()),'median_population_density':float(part.population_density_km2.median()),'median_road_density':float(part.road_density_km_per_km2.median()),'median_signal_density':float(part.signal_density_snapshot_km2.median())})
d.to_csv(O/'training_oof_cluster_cells.csv',index=False);pd.DataFrame(clusters).to_csv(O/'training_cluster_summary.csv',index=False);meta={'data_scope':'720 training cells only, frozen original fivefold1km-gap OOF predictions for retainedv8','legacy_and_validation_targets_used':False,'adjacency':'existing training grid centers within1500m; 8queen neighbors on1km grid','local_statistic':'standardized residual * row-standardized neighboring residual lag','permutation':'9999 global residual-label permutations; two-sided deviations around permutation-null expected localI -1/(n-1)','multiple_testing':'Benjamini-Hochberg across720 local tests q<=.05','seed':575,'large_error_threshold_collisions':200,'large_error_cells':int(d.error_gt200.sum()),'FDR_significant_cells':int(d.significant_FDR05.sum()),'significant_types':d.cluster_type.value_counts().to_dict(),'connected_HH_LL_components':len(clusters),'source_input_sha256':hashlib.sha256((P/'model_table_1000_final.csv').read_bytes()).hexdigest(),'limitation':'Exploratory diagnostics on repeatedly used development data. Significant association is not a cause; permutation assumes exchangeability under null.'};(O/'cluster_diagnostic_protocol.json').write_text(json.dumps(meta,indent=2))
grid=gpd.read_file(P/'grid_1000.gpkg')[['grid_id','geometry']];g=grid.merge(d,on='grid_id',validate='one_to_one');g.to_file(O/'training_cluster_diagnostics.gpkg',driver='GPKG');fig,axes=plt.subplots(1,3,figsize=(14,7))
for ax in axes:grid.plot(ax=ax,color='#eeeeee');ax.set_axis_off()
limit=float(d.abs_error.max());g.plot(column='residual',ax=axes[0],cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),legend=True,legend_kwds={'shrink':.45});axes[0].set_title('Training OOF residuals\nObserved minus predicted',fontsize=10)
g.plot(ax=axes[1],color='#ddd');g[g.error_gt200&(g.residual>0)].plot(ax=axes[1],color='#c7473b');g[g.error_gt200&(g.residual<0)].plot(ax=axes[1],color='#3875a6');axes[1].set_title('Absolute error >200\nRed = underprediction | blue = overprediction',fontsize=10)
colors={'not_significant':'#d7d7d7','HH_underprediction':'#c7473b','LL_overprediction':'#3875a6','HL_outlier':'#edaf42','LH_outlier':'#44a575'}
for name,color in colors.items():
 part=g[g.cluster_type==name]
 if len(part):part.plot(ax=axes[2],color=color)
axes[2].set_title('Local residual clusters\nBH q <=0.05',fontsize=10);axes[2].legend(handles=[Patch(color=c,label=k)for k,c in colors.items()],fontsize=7,loc='lower left');fig.suptitle('Development training OOF only | no legacy or validation targets used',fontsize=12);fig.tight_layout(rect=[0,0,1,.90]);fig.savefig(O/'training_residual_clusters.png',dpi=180,bbox_inches='tight');plt.close(fig);print(json.dumps(meta,indent=2));print(pd.DataFrame(clusters).sort_values('n_cells',ascending=False).head(8).to_string(index=False))
