from pathlib import Path
p=Path('03_scripts/pretraining/build_1km_features.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("parts=parts[(parts.i.to_numpy()==own[:,0])", "print('ROAD_ASSIGN',parts[['i','j']].head().to_dict(),own[:5].tolist(),mid.head().to_wkt().tolist(),flush=True);parts=parts[(parts.i.to_numpy()==own[:,0])");p.write_text(s,encoding='utf8')
