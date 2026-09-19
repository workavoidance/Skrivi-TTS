"""Held-out clean document snippets through the production frozen worker."""
import sys,json,time,subprocess,io,re,statistics
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1]
texts=[
('en','Your appointment is on Friday at 10:45.\nBring the reference number 804219.'),
('nb','Bjørn og Åse møtest ved biblioteket.\nPrisen er 249,90 kroner, inkludert avgifter.'),
('nn','Me ønskjer å høyre kva du meiner.\nDu treng ikkje sende søknaden før måndag.'),
('mixed','Please open the attachment.\nVedlegget inneheld informasjon om møtet.')]
rows=[]
for lang,text in texts:
 for mode in ['clean','jpeg','dark']:
  font=ImageFont.truetype('C:/Windows/Fonts/calibri.ttf',28)
  image=Image.new('RGB',(900,135),'white');ImageDraw.Draw(image).multiline_text((24,20),text,font=font,fill='black',spacing=12)
  if mode=='dark':image=ImageOps.invert(image)
  if mode=='jpeg':
   b=io.BytesIO();image.save(b,format='JPEG',quality=85);image=Image.open(io.BytesIO(b.getvalue()))
  b=io.BytesIO();image.save(b,format='PNG');start=time.perf_counter()
  r=subprocess.run([str(ROOT/'dist/OCRWorker/OCRWorker.exe'),str(ROOT/'build/ocr-assets')],input=b.getvalue(),capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
  assert r.returncode==0,r.stdout
  actual=json.loads(r.stdout)['text'];expected=' '.join(text.split());actual=' '.join(actual.split())
  rows.append(dict(language=lang,mode=mode,expected=expected,actual=actual,exact=expected==actual,seconds=time.perf_counter()-start))
(ROOT/'docs/OCR_HOLDOUT.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('Held-out exact:',sum(x['exact'] for x in rows),'/',len(rows),'Median seconds:',statistics.median(x['seconds'] for x in rows))
for x in rows:
 if not x['exact']:print(x['language'],x['mode'],ascii(x['actual']))
