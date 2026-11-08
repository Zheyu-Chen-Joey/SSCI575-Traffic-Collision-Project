"""Export project maps, comparisons and auditable GIS deliverables from the frozen run."""
import sys,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd,numpy as np,geopandas as gpd,shapely,joblib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
O=ROOT/'04_outputs/rf_project_v1';F=O/'figures';F.mkdir(exist_ok=True);M=ROOT/'05_models/rf_project_v1';ev=json.loads((M/'evaluation.json').read_text());sel=json.loads((O/'frozen_selection.json').read_text());preferred=ev['preferred_before_test'];pred=pd.read_csv(O/'all_predictions.csv');df=pd.read_csv(ROOT/'01_data/processed/pretraining_1km/model_table_1000_final.csv');grid=gpd.read_file(ROOT/'01_data/processed/pretraining_1km/grid_1000.gpkg');g=grid[['grid_id','i','j','geometry']].merge(df.drop(columns=['i','j']),on='grid_id',validate='one_to_one');hin=gpd.read_file(ROOT/'01_data/processed/hin_2024_context.gpkg')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
def save(fig,name):fig.savefig(F/(name+'.png'),bbox_inches='tight',facecolor='white');plt.close(fig)
keys=['baseline_initial','baseline_optimized','enhanced_initial','enhanced_optimized'];labels=['Baseline\ninitial','Baseline\ntuned','Enhanced\ninitial','Enhanced\ntuned'];colors=['#b2bfd0','#537aa3','#e9bb9c','#bf6738'];metricrows=[]
for key in keys:
 v,stage=key.split('_');metricrows.append({'model':key,**ev[key]['test'], 'residual_moran_knn8':ev[key]['residual_moran']['8']['I'],'residual_moran_p':ev[key]['residual_moran']['8']['p_two_sided']})
metrics=pd.DataFrame(metricrows);metrics.to_csv(O/'test_metrics.csv',index=False)
fig,axes=plt.subplots(1,3,figsize=(11,3.6))
for ax,col,title in zip(axes,['rmse','mae','r2'],['RMSE in collisions per cell','MAE in collisions per cell','R squared']):
 ax.bar(labels,metrics[col],color=colors);ax.set_title(title);ax.tick_params(axis='x',labelsize=8)
 for i,val in enumerate(metrics[col]):ax.text(i,val,f'{val:.3f}' if col=='r2' else f'{val:.1f}',ha='center',va='bottom',fontsize=9)
fig.suptitle('Final spatial test set | 227 cells | one evaluation batch');fig.tight_layout();save(fig,'01_test_comparison')
fig,axes=plt.subplots(1,2,figsize=(10,4.5))
for ax,v in zip(axes,['baseline','enhanced']):
 p=pred[(pred.variant==v)&(pred.stage=='optimized')&(pred.prediction_role=='heldout_test')];ax.scatter(p.count_2017_2021,p.predicted,s=18,alpha=.7,color='#537aa3'if v=='baseline'else'#bf6738');hi=max(p.count_2017_2021.max(),p.predicted.max());ax.plot([0,hi],[0,hi],color='gray',linestyle='--');ax.set(xlabel='Observed five-year collisions',ylabel='Predicted collisions',title=v.title()+' tuned RF');ax.text(.04,.95,f"R² = {ev[v+'_optimized']['test']['r2']:.3f}",transform=ax.transAxes,va='top')
fig.tight_layout();save(fig,'02_observed_predicted')
# Wide model output retaining provenance for every row; boundary predictions are extrapolation only.
for key in keys:
 v,stage=key.split('_');p=pred[(pred.variant==v)&(pred.stage==stage)];g=g.merge(p[['grid_id','predicted','residual']].rename(columns={'predicted':key+'_pred','residual':key+'_resid'}),on='grid_id',validate='one_to_one')
g['prediction_role']=np.where(~g.eligible,'boundary_extrapolation_not_evaluated',np.where(g.split=='test','heldout_test','development_in_sample'));g['selected_pred']=g[preferred+'_optimized_pred'];g['selected_resid']=g[preferred+'_optimized_resid'];e=g[g.eligible];t=e[e.split=='test'];maximum=max(t.count_2017_2021.max(),t.selected_pred.max());fig,axes=plt.subplots(1,3,figsize=(10,8));rr=max(abs(t.selected_resid.min()),abs(t.selected_resid.max()))
for ax in axes:g.plot(ax=ax,color='#e8e8e8',edgecolor='white',linewidth=.07);ax.set_axis_off()
t.plot(column='count_2017_2021',ax=axes[0],cmap='YlOrRd',vmin=0,vmax=maximum,legend=True,legend_kwds={'shrink':.35});t.plot(column='selected_pred',ax=axes[1],cmap='YlOrRd',vmin=0,vmax=maximum,legend=True,legend_kwds={'shrink':.35});t.plot(column='selected_resid',ax=axes[2],cmap='RdBu_r',norm=TwoSlopeNorm(vmin=-rr,vcenter=0,vmax=rr),legend=True,legend_kwds={'shrink':.35})
for ax,title in zip(axes,['Observed test count','Selected RF test prediction','Residual observed minus predicted']):ax.set_title(title,fontsize=10)
fig.suptitle('Held-out spatial test cells only | gray cells are not evaluated here');save(fig,'03_test_maps')
fig,axes=plt.subplots(1,2,figsize=(12,5.5))
for ax,v in zip(axes,['baseline','enhanced']):
 im=pd.read_csv(O/f'{v}_validation_permutation_importance.csv').head(10).iloc[::-1];names=im.feature.str.replace('landuse_share_','Land use: ',regex=False).str.replace('_',' ',regex=False);ax.barh(names,im.delta_rmse_mean,xerr=im.delta_rmse_std,color='#537aa3'if v=='baseline'else'#bf6738');ax.axvline(0,color='gray',linewidth=.8);ax.set(title=v.title()+' tuned RF',xlabel='Validation RMSE increase after permutation')
