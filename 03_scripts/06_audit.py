import json,pathlib
from collections import Counter
from zipfile import ZipFile
import xml.etree.ElementTree as ET
p=pathlib.Path('00_admin/source/SSCI575_Project_Update.docx');root=ET.fromstring(ZipFile(p).read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};text='\n'.join(''.join(e.itertext()) for e in root.findall('.//w:t',ns));pathlib.Path('00_admin/source/proposal_extracted.txt').write_text(text,encoding='utf-8')
rows=[]
for f in pathlib.Path('01_data/raw').glob('collisions_20*.json'):rows+=json.loads(f.read_text())
c=Counter(x['date_occ'][:7] for x in rows);pathlib.Path('04_outputs/qa/monthly_counts.csv').write_text('month,n\n'+'\n'.join(f'{k},{v}' for k,v in sorted(c.items())))
p=pathlib.Path('01_data/raw/acs2021_population.json')
if p.exists() and p.read_text().lstrip().startswith('<'):p.rename(p.with_suffix('.failed.html'))
