"""Import authorized, dated daily-equivalent traffic observations. Never geocodes or invents values."""
import sys,pathlib,json,argparse,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.runtime'))
import pandas as pd,numpy as np,geopandas as gpd

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--input',required=True,help='Authorized CSV matching02_config/traffic_values_input_template.csv');a=parser.parse_args();source=pathlib.Path(a.input);df=pd.read_csv(source,dtype={'station_id':str});required=['station_id','count_date','longitude','latitude','daily_volume_vehicles','count_type','is_daily_equivalent','source_url'];assert set(required)<=set(df),required
 if df.empty:raise ValueError('No traffic observations supplied')
 for c in ['longitude','latitude','daily_volume_vehicles']:df[c]=pd.to_numeric(df[c],errors='coerce')
 df['parsed_date']=pd.to_datetime(df.count_date,errors='coerce');equiv=df.is_daily_equivalent.astype(str).str.lower().isin(['true','1','yes']);df['accepted']=df.parsed_date.between('2017-01-01','2021-12-31 23:59:59')&df.longitude.between(-119,-117)&df.latitude.between(33,35)&df.daily_volume_vehicles.ge(0)&np.isfinite(df.daily_volume_vehicles)&equiv&df.station_id.notna()&df.source_url.notna()&df.count_type.notna()
 r=df[df.accepted].drop_duplicates(required).copy()
 if r.empty:raise ValueError('No valid2017–2021 daily-equivalent observations; no output or substitution made')
 if r.duplicated(['station_id','parsed_date']).any():raise ValueError('Conflicting station/date observations require explicit source review')
 xy=gpd.GeoDataFrame(r,geometry=gpd.points_from_xy(r.longitude,r.latitude),crs=4326).to_crs(26911);city=gpd.read_file(ROOT/'01_data/processed/city_boundary.gpkg').geometry.union_all();inside=xy.geometry.intersects(city);xy=xy[inside].copy();
 if xy.empty:raise ValueError('No valid observations inside city boundary')
 origin=np.array([345000.,3730000.]);ij=np.floor((np.c_[xy.geometry.x,xy.geometry.y]-origin)/1000).astype(int);xy['grid_id']=[f'1000_{i}_{j}' for i,j in ij]
 # A station must not move between cells. Multiple study dates average per station before averaging stations.
 if (xy.groupby('station_id').grid_id.nunique()>1).any():raise ValueError('Station moves between cells; split into distinct site IDs first')
 station=xy.groupby(['grid_id','station_id']).agg(station_mean_daily=('daily_volume_vehicles','mean'),n_observations=('daily_volume_vehicles','size'),date_min=('parsed_date','min'),date_max=('parsed_date','max')).reset_index();grid=station.groupby('grid_id').agg(traffic_volume_2017_2021=('station_mean_daily','mean'),traffic_volume_station_count=('station_id','nunique'),traffic_volume_n_observations=('n_observations','sum')).reset_index();grid['traffic_volume_observed']=True
 P=ROOT/'01_data/processed/pretraining_1km';Q=ROOT/'04_outputs/pretraining';grid.to_csv(P/'traffic_volume_1000.csv',index=False);station.to_csv(P/'traffic_station_summary.csv',index=False);df.to_csv(Q/'traffic_import_rows.csv',index=False);sha=hashlib.sha256(source.read_bytes()).hexdigest();snapshot=ROOT/f'01_data/raw/pretraining_20261107/traffic_authorized_{sha[:16]}.csv'
 if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
 qa={'source_sha256':sha,'n_input':len(df),'n_in_city_valid':len(xy),'grid_cells_observed':len(grid),'station_count':len(station),'aggregation':'Mean observed daily-equivalent traffic per station, then unweighted station mean per grid; sampled dates only, not a complete five-year AADT.','count_types':sorted(xy.count_type.astype(str).unique().tolist()),'source_urls':sorted(xy.source_url.astype(str).unique().tolist())};(Q/'traffic_import_qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2));return 0
if __name__=='__main__':main()
