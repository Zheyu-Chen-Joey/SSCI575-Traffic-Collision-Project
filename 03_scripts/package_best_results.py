"""Package the single retained spatial RF and its reproducible evidence."""
from pathlib import Path
import json,hashlib,zipfile,datetime,re
R=Path(__file__).resolve().parents[1];O=R/'04_outputs/rf_spatial_v5';M=R/'05_models/rf_spatial_v5';models=list((R/'05_models').rglob('*.joblib'));assert len(models)==1 and models[0]==M/'spatial_frozen_rf.joblib'
clean=R/'00_admin/cleanup_manifest.json';c=json.loads(clean.read_text(encoding='utf-8-sig'));c['post_cleanup_checks']['final_report_rendered_pages']=5;c['post_cleanup_checks']['obsolete_QA_and_logs_removed']=True;clean.write_text(json.dumps(c,indent=2),encoding='utf-8')
files=[R/p for p in ['README.md','requirements.txt','00_admin/latest_results.json','00_admin/cleanup_manifest.json','02_config/feature_design.json','02_config/spatial_extension_v5.json','06_reports/RF_Spatial_Extension_v5.docx','06_reports/grid_decision.md','06_reports/Signal_Source_Semantics_Clarification.txt','06_reports/presentations/SSCI575_Presentation2_Downloads_Minimal_Final.pptx','06_reports/SSCI575_Presentation2_Speaking_Script.docx','03_scripts/package_best_results.py','03_scripts/create_rf_spatial_v5_report.py','01_data/processed/pretraining_1km/model_table_1000_final.csv','01_data/processed/pretraining_1km/grid_1000.gpkg']]
for folder in [M,O]:files +=[p for p in folder.rglob('*')if p.is_file()and p.suffix!='.log'and '__pycache__'not in p.parts]
files +=[R/'03_scripts/pretraining'/name for name in ['pipeline_definition.py','rf_coverage_scaled_model.py','rf_spatial_model.py','predict_spatial_rf_v5.py','train_best_spatial_rf.py','export_rf_spatial_v5.py']]
files=sorted(set(files));assert all(p.is_file()for p in files)
for target in re.findall(r'\]\(([^)]+)\)',(R/'README.md').read_text()):
 if not target.startswith(('http:','https:','#')):assert (R/target).exists(),target
manifest={'version':'spatial_RF_v5_best_only','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trained_model_count':1,'retention':'selected model plus data, necessary verification and frozen references; original raw snapshots remain in full repository','files':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in files]};mp=R/'00_admin/project_result_manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');dest=R/'06_reports/SSCI575_Project_Results.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files:z.write(p,p.relative_to(R).as_posix())
 z.write(mp,'00_admin/project_result_manifest.json');z.writestr('PACKAGE_README.txt','Best-only spatial RF v5. Exactly one trained model. See README.md. Frozen reference predictions support comparisons without old model artifacts. Full raw snapshots and local runtime are retained in the complete workspace, not bundled here.\n')
with zipfile.ZipFile(dest)as z:assert z.testzip()is None;assert len([n for n in z.namelist()if n.endswith('.joblib')])==1
print('Best-only package verified:',len(files),'files,',round(dest.stat().st_size/1e6,2),'MB; exactly1model')
