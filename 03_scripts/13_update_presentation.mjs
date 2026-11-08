import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {FileBlob,PresentationFile} from 'file:///C:/Users/czy08/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const workspaceDir=process.cwd();
const source='C:/Users/czy08/Desktop/SSCI575_Presentation2_Traffic_Project_USC_Template.pptx';
const SKILL_DIR='C:/Users/czy08/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const p=await PresentationFile.importPptx(new FileBlob(await fs.readFile(source),'application/vnd.openxmlformats-officedocument.presentationml.presentation'));
const info=await p.inspect({kind:'slide,textbox,table,layout',maxChars:1000000});
const records=info.records;
function shape(sl,name){const r=records.find(r=>r.kind==='textbox'&&r.slideIndex===sl-1&&r.name===name);if(!r)throw Error(`Missing ${sl} ${name}`);return p.resolve(r.id);}
function put(sl,n,text){const x=shape(sl,'TextBox '+n);x.text=text;x.text.autoFit='none';x.text.wrap='square';return x;}
function table(sl,values){const r=records.find(r=>r.kind==='table'&&r.slideIndex===sl-1);const t=p.resolve(r.id);for(let i=0;i<values.length;i++)for(let j=0;j<values[i].length;j++)t.cells.set(i,j,values[i][j]);return t;}
// Retain all 12 source slides, their branding, Arial typography and object positions.
put(1,2,'Presentation 2: Project Progress Update');
put(1,3,'Traffic Collision Burden in Los Angeles: Urban Context and Road Design');
put(1,7,'Road design added to the study\n31 grid sizes assessed before modeling\n1 km chosen as the working scale\nRF comparison planned after data checks');
put(1,11,'City of Los Angeles\n2017–2021 collision records\nTarget: collision count per 1 km grid\nModel: Random Forest Regression');
put(1,18,'Source: project plan, cleaning logs and scale validation report. Updated November 7, 2026.');
put(2,2,'Feedback and Design Changes');
put(2,3,'Road conditions and spatial scale both require explicit treatment.');
put(2,6,'Land use');
put(2,7,'Surrounding land use only partly describes a road. Road geometry and road class provide additional information about its operating conditions.');
put(2,10,'Road design');
put(2,11,'We plan to add road sinuosity, road-class shares and signal density. Speed limit remains optional until spatial and temporal coverage are verified.');
put(2,14,'A fixed 1 km working grid');
put(2,15,'The 31-scale analysis identified 1.1 km as the first local NSR dip. We adopt 1 km for clear reporting and aggregation. It remains a practical choice with stated limitations.');
put(2,16,'Source: revised plan and local scale diagnostics. NSR = nugget / total sill.');
put(3,2,'Research Questions and Scope');
put(3,3,'Prediction will use a fixed 1 km grid, with scale diagnostics reported separately.');
put(3,7,'How well do traffic exposure, road network, population and land use predict 2017–2021 collision counts at 1 km?');
put(3,11,'Do road geometry, road-class shares and signal density improve prediction beyond the original six feature groups?');
put(3,15,'How sensitive is collision spatial structure to grid size, and what evidence and limitations support the 1 km working scale?');
put(3,24,'Scope: City of Los Angeles, 2017–2021. Spatial test data remain outside tuning and scale fitting.');
put(4,2,'Data Preparation and Current Gaps');
put(4,3,'Collision and geometry processing are complete. Numeric exposure data remain incomplete.');
put(4,7,'232,695 downloaded records. Retained 230,536 after coordinate and city-boundary checks.');
put(4,11,'28,364 clipped road features. Length and sinuosity proxy computed. Intersection topology needs review.');
put(4,14,'Population and land use');
put(4,15,'50,643 land-use features and 2,941 block-group geometries. ACS population values still unavailable.');
put(4,17,'!');put(4,18,'Traffic and signal data');
put(4,19,'6,800 traffic-report locations and 5,506 signal points. Dated traffic values and historical coverage need audit.');
put(4,22,'Scale diagnostics');
put(4,23,'31 grids from 500 to 5,000 m, every 150 m. A separate 1,000 m aggregation is the next step.');
put(4,24,'Source: collision_cleaning.json, predictor_cleaning.json and scale_diagnostics.csv.');
// Existing status icon for incomplete population data.
put(4,13,'!');
put(5,2,'Predictors and Data Readiness');
put(5,3,'Baseline and enhanced feature definitions will use the same 1 km analysis grid.');
table(5,[['Feature group','Planned variables','Current status'],['Traffic exposure','Traffic Volume','Values / dates pending'],['Road network','Road Density, Intersection Density, Road Type','Road geometry ready'],['Urban context','Population Density, Land Use shares','Population pending'],['Road design','Road sinuosity, road-class length shares','Geometry proxy ready'],['Intersection control','Signalized Intersection Density','5,506 points to audit'],['Operating speed','Speed Limit','Optional after audit']]);
put(5,5,'Source: TIGER 2021 roads / block groups, LA land use and LADOT layers. All features need 1 km aggregation.');
put(6,2,'Preprocessing and Scale Diagnostics');
put(6,3,'Scale assessment precedes RF training. The 1 km choice requires its own aggregation.');
put(6,6,'1. Clean');put(6,7,'2017–2021\nunique report IDs\nvalid coordinates');
put(6,11,'2. Project');put(6,12,'City boundary\nEPSG:26911\nmeters');
put(6,16,'3. Count');put(6,17,'31 grid sizes\n500–5,000 m\n150 m steps');
put(6,21,'4. Fit');put(6,22,'Semi-variogram\nNSR and Moran’s I\nfit sensitivity');
put(6,26,'5. Adopt');put(6,27,'1 km work grid\nfixed origin\nclear reporting');
put(6,31,'6. Check');put(6,32,'1 km aggregation\ncoverage audit\nRF table next');
put(6,35,'Current boundary between completed and planned work');
put(6,36,'Scale diagnostics and geometry cleaning are complete. Population, dated traffic values and the 1 km feature table remain pending.');
put(6,37,'Source: scripts 02_clean_and_grid.py, 07_origin_sensitivity.py and 10_validate_range.py.');
put(7,2,'Scale Evidence and the 1 km Decision');
put(7,3,'The working scale balances standard reporting with the available spatial evidence.');
table(7,[['Step','Evidence','Limitation','Decision'],['31-scale search','1.1 km: first local dip\nNSR = 0.2240','Shallow difference\n1.25 km: 0.2259','Retain as a\ndiagnostic candidate'],['Validation','1.1 km dip retained\n52 / 53 block deletions','45 km spherical fit\nRange remains sensitive','Supports candidate\nwith qualifications'],['Working grid','1 km chosen for\nreporting and aggregation','No exact 1 km run in\nthe original search','Recompute 1 km\nmetrics separately']]);
put(7,7,'Interpretation of the evidence');
put(7,8,'Lower NSR alone does not establish the best scale. The 1.1 km findings do not supply 1 km statistics. The 1 km grid is a practical, documented analysis choice.');
put(7,9,'Source: scale_diagnostics.csv and range_validation.md. The 52/53 result is an influence check, not a probability.');
put(8,2,'Random Forest Feature Comparison');
put(8,3,'Planned comparison at 1 km. Both feature sets will use the same spatial split.');
put(8,7,'Original six feature groups:\nTraffic Volume\nRoad Density\nIntersection Density\nRoad Type\nPopulation Density\nLand Use shares');
put(8,11,'Baseline features plus:\nRoad sinuosity proxy\nRoad-class length shares\nSignalized Intersection Density\nSpeed Limit if coverage is adequate');
put(8,15,'Planned comparison');
put(8,16,'Compare spatial test error and residual autocorrelation after data checks and tuning. RF training has not started.');
put(8,17,'Source: revised plan, Section 8. Road sinuosity is a segment-based proxy for curvature.');
put(9,2,'Random Forest Training Plan');
put(9,3,'Starting settings only. Spatial validation will guide tuning after the data checks.');
table(9,[['Setting','Starting plan','Purpose'],['n_estimators','300 to 500','Check prediction stability'],['max_depth','12','Limit tree complexity'],['min_samples_split','10','Avoid small split groups'],['min_samples_leaf','5','Avoid very small leaves'],['max_features','sqrt','Introduce tree diversity'],['Bootstrap / OOB','On / supplementary only','Spatial validation remains primary'],['random_state','42','Reproduce model runs']]);
put(9,7,'Spatial validation');
put(9,8,'Compare tree counts on spatial validation. OOB error is supplementary because nearby grids can share spatial structure.');
put(9,9,'Planned parameters, not fitted results. The reserved test set will not guide tuning or grid selection.');
put(10,2,'Evaluation and Spatial Diagnostics');
put(10,3,'Evaluate both RF feature sets at 1 km after the modeling table is ready.');
put(10,11,'Training vs. validation error\nSpatial split sensitivity\nOOB as a supplement\nFixed test set');
put(10,15,'Residual map\nResidual Moran’s I\nPrediction maps\nImportance stability');
put(10,19,'Interpretation');
put(10,20,'Feature importance describes predictive contribution. Residual clustering will show where the fitted model leaves spatial structure unexplained.');
put(10,20,'Feature importance describes predictive contribution. Check residual clustering and report limits on causal interpretation.');
put(10,20,'Feature importance describes predictive contribution. Residual clustering and causal limits must accompany accuracy results.');
put(10,20,'Feature importance describes predictive contribution. Residual clustering and causal limits must accompany accuracy results.');
// Footer is TextBox 20 in source; interpretation body is TextBox 19.
put(10,19,'Feature importance describes predictive contribution. Check residual clustering and retain the study’s limits on causal interpretation.');
put(10,18,'Interpretation');
put(10,20,'Planned evaluation at 1 km. No R², RMSE, MAE or residual results are available yet.');
put(11,2,'Progress and Next Steps');
put(11,3,'Completed scale diagnostics inform a practical 1 km decision. Modeling remains pending.');
put(11,7,'230,536 cleaned collision records\n31 grid sizes assessed\n1.1 km diagnostic candidate\nExtended-distance and block checks\n1 km working scale selected\nRoad and land-use geometry ready');
put(11,11,'1. Build and check the exact 1 km grid\n2. Audit 2021 collision completeness\n3. Obtain ACS and dated traffic values\n4. Aggregate baseline / enhanced features\n5. Tune RF on spatial validation\n6. Evaluate once on reserved test data');
put(11,14,'Main takeaway');
put(11,15,'We adopt 1 km for clear reporting and aggregation. Scale diagnostics support a nearby candidate, while data gaps and model sensitivity remain explicit.');
put(11,16,'Source: cleaning logs, scale diagnostics, validation report and the November 7 working-scale decision.');
put(12,2,'Team Roles, References and AI Use');
put(12,3,'Suggested presentation time: approximately 10 minutes.');
put(12,7,'Slides 1–4\nStudy scope, design changes, research questions and verified data status');
put(12,11,'Slides 5–7\nPredictors, preprocessing, scale evidence and the 1 km decision');
put(12,15,'Slides 8–11\nPlanned RF comparison, training, spatial evaluation and next steps');
put(12,16,'Methods: Chen et al. (2019), PLOS ONE 14(11), e0225139. Data: LAPD collisions, Census TIGER 2021, ACS 2021, LA land use and LADOT layers. Detailed sources are in slide notes.\n\nAI use: ChatGPT assisted with data processing scripts, diagnostics, writing and slide editing. Results and research decisions require team review.');
put(12,17,'Project materials: SSCI575_Grid_Methods_and_Validation_Report.docx and range_validation.md.');
// Correctly retain original object styles while making existing titles fit within the brand header.
for(let sl=1;sl<=12;sl++){
 const title=shape(sl,'TextBox 2');title.position={...title.position,width:800};
}
const notes={
 1:'Update November 7, 2026. Working scale is 1000 m by user decision for standard reporting. Existing diagnostics are for 500+150k m grids, including 1100 m but excluding 1000 m. Do not transfer their numeric values to 1000 m.',
 2:'Road sinuosity = segment length / endpoint distance, with missing values for endpoint distance <=1 m. This proxy depends on segmentation. MTFCC is not a validated arterial classification. Scale choice precedes RF; do not select scale using final test performance.',
 3:'Fixed geographic holdout: 5 km blocks relative to E345000,N3730000, with (bx*73856093+by*19349663)%5==0. Any grid cell intersecting a reserved block is excluded from variogram fitting. No RF results yet.',
 4:'LAPD raw yearly totals: 2017 57727; 2018 57159; 2019 56628; 2020 42385; 2021 18796. Zero duplicate report IDs. Invalid coordinates 403 and outside-city points 1756. 2021 reduction requires audit. Roads 28364; BG geometry 2941; land use 50643; traffic locations 6800; signals 5506 after spatial cleaning. Population API returned Missing Key HTML. Vision Zero Improvements/2 returned only 60 objects and was not used as a full signal inventory.',
 5:'Road and signal snapshots require historical checks. The traffic layer contains geometry and NavigateLA report URLs, not validated volume/date fields. 68.86% traffic-location coverage belongs to the 1100 m grid and is not valid traffic-value coverage at 1000 m. No population values were acquired.',
 6:'Semi-variogram gamma(h)=sum[(Zi-Zj)^2]/[2N(h)]. NSR=c0/(c0+c1). Main fit: spherical, 25 bins over 0–25 km, >=30 pairs/bin, pair-count weighted least squares, multiple starts, Range upper bound 50 km, seed575, maximum2500 training cells. Include city-intersection grids in output but fit only nonholdout cells with >=80% city area. All 31 grids conserve230536 collisions.',
 7:'At 1100m:1230 total cells,656 eligible training cells,NSR0.224015,Range39.319km. At1250m:NSR0.225890. Four origins near800–1850m give a1100m dip in3/4 settings. Extended validation:14 scales500–2450m, fixed1km lag bins, max lags25/35/45/55/65km, spherical and exponential models, Range cap150km. 35km spherical fit hits cap. Empirical semivariance peaks around35–36km and declines rather than reaching a sustained plateau. Leave-one-5km-block-out:1100m below950m and1250m for29/53 common deletions at25km,52/53 at45km,49/53 at55km. These are influence counts, not confidence levels. 45km is a sensitivity setting, not a retrospectively preferred primary model. New1km aggregation and diagnostics are pending.',
 8:'Proposed feature groups from revised plan. Final predictor table and RF have not been built. Use the same spatial split and response for both feature sets. Feature inclusion depends on quality and study-period coverage.',
 9:'These are proposed initial parameters from the source deck. They are not fitted, evaluated or validated. The original OOB-based early-stop wording is replaced by spatial validation tuning. This deck reports a training plan only.',
 10:'R²,RMSE,MAE and residual Moran are planned. Do not use final test performance to change grid size, features or hyperparameters. A fixed working-scale choice does not establish causal effects.',
 11:'Data gates remain closed until population values, dated traffic counts and study-period audit are complete. Exact1000m count, zero-rate,NSR and coverage have not been calculated in this revision. Do not reuse1100m statistics.',
 12:'Chen L,Gao Y,Zhu D,Yuan Y,Liu Y(2019). Quantifying the scale effect in geospatial big data using semi-variograms. https://doi.org/10.1371/journal.pone.0225139 . This project operationalizes the idea and is not an exact reproduction.'
};
const sources='\nSources: https://data.lacity.org/resource/d5tf-ez2w.json ; https://maps.lacity.org/lahub/rest/services/Boundaries/MapServer/7 ; https://www2.census.gov/geo/tiger/TIGER2021/ROADS/tl_2021_06037_roads.zip ; https://www2.census.gov/geo/tiger/TIGER2021/BG/tl_2021_06_bg.zip ; https://api.census.gov/data/2021/acs/acs5 ; https://maps.lacity.org/lahub/rest/services/City_Planning_Department/MapServer/7 ; https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/22 ; https://maps.lacity.org/lahub/rest/services/LADOT/MapServer/30 . Local evidence: 04_outputs/qa,04_outputs/grid_search,04_outputs/range_validation.';
for(let i=0;i<12;i++){const sn=p.slides.items[i].speakerNotes;sn.text=(sn.text?.trim()?sn.text.trim()+'\n\n':'')+notes[i+1]+([0,3,4,6,11].includes(i)?sources:'');}

