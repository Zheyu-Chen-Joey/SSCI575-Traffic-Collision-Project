from pathlib import Path
p=Path('03_scripts/pretraining/import_traffic_values.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("&df.station_id.notna()&df.source_url.notna()", "&df.station_id.notna()&df.source_url.notna()&df.count_type.notna()")
s=s.replace("xy=xy[inside].copy();origin=", "xy=xy[inside].copy();\n if xy.empty:raise ValueError('No valid observations inside city boundary')\n origin=")
p.write_text(s,encoding='utf8')
