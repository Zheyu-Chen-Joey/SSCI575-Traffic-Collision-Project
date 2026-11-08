from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
sections=[('Zexu Gao','Slides 1–4',[
('Slide 1  Project Progress Update', '''Hello everyone. Today, our team will present the progress of our Los Angeles traffic collision project.
Our study focuses on recorded traffic collisions within the City of Los Angeles from 2017 to 2021. We aim to predict collision counts using urban context and roadway-design features, with Random Forest regression as our modeling method.
Since the first phase, we have made three main updates. We added roadway-design features, completed the main data preprocessing steps, and examined grid sizes before selecting a one-kilometer working grid.
In this presentation, I will introduce the revised design and our progress. Zheyu will explain the predictors and grid selection. Xinchen will then present the planned modeling and evaluation.'''),
('Slide 2  Why We Revised the Phase 1 Design', '''Our first revision concerns how we describe roads.
Land use provides useful information about the surrounding environment, but it does not fully describe the road itself. For example, a freeway and a local street may pass through similar land-use areas, while having very different operating conditions.
We therefore added road sinuosity, freeway and arterial shares, and signal point density. These features provide additional information about road geometry and operation.
Our second revision concerns spatial scale. Rather than choosing a grid size without checking it, we examined 31 grid sizes. This analysis informed our selection of a one-kilometer working grid, which Zheyu will explain.'''),
('Slide 3  Revised Research Questions and Scope', '''Our project has three research questions.
First, how well can road network, population, and land-use features predict recorded collision counts?
Second, do the additional roadway-design features improve prediction beyond the baseline features?
Third, what do the scale diagnostics reveal about spatial structure at our selected grid size?
Our target is the number of recorded collisions in each grid cell. The analysis examines predictive relationships, and we will avoid interpreting feature importance as evidence of causation.'''),
('Slide 4  Progress Completed So Far', '''We have completed the main preprocessing work.
The cleaned collision dataset contains 230,536 records. We have prepared road-network features, population estimates, land-use shares, and the additional roadway-design inputs.
We have also constructed the one-kilometer grid. It contains 1,473 cells intersecting the city boundary, of which 1,113 meet our city-area eligibility rule.
The data and training scripts are prepared, but we have not trained either model yet.
I will now hand over to Zheyu to explain our selected variables and grid choice.''')]),
('Zheyu Chen','Slides 5–7',[
('Slide 5  Updated Predictors', '''Thank you, Zexu. I will introduce our predictors, preprocessing workflow, and grid selection.
Our baseline model contains five feature groups: road density, intersection density, road type, population density, and land-use composition.
Road density measures the amount of road within each grid cell. Intersection density describes road-network connectivity, while road type identifies the dominant road category.
Population density represents the residential population context. For land use, we use category shares rather than assigning one dominant category to the entire cell. We also retain the uncovered fraction so that the shares do not imply complete land-use coverage.
The enhanced model adds four inputs: road sinuosity, freeway share, arterial share, and signal point density.
Road sinuosity is a geometry-based measure of how indirect a road segment is. Freeway and arterial shares describe road function, while signal point density represents the concentration of signal locations.
Both models will use the same grid cells and collision counts.'''),
('Slide 6  Preprocessing Workflow', '''Our workflow has six main steps.
First, we filter collision records to the study period and remove invalid locations.
Second, we clip the spatial datasets to the City of Los Angeles and use the same projected coordinate system, EPSG 26911, so that distances and areas are measured in meters.
Third, we construct the grid using a fixed origin.
Fourth, we calculate the baseline and additional roadway-design features.
Fifth, we aggregate those features into one row per grid cell.
Finally, we check record totals, missing values, and spatial assignments. Each valid collision is assigned to exactly one cell, and zero-collision cells are retained.'''),
('Slide 7  Grid Selection', '''We examined 31 grid sizes, from 500 to 5,000 meters, using 150-meter increments.
For each size, we counted collisions within cells and examined the spatial variation in those counts using a semivariogram. One diagnostic was the nugget-to-sill ratio, or NSR.
The search identified a first local NSR dip near 1.1 kilometers. This provided a nearby diagnostic reference, but it did not establish a unique best scale.
We selected one kilometer as a practical working scale because it provides round units and makes maps and feature summaries easier to interpret.
We then constructed and checked the exact one-kilometer grid separately. Its diagnostics show spatial autocorrelation in collision counts, which supports using spatial methods in the subsequent analysis.
Our grid choice therefore combines diagnostic evidence with a clear reporting unit. It is not a claim that one kilometer will produce the lowest prediction error.
Xinchen will now explain how we plan to compare the two Random Forest models.''')]),
('Xinchen Geng','Slides 8–11',[
('Slide 8  Random Forest Experiment', '''Thank you, Zheyu. Our experiment uses one algorithm, Random Forest regression, with two feature sets.
The baseline model uses the five groups just introduced: road density, intersection density, road type, population density, and land use.
The enhanced model uses all baseline inputs and adds road sinuosity, freeway share, arterial share, and signal point density.
This comparison allows us to examine the predictive contribution of the added roadway-design information while keeping the algorithm, target, and spatial partitions consistent.
We will evaluate whether these additions reduce prediction error and unexplained spatial patterns. Improvement is a hypothesis to test, rather than an assumed outcome.'''),
('Slide 9  Architecture and Overfitting Control', '''The table presents our planned Random Forest settings.
We plan to start with 300 trees and consider up to 500. Our initial maximum tree depth is 12, with a minimum of 10 samples for splitting and five samples in each leaf.
These restrictions help prevent individual trees from becoming too complex. We also use a fixed random seed to make the experiments reproducible.
These are starting settings, rather than fitted results. Parameter tuning will use spatial folds within the training data. Validation results will help us assess the selected configuration, while the final test set will remain separate.
Spatial validation will provide the main evidence of generalization. Out-of-bag error, if examined, will be supplementary.'''),
('Slide 10  Evaluation and Spatial Diagnostics', '''We will evaluate prediction using R-squared, root mean squared error, and mean absolute error.
We will also compare observed and predicted counts and examine differences between training and validation performance.
Because nearby cells can share similar conditions, prediction accuracy alone is insufficient. We will map residuals and calculate residual Moran’s I to check whether spatial clustering remains after prediction.
Feature-importance stability will provide another check on how consistently the models use the available information.
Our interpretation will remain focused on recorded collision burden. The results will not establish causal effects or exposure-adjusted collision risk.'''),
('Slide 11  Preliminary Progress and Next Steps', '''At this stage, the core datasets are preprocessed, the one-kilometer grid is constructed, and the selected predictors are prepared.
Our next step is to finalize the input version, train the baseline and enhanced models, and compare their performance using the same spatial partitions.
We will then examine residual spatial structure and feature-importance stability before preparing the final maps and presentation figures.
The main progress so far is a reproducible data workflow and a defined model comparison. Model performance remains unknown because training has not yet started.
Thank you for listening. We welcome your questions.''')])]
doc=Document();sec=doc.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.7);sec.left_margin=sec.right_margin=Inches(.8)
for name in ['Normal','Title','Heading 1','Heading 2']:
 st=doc.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(11);doc.styles['Normal'].paragraph_format.space_after=Pt(5);doc.styles['Normal'].paragraph_format.line_spacing=1.08
