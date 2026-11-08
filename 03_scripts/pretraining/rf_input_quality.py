"""Observable input-quality flags; these are not calibrated prediction intervals."""
import pandas as pd
from pipeline_definition import LANDUSE

def input_quality_flags(frame):
 coverage=(1-frame.landuse_uncovered_fraction).clip(0,1)
 missing=frame[LANDUSE].isna();airport=(frame.landuse_share_lax_airport>.5)&(frame.population_density_km2==0)
 values=[]
 for i in range(len(frame)):
  tags=[]
  if missing.iloc[i].all():tags.append('landuse_all_missing')
  elif missing.iloc[i].any():tags.append('landuse_partly_missing')
  if pd.isna(coverage.iloc[i]):tags.append('landuse_coverage_unknown')
  elif coverage.iloc[i]<.5:tags.append('landuse_polygon_coverage_below50pct')
  if airport.iloc[i]:tags.append('airport_zero_residential_population_proxy')
  values.append(';'.join(tags)if tags else'none_selected')
 return pd.DataFrame({'landuse_polygon_coverage':coverage.to_numpy(),'input_quality_flags':values,'input_review_recommended':[x!='none_selected'for x in values]})
