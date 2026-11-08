from pathlib import Path
p=Path('03_scripts/pretraining/import_traffic_values.py');s=p.read_text(encoding='utf-8-sig').replace('return0','return 0');p.write_text(s,encoding='utf8')
p=Path('03_scripts/pretraining/audit_traffic_summary.py');s=p.read_text(encoding='utf-8-sig').replace("df['total_numeric']=", "df.loc[~df['parsed_date'].between('1950-01-01','2026-11-07'),'parsed_date']=pd.NaT;df['total_numeric']=");p.write_text(s,encoding='utf8')
p=Path('03_scripts/pretraining/finalize_inputs.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("# Keep true zero quantities separate", """traffic_input=P/'traffic_volume_1000.csv'
if traffic_input.exists():
 t=pd.read_csv(traffic_input);df=df.drop(columns=['traffic_volume_2017_2021','traffic_volume_observed']).merge(t,on='grid_id',how='left',validate='one_to_one');df['traffic_volume_observed']=df.traffic_volume_observed.fillna(False).astype(bool)
# Keep true zero quantities separate""")
s=s.replace("ready={'status':'blocked_for_full_baseline'", """train_cov=df.loc[df.eligible & (df.split=='train'),'traffic_volume_2017_2021'].notna().mean()
if train_cov>=.5:blocking=[]
else:blocking[0]['training_value_coverage']=float(train_cov);blocking[0]['required_minimum_training_coverage']=.5;blocking[0]['threshold_basis']='Project operational gate, not a universal statistical threshold.'
ready={'status':'blocked_for_full_baseline' if blocking else 'ready_with_documented_caveats'""")
p.write_text(s,encoding='utf8')
