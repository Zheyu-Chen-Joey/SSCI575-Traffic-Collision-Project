import importlib.metadata,pathlib
names=['numpy','pandas','scipy','shapely','pyproj','geopandas','requests','matplotlib','pyogrio']
ds={d.metadata['Name'].lower():d.version for d in importlib.metadata.distributions(path=['.runtime'])}
pathlib.Path('requirements.txt').write_text('\n'.join(n+'=='+ds[n] for n in names)+'\n')