for(let sl=1;sl<=12;sl++){const x=shape(sl,'TextBox 3');x.position={left:48,top:120,width:810,height:34};}
put(7,7,'Scale interpretation');
// Repair inherited one-line geometry while retaining template fonts and row positions.
for(const [name,top] of [['TextBox 7',188],['TextBox 11',263],['TextBox 15',338],['TextBox 19',413],['TextBox 23',488]]){
 const x=shape(4,name);x.position={left:127,top,width:720,height:40};
}
put(4,7,'232,695 records downloaded. Retained 230,536 after coordinate and city-boundary checks.');
put(4,23,'31 grids assessed from 500 to 5,000 m. Exact 1,000 m aggregation is next.');
put(9,8,'Tune with spatial validation. Treat OOB error as supplementary.');
shape(9,'TextBox 7').position={left:87.36,top:541,width:700,height:20};
shape(9,'TextBox 8').position={left:87.36,top:561,width:727,height:18};
shape(9,'TextBox 9').position={left:49.92,top:585,width:820,height:16};
shape(9,'TextBox 7').text.insets=0;shape(9,'TextBox 8').text.insets=0;
const footers={1:18,2:16,3:24,4:24,5:5,6:37,7:9,8:17,10:20,11:16,12:17};
for(const [sl,n] of Object.entries(footers)){const x=shape(Number(sl),'TextBox '+n);x.position={left:49.92,top:562.56,width:820,height:28};}

await fs.writeFile('06_reports/_qa/ppt_build/edited_inspect.json',JSON.stringify(await p.inspect({kind:'slide,textbox,table',maxChars:1000000})));
const candidate=path.join(workspaceDir,'06_reports/_qa/ppt_build/candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);console.log('EXPORTED',candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
try {
const out=await finalizePresentation({workspaceDir,candidatePath:candidate,finalPath:path.join(workspaceDir,'06_reports/presentations/SSCI575_Presentation2_Updated_1km_Reviewed.pptx'),pythonExecutable:'C:/Users/czy08/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','9144000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','5','--require-native-table-slide','7','--require-native-table-slide','9'],requiredNativeTableOwnerSlides:[5,7,9],verifyArtifactToolImport:true,receiptPath:path.join(workspaceDir,'06_reports/_qa/ppt_build/final_v3.validation.json')});console.log(JSON.stringify(out));
}catch(e){console.error('FINALIZE:',e.message);process.exitCode=1;}
