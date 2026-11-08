from zipfile import ZipFile
from lxml import etree as E
import json,pathlib
z=ZipFile(r'C:/Users/czy08/Desktop/SSCI575_Presentation2_Traffic_Project_USC_Template.pptx');ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
print('SIZE',E.fromstring(z.read('ppt/presentation.xml')).find('p:sldSz',ns).attrib)
out=[]
for n in sorted([n for n in z.namelist() if __import__('re').match(r'ppt/slides/slide\d+.xml$',n)],key=lambda n:int(__import__('re').search(r'(\d+)\.xml',n)[1])):
 x=E.fromstring(z.read(n));sp=[]
 for shape in x.findall('.//p:spTree/*',ns):
  ts=shape.findall('.//a:t',ns)
  if ts:
   sp.append({'id':shape.find('.//p:cNvPr',ns).get('id'),'name':shape.find('.//p:cNvPr',ns).get('name'),'text':'\n'.join(t.text or '' for t in ts),'fonts':list(set(shape.xpath('.//a:latin/@typeface',namespaces=ns)))})
 out.append({'slide':n,'shapes':sp});print(n,json.dumps(sp,ensure_ascii=False))
pathlib.Path('06_reports/_qa/ppt_source/text.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
