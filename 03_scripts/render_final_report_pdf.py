from pathlib import Path
import pypdfium2 as pdf
from PIL import Image
r=Path('06_reports/_qa/final_project_report');d=pdf.PdfDocument(r/'report.pdf');print('Pages',len(d));o=Image.new('RGB',(1600,550*((len(d)+3)//4)),'white')
for i in range(len(d)):
 im=d[i].render(scale=1.5).to_pil();im.save(r/f'page-{i+1}.png');im.thumbnail((400,550));o.paste(im,((i%4)*400,(i//4)*550))
o.save(r/'contact.png')
