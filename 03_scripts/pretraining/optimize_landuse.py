from pathlib import Path
p=Path('03_scripts/pretraining/build_1km_features.py');s=p.read_text(encoding='utf-8-sig');start=s.index("lu=gpd.read_file(ROOT/'01_data/processed/landuse.gpkg')");end=s.index('# Signals and potential traffic coverage',start)
s=s[:start]+'''lu=gpd.read_file(ROOT/'01_data/processed/landuse.gpkg');catmap={re.sub('[^a-z0-9]+','_',c.lower()).strip('_'):c for c in lu.Category.unique()};catreverse={v:k for k,v in catmap.items()};idx=lu.sindex
from concurrent.futures import ThreadPoolExecutor

def local_landuse(k):
 geom=g.geometry.iloc[k];matches=idx.query(geom,predicate='intersects');sub=lu.iloc[matches];unions={}
 for cat,group in sub.groupby('Category'):
  pieces=shapely.intersection(group.geometry.to_numpy(),geom);unions[catreverse[cat]]=shapely.union_all(pieces)
 row={name:float(unions[name].area) if name in unions else 0.0 for name in catmap};row['coverage_m2']=float(shapely.union_all(list(unions.values())).area) if unions else 0.0
 return row
with ThreadPoolExecutor(max_workers=6) as pool:landrows=list(pool.map(local_landuse,range(len(g))))
la=pd.DataFrame(landrows)
for name in catmap:g['landuse_share_'+name]=la[name].to_numpy()/(g.city_area_km2.to_numpy()*1e6)
g['landuse_coverage']=la.coverage_m2.to_numpy()/(g.city_area_km2.to_numpy()*1e6);cols=[c for c in g if c.startswith('landuse_share_')];g['landuse_overlap_fraction']=g[cols].sum(axis=1)-g.landuse_coverage;g['landuse_uncovered_fraction']=(1-g.landuse_coverage).clip(0,1);qa['landuse']={'categories':catmap,'max_cross_category_overlap_fraction':float(g.landuse_overlap_fraction.max()),'n_cells_overlap_gt_1pct':int((g.landuse_overlap_fraction>.01).sum()),'snapshot':'current General Plan Land Use; not proof of 2017–2021 conditions'};print('LANDUSE',qa['landuse'],flush=True)
''' + s[end:];p.write_text(s,encoding='utf8')
