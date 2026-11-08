import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import pandas as pd
r=pd.read_csv('01_data/processed/pretraining_1km/model_table_1000.csv');print(r[['population_geometry_coverage','landuse_coverage','landuse_overlap_fraction','sinuosity_length_coverage']].describe().to_string());print(json.load(open('04_outputs/pretraining/feature_build_qa.json'))['signals']);print(r.dtypes[['eligible','split']])
