import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path.cwd()/'.runtime'))
import geopandas as gpd
for n in ['landuse','traffic_counts']:
 g=gpd.read_file('01_data/processed/'+n+'.gpkg');print(n,len(g));print(g.drop(columns='geometry').head(2).to_json());
 if n=='landuse':print(g['Category'].value_counts().to_dict());print(g['GPLU_Legend'].value_counts().head(10).to_dict())
