"""Join audited inputs, publish schema/splits, and expose unresolved readiness gates."""
import sys,pathlib,json,hashlib,datetime,platform
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd,numpy as np,geopandas as gpd,importlib.metadata
from scipy.spatial import cKDTree
P=ROOT/'01_data/processed/pretraining_1km';Q=ROOT/'04_outputs/pretraining';df=pd.read_csv(P/'model_table_1000.csv');en=pd.read_csv(P/'road_enrichment_1000.csv');df=df.merge(en,on='grid_id',how='left',validate='one_to_one')
classcols=[c for c in df if c.startswith('road_share_S')];df['road_type_dominant']=df[classcols].fillna(-1).idxmax(axis=1).str.replace('road_share_','',regex=False);df.loc[df.road_length_m==0,'road_type_dominant']='no_motorized_road'
lu=[c for c in df if c.startswith('landuse_share_')];df.loc[df.landuse_coverage<1e-6,lu]=np.nan
traffic_input=P/'traffic_volume_1000.csv'
if traffic_input.exists():
 t=pd.read_csv(traffic_input);df=df.drop(columns=['traffic_volume_2017_2021','traffic_volume_observed']).merge(t,on='grid_id',how='left',validate='one_to_one');df['traffic_volume_observed']=df.traffic_volume_observed.fillna(False).astype(bool)
# Keep true zero quantities separate from missing estimates. Drop no zero-collision cells.
assert len(df)==1473 and df.count_2017_2021.sum()==230536;assert df.grid_id.is_unique;assert df.population.notna().all();assert df.population.ge(0).all();assert np.allclose(df[classcols].sum(axis=1)[df.road_length_m>0],1)
fcols=['freeway_share_functional','arterial_share_functional','collector_share_functional','local_share_functional'];assert np.allclose(df[fcols].sum(axis=1)[df.functional_network_length_m>0],1)
assert not (df.groupby('block_id').split.nunique()>1).any();assert np.isfinite(df.select_dtypes('number').to_numpy()).sum()+df.select_dtypes('number').isna().sum().sum()==df.select_dtypes('number').size
# Match signal snapshot to original topology nodes for a spatial consistency audit, not temporal validation.
n=gpd.read_file(P/'intersection_tiger_topology.gpkg');sig=gpd.read_file(ROOT/'01_data/processed/signal_locations.gpkg');dist,_=cKDTree(np.c_[n.geometry.x,n.geometry.y]).query(np.c_[sig.geometry.x,sig.geometry.y]);pd.DataFrame({'signal_source_row':range(len(sig)),'distance_to_topology_node_m':dist,'within_30m':dist<=30}).to_csv(Q/'signal_topology_match.csv',index=False)
qa={'all_rows':len(df),'eligible_rows':int(df.eligible.sum()),'fixed_eligible_splits':df[df.eligible].split.value_counts().to_dict(),'split_target_audit':'Only total conservation inspected; no test target used for feature/tuning decisions.','signal_within30m_fraction':float((dist<=30).mean()),'signal_distance_median_m':float(np.median(dist)),'landuse_coverage_median':float(df.landuse_coverage.median()),'n_no_landuse_polygon':int((df.landuse_coverage<1e-6).sum()),'no_fitted_models':True}
df.to_csv(P/'model_table_1000_final.csv',index=False);geom=gpd.read_file(P/'grid_1000.gpkg')[['grid_id','geometry']];g=geom.merge(df,on='grid_id',validate='one_to_one');g.to_file(P/'model_table_1000_final.gpkg',driver='GPKG')
for split in ['train','validation','test']:df[df.eligible & (df.split==split)].to_csv(P/f'{split}_1000.csv',index=False)
missing=df.isna().sum().rename('missing').to_frame();missing['fraction']=missing.missing/len(df);missing.to_csv(Q/'final_missingness.csv')
# Raw extract counts cross-check only proves no truncation relative to this published interface.
server={int(r['year']):int(r['n']) for r in json.load(open(ROOT/'01_data/raw/pretraining_20261107/collision_counts_by_year.json'))};extract={y:len(json.load(open(ROOT/f'01_data/raw/collisions_{y}.json'))) for y in range(2017,2022)};assert server==extract
qa['collision_extract_matches_publisher_by_year']=True;qa['collision_completeness']='matches current published extract; 2021 low count remains unexplained and is not a population-level completeness guarantee';(Q/'final_integrity.json').write_text(json.dumps(qa,indent=2))
design=json.loads((ROOT/'02_config/feature_design.json').read_text());blocking=[]
from pipeline_definition import feature_names
tr=df[df.eligible & (df.split=='train')]
for variant in ['baseline','enhanced']:
 for name in feature_names(variant):
  if tr[name].isna().all():blocking.append({'id':'all_missing_selected_feature','variant':variant,'field':name,'reason':'Selected input has no observed values in training data.'})
if design['include_traffic_volume']:
 train_cov=tr.traffic_volume_2017_2021.notna().mean()
 if train_cov<.5:blocking.append({'id':'traffic_coverage','training_coverage':float(train_cov),'required_minimum':.5})
