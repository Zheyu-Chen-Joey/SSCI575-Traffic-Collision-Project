"""Package the single retained spatial RF and its reproducible evidence."""
from pathlib import Path
import json,hashlib,zipfile,datetime,re
R=Path(__file__).resolve().parents[1];O=R/'04_outputs/rf_spatial_v5';M=R/'05_models/rf_spatial_v5';models=list((R/'05_models').rglob('*.joblib'));research=R/'05_models/rf_hollywood_research/hollywood_holdout_pair.joblib';allowed_models=[M/'spatial_frozen_rf.joblib']+([research]if research.exists()else[]);assert set(models)==set(allowed_models)
clean=R/'00_admin/cleanup_manifest.json';c=json.loads(clean.read_text(encoding='utf-8-sig'));c['post_cleanup_checks']['final_report_rendered_pages']=5;c['post_cleanup_checks']['obsolete_QA_and_logs_removed']=True;clean.write_text(json.dumps(c,indent=2),encoding='utf-8')
files=[R/p for p in ['README.md','requirements.txt','00_admin/latest_results.json','00_admin/cleanup_manifest.json','02_config/feature_design.json','02_config/spatial_extension_v5.json','06_reports/RF_Spatial_Extension_v5.docx','06_reports/grid_decision.md','06_reports/Signal_Source_Semantics_Clarification.txt','06_reports/presentations/SSCI575_Presentation2_Downloads_Minimal_Final.pptx','06_reports/SSCI575_Presentation2_Speaking_Script.docx','03_scripts/package_best_results.py','03_scripts/create_rf_spatial_v5_report.py','01_data/processed/pretraining_1km/model_table_1000_final.csv','01_data/processed/pretraining_1km/grid_1000.gpkg']]
for folder in [M,O]:files +=[p for p in folder.rglob('*')if p.is_file()and p.suffix!='.log'and '__pycache__'not in p.parts]
files +=[R/'03_scripts/pretraining'/name for name in ['pipeline_definition.py','rf_coverage_scaled_model.py','rf_spatial_model.py','rf_local_weighted_model.py','predict_spatial_rf_v5.py','train_best_spatial_rf.py','export_rf_spatial_v5.py']]
files += [R/'06_reports/RF_Refinement_20261107.txt']
files += [R/'03_scripts/pretraining'/name for name in ['rf_refined_local_model.py','refine_local_rf.py','finalize_refinement_audit.py']]
files += [R/'03_scripts/pretraining'/name for name in ['rf_rotated_local_model.py','rf_coordinate_blend_model.py','robust_local_rf.py']]
files += [R/'03_scripts/create_coordinate_rf_report.py']
files += [R/'03_scripts/pretraining'/name for name in ['rf_orientation_ensemble.py','study_orientation_ensemble.py']]
files += [R/'06_reports/RF_Tree_Structure_Validation.txt']
files += [R/'03_scripts/pretraining'/name for name in ['study_rf_tree_structure.py','archive_tree_structure_audit.py']]
files += [R/'06_reports/RF_Residual_Hotspots_Investigation.docx',R/'03_scripts/create_residual_investigation_report.py']
files += [R/'03_scripts/pretraining'/name for name in ['rf_input_quality.py','investigate_residual_hotspots.py','complete_residual_audit.py','rf_missingness_robust_model.py','study_missingness_correction.py']]
files += [p for p in (R/'04_outputs/residual_investigation').rglob('*')if p.is_file()and p.suffix!='.log']
files += [R/'06_reports/RF_Scaling_Validation.txt',R/'06_reports/RF_Scaling_Blend_Validation.txt']
files += [R/'03_scripts/pretraining'/name for name in ['study_rf_scaling.py','archive_scaling_audit.py','rf_scaling_blend_model.py','study_rf_scaling_blend.py','archive_scaling_blend_audit.py']]
files += [R/'03_scripts/pretraining/render_scaling_tradeoff.py']
files += [R/'06_reports/RF_Cluster_Targeted_Optimization.docx',R/'03_scripts/create_cluster_targeted_report.py']
files += [R/'03_scripts/pretraining'/name for name in ['rf_cluster_weighted_model.py','study_rf_cluster_weighting.py','study_rf_local_cluster_weighting.py','check_conservative_cluster_candidate.py','diagnose_development_clusters.py','finalize_cluster_targeted_audit.py','build_cluster_evidence.py']]
files += [p for p in (R/'04_outputs/cluster_targeted_optimization').rglob('*')if p.is_file()and p.suffix!='.log']
files += [R/'06_reports/RF_Support_Protection_Optimization.docx',R/'03_scripts/create_support_protection_report.py']
files += [R/'03_scripts/pretraining'/name for name in ['rf_supported_cluster_model.py','study_supported_cluster_rf.py','study_distance_supported_rf.py','finalize_support_protection_audit.py']]
files += [p for p in (R/'04_outputs/support_protection_optimization').rglob('*')if p.is_file()and p.suffix!='.log']
files += [R/'06_reports/RF_Hollywood_Validation.txt',R/'03_scripts/retain_single_release.py']
files += [R/'03_scripts/pretraining'/name for name in ['rf_crossfit_residual_model.py','study_hollywood_residual_rf.py','diagnose_hollywood_residual_candidate.py','finalize_hollywood_audit.py']]
files += [p for p in (R/'04_outputs/hollywood_targeted_optimization').rglob('*')if p.is_file()and p.suffix!='.log']
if research.exists():files += [p for p in research.parent.rglob('*')if p.is_file()and '__pycache__'not in p.parts]
files=sorted(set(files));assert all(p.is_file()for p in files)
for target in re.findall(r'\]\(([^)]+)\)',(R/'README.md').read_text(encoding='utf-8')):
 if not target.startswith(('http:','https:','#')):assert (R/target).exists(),target
manifest={'version':'v8_production_control_plus_Hollywood_research'if research.exists()else'spatial_RF_v5_best_only','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trained_model_count':1,'production_model_count':1,'research_comparison_bundle_count':int(research.exists()),'serialized_model_file_count':len(allowed_models),'retention':'one retained production RF; research candidate entities removed; historical validation evidence retained','files':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in files]};mp=R/'00_admin/project_result_manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');dest=R/'06_reports/SSCI575_Project_Results.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files:z.write(p,p.relative_to(R).as_posix())
 z.write(mp,'00_admin/project_result_manifest.json');z.writestr('PACKAGE_README.txt','Retained production RF control plus Hollywood research comparison bundle when present. Research bundle is not a production replacement. See README.md and its input contract. Frozen reference predictions support comparisons without old model artifacts. Full raw snapshots and local runtime are retained in the complete workspace, not bundled here.\n')
with zipfile.ZipFile(dest)as z:assert z.testzip()is None;assert len([n for n in z.namelist()if n.endswith('.joblib')])==len(allowed_models)
print('Package verified:',len(files),'files,',round(dest.stat().st_size/1e6,2),'MB;1production control +',int(research.exists()),'research comparison bundle')