doc.styles['Title'].font.size=Pt(20);doc.styles['Heading 1'].font.size=Pt(17);doc.styles['Heading 2'].font.size=Pt(12)
for i,(name,slides,parts) in enumerate(sections):
 if i:doc.add_page_break()
 if i==0:
  doc.add_paragraph('SSCI 575 Presentation 2 Speaking Script','Title')
  doc.add_paragraph('English speaking notes for three presenters. Each section targets approximately three minutes; rehearse with natural pauses and slide transitions. No models have been trained.').paragraph_format.space_after=Pt(12)
 doc.add_heading(name,1)
 count=sum(len(t.split()) for h,t in parts);doc.add_paragraph(f'{slides}  |  Target 3 minutes  |  {count} words').paragraph_format.space_after=Pt(10)
 for j,(heading,txt) in enumerate(parts):
  # Keep each presenter’s two-page practice copy predictable.
  if j==2:doc.add_page_break()
  doc.add_heading(heading,2)
  for line in txt.split('\n'):doc.add_paragraph(line)
footer=sec.footer.paragraphs[0];footer.alignment=2
r=footer.add_run('SSCI 575  |  ');r.font.size=Pt(9)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
for el in list(doc.styles.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
for el in list(doc.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
out=Path('06_reports/SSCI575_Presentation2_Speaking_Script.docx');doc.save(out);print(out)
