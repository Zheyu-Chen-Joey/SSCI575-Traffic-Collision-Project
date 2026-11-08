import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {FileBlob,PresentationFile} from 'file:///C:/Users/czy08/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const workspaceDir=process.cwd();
const source='C:/Users/czy08/Downloads/SSCI575_Presentation2_Traffic_Project_USC_Template.pptx.pptx';
const SKILL_DIR='C:/Users/czy08/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const p=await PresentationFile.importPptx(new FileBlob(await fs.readFile(source),'application/vnd.openxmlformats-officedocument.presentationml.presentation'));
const info=await p.inspect({kind:'slide,textbox,table,layout',maxChars:1000000});
const records=info.records;
function shape(sl,name){const r=records.find(r=>r.kind==='textbox'&&r.slideIndex===sl-1&&r.name===name);if(!r)throw Error(`Missing ${sl} ${name}`);return p.resolve(r.id);}
function put(sl,n,text){const x=shape(sl,'TextBox '+n);x.text=text;x.text.autoFit='none';x.text.wrap='square';return x;}
function table(sl,values){const r=records.find(r=>r.kind==='table'&&r.slideIndex===sl-1);const t=p.resolve(r.id);for(let i=0;i<values.length;i++)for(let j=0;j<values[i].length;j++)t.cells.set(i,j,values[i][j]);return t;}

put(1,18,'• Added roadway-design variables\n• Assessed grid scales and selected a 1 km working grid\n• Completed core data preprocessing\n• Finalized the Random Forest experiment design');
put(2,24,'We added variables describing road geometry and operation: road sinuosity, freeway/arterial share, and signal point density.');
put(2,29,'Issue 3: Grid selection');
put(2,30,'We assessed 31 grid sizes from 500 to 5,000 m. A local NSR dip near 1.1 km informed the choice of a round 1 km working grid for mapping and aggregation.');
put(3,12,'The project tests added roadway information using a fixed 1 km working grid.');
put(3,18,'How well can road network, population, and land use predict 2017–2021 collision counts?');
put(3,24,'Do roadway-design variables add useful predictive information beyond the five baseline feature groups?');
put(3,30,'What do scale diagnostics show about spatial structure at the selected 1 km working grid?');
put(4,32,'Road sinuosity, freeway/arterial shares, and signal point density prepared for grid aggregation.');
put(4,36,'1 km working grid');
put(4,37,'1 km grid constructed: 1,473 city-intersecting cells; 1,113 meet the city-area eligibility rule.');
put(5,12,'Five baseline feature groups are compared with the added roadway-design inputs.');
put(5,14,'Sources: TIGER 2021, ACS 2021, LA land use, Caltrans functional classes and LADOT signals.');
table(5,[['Feature group','Variables','Status'],['Road network','Road Density; Intersection Density; Road Type','Baseline'],['Population','Population Density','Baseline'],['Land use','Land Use shares; uncovered fraction','Baseline'],['Road geometry','Road Sinuosity proxy','Added'],['Road function','Freeway Share; Arterial Share','Added'],['Intersection control','Signal Point Density','Added']]);
put(6,12,'All datasets use the City of Los Angeles boundary, EPSG:26911, and a fixed 1 km working grid.');
put(6,32,'1 km\nfixed origin');
put(6,39,'roads + population\nland use');
put(6,46,'one row per\n1 km grid');
put(6,60,'Road Sinuosity +\nFreeway/Arterial Share +\nSignal Point Density');
put(7,11,'Grid Selection: 1 km');
put(7,12,'Scale diagnostics inform a practical, consistent unit for mapping and feature aggregation.');
table(7,[['Step','Evidence','Interpretation','Choice'],['Scale search','31 grids: 500–5,000 m','First local NSR dip near 1.1 km','Nearby candidate'],['Working grid','Fixed 1 km × 1 km','Round units; clear maps and summaries','Practical scale'],['1 km checks','1,473 cells; 1,113 eligible','NSR 0.2587; Moran’s I 0.7402','Diagnosed separately']]);
put(7,18,'Selection rationale');
put(7,19,'We use 1 km for round units and consistent interpretation. The nearby 1.1 km NSR dip informed the choice; it does not establish a unique optimum.');
put(7,20,'Source: 31-scale search and separate 1 km diagnostics. No RF training used for grid selection.');
put(8,18,'Five baseline groups:\nRoad Density\nIntersection Density\nRoad Type\nPopulation Density\nLand Use');
put(8,24,'Baseline features +\nRoad Sinuosity proxy\nFreeway / Arterial Share\nSignal Point Density');
put(10,24,'Training vs. validation error\nOOB error\nSpatial split sensitivity');
put(10,36,'Second-phase plan: fixed 1 km grid, held-out performance and residual spatial diagnostics.');
put(11,18,'✓ Core datasets are preprocessed\n✓ Fixed 1 km grid constructed\n✓ Road sinuosity derived from geometry\n✓ Freeway/arterial shares prepared\n✓ Signal point density prepared');
put(11,24,'1. Finalize the 1 km modeling inputs\n2. Run Baseline RF and Enhanced RF\n3. Compare R² / RMSE / MAE\n4. Check residual Moran’s I\n5. Review feature-importance stability\n6. Prepare maps and StoryMap-ready figures');
for(const n of [26,31]){const x=shape(4,'TextBox '+n);x.position={...x.position,width:600};}
const note='Current project uses a practical1000m working grid; origin E345000,N3730000,EPSG26911.31 scales500–5000m in150m increments yielded a first local NSR dip at1100m,not a unique optimum.1000m independently diagnosed:1473 cells,1113 eligible>=80%cityarea,NSR0.25868049,MoranI0.74023965. Selected inputs: five baseline groups (12fields), enhanced four additions (16fields). No model trained. Local evidence:02_config/feature_design.json,04_outputs/pretraining/feature_build_qa.json,06_reports/grid_decision.md.';
for(const n of [1,2,3,4,5,6,7,8,11])p.slides.items[n-1].speakerNotes.text=note;
await fs.writeFile('06_reports/_qa/ppt_build/edited_inspect.json',JSON.stringify(await p.inspect({kind:'slide,textbox,table',maxChars:1000000})));
const candidate=path.join(workspaceDir,'06_reports/_qa/ppt_build/candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);console.log('EXPORTED',candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
try {
const out=await finalizePresentation({workspaceDir,candidatePath:candidate,finalPath:path.join(workspaceDir,'06_reports/presentations/SSCI575_Presentation2_Downloads_Minimal_Final.pptx'),pythonExecutable:'C:/Users/czy08/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','9753600,7315200','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','5','--require-native-table-slide','7','--require-native-table-slide','9'],requiredNativeTableOwnerSlides:[5,7,9],verifyArtifactToolImport:true,receiptPath:path.join(workspaceDir,'06_reports/_qa/ppt_build/downloads_minimal_final.validation.json')});console.log(JSON.stringify(out));
}catch(e){console.error('FINALIZE:',e.message);process.exitCode=1;}
