import pathlib
p=pathlib.Path('03_scripts/01_download.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("r=requests.get(url,params=params,timeout=180);r.raise_for_status();p.write_bytes(r.content);log.append", "r=requests.get(url,params=params,timeout=180);r.raise_for_status();\n if p.suffix=='.json':\n  try: r.json()\n  except ValueError:\n   p.with_suffix('.failed.html').write_bytes(r.content);raise RuntimeError(f'{name}: expected JSON; API returned HTML, check authentication or service status')\n p.write_bytes(r.content);log.append")
s=s.replace("print(name,len(r.content),flush=True)","print(name,len(r.content),flush=True);pathlib.Path('00_admin/download_manifest.json').write_text(json.dumps(log,indent=2))")
p.write_text(s,encoding='utf-8')
