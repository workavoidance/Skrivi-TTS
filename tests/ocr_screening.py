"""Synthetic printed-text screen. Run with build/ocr-env Python; no network used."""
import json,time,re,statistics,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import tesserocr
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ocr-screening';OUT.mkdir(exist_ok=True)
def distance(a,b):
 row=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  nxt=[i]
  for j,y in enumerate(b,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
  row=nxt
 return row[-1]
def normalize(s):return ' '.join(s.split())
passages={
'en':['The train leaves at 14:35. Please arrive ten minutes early.','Sarah paid 125.50 kroner for three books and a newspaper.','Read the first paragraph, then continue to the next page.'],
'nb':['Toget går klokken 14:35. Møt opp ti minutter før avgang.','Øyvind kjøpte tre bøker og ei avis for 125,50 kroner.','Les det første avsnittet og fortsett på neste side.'],
'nn':['Toget går klokka 14:35. Møt opp ti minutt før avgang.','Eg kjøpte tre bøker og ei avis for 125,50 kroner.','Ho ønskjer å lese teksten. Dei kjem ikkje før i morgon.'],
'mixed':['Møtet startar klokka 09:30. Please bring your notes.','Åse and Øyvind will arrive on Tuesday, 22 September.','Dokumentet heiter Annual Report. Les side 12 til 15.']}
results=[]
t0=time.perf_counter()
api=tesserocr.PyTessBaseAPI(path=str(ROOT/'build/ocr-assets'),lang='nor+eng',psm=6)
init=time.perf_counter()-t0
for lang,lines in passages.items():
 for family in ['arial.ttf','times.ttf']:
  for size in [18,30,44]:
   font=ImageFont.truetype('C:/Windows/Fonts/'+family,size)
   w=int(max(font.getlength(x) for x in lines))+48
   im=Image.new('RGB',(w,3*(size+14)+32),'white');draw=ImageDraw.Draw(im)
   for n,line in enumerate(lines):draw.text((24,12+n*(size+14)),line,font=font,fill='black')
   name=f'{lang}-{family}-{size}';im.save(OUT/(name+'.png'))
   runs=[]
   for _ in range(3):
    start=time.perf_counter();api.SetImage(im);actual=api.GetUTF8Text();runs.append(time.perf_counter()-start)
   expected=normalize(' '.join(lines));actual=normalize(actual)
   results.append(dict(id=name,language=lang,expected=expected,actual=actual,character_errors=distance(expected,actual),word_errors=distance(expected.split(),actual.split()),seconds=runs))
api.End()
report=dict(engine=tesserocr.tesseract_version(),settings=dict(languages='nor+eng',psm=6),initialization_seconds=init,results=results)
(ROOT/'docs/OCR_SCREENING.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Samples:',len(results),'Exact:',sum(x['character_errors']==0 for x in results),'CER:',sum(x['character_errors'] for x in results)/sum(len(x['expected']) for x in results),'Median seconds:',statistics.median(t for x in results for t in x['seconds']))
for x in results:
 if x['character_errors']:print(x['id'],repr(x['actual']))
