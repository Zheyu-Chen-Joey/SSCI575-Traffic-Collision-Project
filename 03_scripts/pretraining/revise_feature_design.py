import pathlib,json
R=pathlib.Path.cwd()
design={'version':'2026-11-07_no_traffic_volume','authorization':'User explicitly requested temporary removal of traffic volume on2026-11-07','working_scale_m':1000,'include_traffic_volume':False,'baseline_feature_groups':['road_density','intersection_density','road_type','population_density','land_use_composition'],'enhanced_additions':['road_sinuosity_proxy','freeway_share_functional','arterial_share_functional','signal_density_snapshot'],'target':'published_LAPD_collision_count_2017_2021','training_authorized':False,'interpretation_limits':['Predict recorded collision burden, not exposure-adjusted crash risk or accident rate.','No direct vehicle-exposure control; road/population features are not claimed to replace observed traffic.','Baseline uses5 original groups after traffic removal, not the original6-group baseline.']}
(R/'02_config/feature_design.json').write_text(json.dumps(design,indent=2),encoding='utf8')
p=R/'03_scripts/pretraining/pipeline_definition.py';s=p.read_text(encoding='utf-8-sig').replace('import sys,pathlib','import sys,pathlib,json').replace("BASE_NUM=['traffic_volume_2017_2021',","BASE_NUM=[");s=s.replace("BASE_CAT=['road_type_dominant']", "DESIGN=json.loads((ROOT/'02_config/feature_design.json').read_text())\nif DESIGN['include_traffic_volume']:BASE_NUM=['traffic_volume_2017_2021',*BASE_NUM]\nBASE_CAT=['road_type_dominant']");p.write_text(s,encoding='utf8')
p=R/'03_scripts/pretraining/finalize_inputs.py';s=p.read_text(encoding='utf-8-sig');start=s.index("traffic=json.load(open(Q/'traffic_audit.json'))");end=s.index("ready={'status':",start)
s=s[:start]+'''design=json.loads((ROOT/'02_config/feature_design.json').read_text());blocking=[]
from pipeline_definition import feature_names
tr=df[df.eligible & (df.split=='train')]
for variant in ['baseline','enhanced']:
 for name in feature_names(variant):
  if tr[name].isna().all():blocking.append({'id':'all_missing_selected_feature','variant':variant,'field':name,'reason':'Selected input has no observed values in training data.'})
if design['include_traffic_volume']:
 train_cov=tr.traffic_volume_2017_2021.notna().mean()
 if train_cov<.5:blocking.append({'id':'traffic_coverage','training_coverage':float(train_cov),'required_minimum':.5})
''' + s[end:]
s=s.replace("'blocked_for_full_baseline' if blocking else 'ready_with_documented_caveats'","'blocked_for_selected_design' if blocking else 'ready_for_training_inputs_no_fit'").replace("'preparation_complete_except_external_traffic_values':True","'preparation_complete_for_selected_design':not bool(blocking),'feature_design':design").replace("'optional_excluded':['speed_limit'","'optional_excluded':['traffic_volume','speed_limit'")
s=s.replace("'traffic_volume_2017_2021':('baseline'","'traffic_volume_2017_2021':('excluded_by_user_design'").replace("'Missing until study-period dated numeric observations are ingested. No automatic historic substitution.'","'Retained as an audit field only. User temporarily excluded traffic volume; not passed to either RF pipeline.'")
p.write_text(s,encoding='utf8')
p=R/'03_scripts/pretraining/verify_inputs.py';s=p.read_text(encoding='utf-8-sig').replace("columns=feature_names(v);assert", "columns=feature_names(v);assert not any(c.startswith('traffic_') for c in columns),'Excluded traffic input leaked into pipeline';assert");p.write_text(s,encoding='utf8')
p=R/'02_config/analysis.json';d=json.loads(p.read_text());d['feature_design']='02_config/feature_design.json';d['traffic_volume_included']=False;d['model_allowed']=False;d['scope']='prepare_only_no_training';p.write_text(json.dumps(d,indent=2),encoding='utf8')