fig.suptitle('Exploratory validation importance | 20 permutations | correlated inputs can share contribution');fig.tight_layout();save(fig,'04_validation_importance')
cv=pd.read_csv(O/'cv_fold_scores.csv');fig,ax=plt.subplots(figsize=(9,4));
for v,color in [('baseline','#537aa3'),('enhanced','#bf6738')]:
 a=cv[cv.variant==v].groupby('candidate').rmse.agg(['mean','std']);ax.errorbar(a.index,a['mean'],yerr=a['std']/np.sqrt(5),fmt='o',color=color,label=v,capsize=2,markersize=4)
ax.set(xlabel='Predeclared candidate index (0 = initial settings)',ylabel='Mean training spatial-CV RMSE',title='Optimization uses training cells only; error bars are fold SE');ax.legend();fig.tight_layout();save(fig,'05_training_cv')
sen=pd.read_csv(O/'development_sensitivity.csv');sen['label']=sen['check']+' '+sen.seed.astype(str);pivot=sen.pivot(index='label',columns='variant',values='rmse');fig,ax=plt.subplots(figsize=(10,4.5));pivot.plot.barh(ax=ax,color=['#537aa3','#bf6738']);ax.set(xlabel='Development evaluation RMSE',ylabel='',title='Split, buffer and RF-seed sensitivity | external test cells excluded');fig.tight_layout();save(fig,'06_development_sensitivity')
# HIN contextual overlay; exact boundary attribution is consistent with existing roads.
parts=gpd.overlay(g[['grid_id','i','j','geometry']],hin[['geometry']],how='intersection',keep_geom_type=False).explode(ignore_index=True);parts=parts[parts.geom_type=='LineString'].copy();mid=parts.geometry.interpolate(.5,normalized=True);ij=np.floor((np.c_[mid.x,mid.y]-[345000,3730000])/1000).astype(int);parts=parts[(parts.i.to_numpy()==ij[:,0])&(parts.j.to_numpy()==ij[:,1])];parts['length']=parts.length;agg=parts.groupby('grid_id').length.sum();g['hin_length_m']=g.grid_id.map(agg).fillna(0);assert abs(g.hin_length_m.sum()-hin.length.sum())<.1;e=g[g.eligible];t=e[e.split=='test'];n=int(np.ceil(len(t)*.1));high=t.nlargest(n,'selected_pred');context={'source':'00_admin/hin_manifest.json','role':'non-independent context, NOT a model input or performance ground truth','test_top_predicted_cells':n,'fraction_high_predicted_test_cells_with_any_HIN':float((high.hin_length_m>0).mean()),'fraction_all_test_cells_with_any_HIN':float((t.hin_length_m>0).mean()),'hin_length_conserved_m':float(g.hin_length_m.sum()),'warning':'HIN targets severe-injury corridors; model targets all recorded collisions. Any-HIN in1km cell is coarse coincidence.'};(O/'hin_context.json').write_text(json.dumps(context,indent=2))
fig,axes=plt.subplots(1,2,figsize=(10,8));e.plot(column='count_2017_2021',cmap='YlOrRd',ax=axes[0],legend=True,legend_kwds={'shrink':.35});e.plot(ax=axes[1],color='#e8e8e8',edgecolor='white',linewidth=.1);high.plot(ax=axes[1],color='#f2b134');hin.plot(ax=axes[1],color='#a00000',linewidth=.55)
axes[0].set_title('Observed burden | all eligible cells');axes[1].set_title('Top predicted test cells and official HIN2024');
for ax in axes:ax.set_axis_off()
fig.suptitle('Contextual overlap only | HIN is not independent ground truth');save(fig,'07_HIN_context')
fig,ax=plt.subplots(figsize=(7,3.7));counts=[int(df[f'count_{y}'].sum())for y in range(2017,2022)];ax.bar([str(y)for y in range(2017,2022)],counts,color=['#537aa3']*4+['#bf6738']);ax.set(title='Cleaned published collision records by year',ylabel='Records in city boundary');
for i,c in enumerate(counts):ax.text(i,c,f'{c:,}',ha='center',va='bottom')
fig.tight_layout();save(fig,'08_annual_records')
g.to_file(O/'grid_predictions_1000.gpkg',layer='grid_predictions',driver='GPKG');hin.to_file(O/'grid_predictions_1000.gpkg',layer='hin2024_context',driver='GPKG');g.to_crs(4326).to_file(O/'grid_predictions_1000.geojson',driver='GeoJSON');g.drop(columns='geometry').to_csv(O/'grid_predictions_1000.csv',index=False)
print('FIGURES',len(list(F.glob('*.png'))),'GIS rows',len(g),'preferred',preferred)
