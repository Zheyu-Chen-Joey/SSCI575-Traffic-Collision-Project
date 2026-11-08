from pathlib import Path
import pypdfium2 as pdf
from PIL import Image
r=Path('06_reports/_qa/speaking_script');d=pdf.PdfDocument(r/'script.pdf');print('Pages',len(d));out=Image.new('RGB',(1200,600*((len(d)+2)//3)),'white')
for i in range(len(d)):
 im=d[i].render(scale=1.5).to_pil();im.save(r/f'page-{i+1}.png');im.thumbnail((400,600));out.paste(im,((i%3)*400,(i//3)*600))
out.save(r/'contact.png')
