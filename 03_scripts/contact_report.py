from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
files=sorted(Path('06_reports/_qa/final_report').glob('page-*.png'));sheet=Image.new('RGB',(1200, int((len(files)+2)//3)*590),'#ccc')
for k,f in enumerate(files):
 im=Image.open(f);im.thumbnail((390,550));x=(k%3)*400;y=(k//3)*590;sheet.paste(im,(x,y+25));ImageDraw.Draw(sheet).text((x+5,y+5),f.stem,fill='black')
sheet.save('06_reports/_qa/contact.png')