ready={'status':'blocked_for_selected_design' if blocking else 'ready_for_training_inputs_no_fit','preparation_complete_for_selected_design':not bool(blocking),'feature_design':design,'candidate_feature_audits':{'speed_limit':design.get('speed_limit_admission',{})},'training_executed':False,'training_authorized_this_task':False,'working_scale_m':1000,'blocking_items':blocking,'review_items':['2021 published collision count decreases: investigate reporting coverage before interpreting total burden.','Population allocation assumes uniform BG total area, including water; MOE approximate.','Land use, signal and Caltrans functional classification are current snapshots; historical consistency unverified.','TIGER topology junctions are an operational connectivity measure; no complete physical grade-separation audit.','Spatial splits have no distance buffer. RF generalization must be described as retrospective within-city assessment.'],'optional_excluded':['traffic_volume','speed_limit','sight_distance','population_derived_rurality'],'input_table':str(P/'model_table_1000_final.csv'),'quality_checks_passed':qa};(Q/'readiness.json').write_text(json.dumps(ready,indent=2))
# Field dictionary including exact feature provenance and units.
dictionary={
 'count_2017_2021':('target','recorded collisions','LAPD d5tf-ez2w','Sum 2017–2021 cleaned records in half-open grid.'),
 'traffic_volume_2017_2021':('excluded_by_user_design','daily-equivalent vehicles/day','required future authorized counts','Retained as an audit field only. User temporarily excluded traffic volume; not passed to either RF pipeline.'),
 'road_density_km_per_km2':('baseline','road km/city km2','2021 TIGER Roads','S1100,S1200,S1400,S1630,S1640 lines clipped and split. Boundary line assigned by midpoint.'),
 'intersection_density_km2':('baseline','nodes/city km2','2021 TIGER Edges','Degree>=3 unique TLID incident at TNID node on S1200,S1400,S1640; no artificial clipping nodes.'),
 'road_type_dominant':('baseline','MTFCC category','2021 TIGER Roads','Length-dominant MTFCC. no_motorized_road explicit.'),
 'population_density_km2':('baseline','estimated people/city km2','2021 ACS5 B01003 and 2021 BG','Uniform full-BG-area allocation; clipped city area denominator.'),
 'population_moe90_approx':('diagnostic','people','2021 ACS5 B01003 M001','sqrt(sum((BG area weight * BG 90% MOE)^2)). Independence approximation.'),
 'road_sinuosity_length_weighted':('enhanced','dimensionless ratio','2021 TIGER Roads','Length / endpoint distance proxy averaged by clipped road length. Closed/endpoints<=1m missing. Depends on segmentation.'),
 'freeway_share_functional':('enhanced','fraction','Caltrans Functional Classification current snapshot','Classes1,2 length / all functional network length.'),
 'arterial_share_functional':('enhanced','fraction','Caltrans Functional Classification current snapshot','Classes3,4 length / all functional network length.'),
 'signal_density_snapshot_km2':('enhanced','unique signal points/city km2','LADOT Signal Locations current snapshot','0.1m coordinate deduplication. Does not establish historic installation coverage.'),
 'landuse_uncovered_fraction':('baseline','fraction','General Plan Land Use current snapshot','1 - union category area / city area. Includes unmapped roads/water; not inferred category.'),
 'split':('partition','train/validation/test','fixed5km hash blocks','Test keeps prior rule; train-side validation separate hash. Not chosen by targets.'),
 'eligible':('partition','boolean','city area fraction','>=80% of original1km square lies within city. Full cells table still retains boundary fragments.'),
}
for c in lu:dictionary[c]=('baseline','fraction of clipped city area','General Plan Land Use current snapshot','Union within category per grid; no renormalization of uncovered area; null when no land-use polygons observed.')
rows=[]
for c in df:
 role,unit,source,method=dictionary.get(c,('diagnostic','see name','derived project data','Not selected as model input unless explicitly listed in pipeline_definition.py.'))
 rows.append({'field':c,'dtype':str(df[c].dtype),'role':role,'unit':unit,'source':source,'construction':method,'missing_count':int(df[c].isna().sum())})
pd.DataFrame(rows).to_csv(Q/'data_dictionary.csv',index=False)
# Exact environments, paths and checksums, without serializing a fitted model.
manifest=[]
for folder in [ROOT/'01_data/raw/pretraining_20261107',P]:
 for f in sorted(folder.glob('*')):
  if f.is_file():manifest.append({'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(ROOT/'00_admin/pretraining_manifest.json').write_text(json.dumps({'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':manifest},indent=2))
versions={m:importlib.metadata.version(m) for m in ['numpy','pandas','scipy','geopandas','shapely','pyproj','scikit-learn','joblib']};(ROOT/'05_models/pretraining/environment.json').write_text(json.dumps({'python':platform.python_version(),'packages':versions},indent=2));print(json.dumps(qa,indent=2));print('READINESS',ready['status'])

