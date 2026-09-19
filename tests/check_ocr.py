"""Verify frozen OCR and DPI crop mapping without private captures."""
import json,os,sys,time,subprocess,tempfile,statistics,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap,QImage,QColor
from PySide6.QtCore import QRect,QPoint,Qt
from PySide6.QtTest import QTest
from screen_region import RegionOverlay
app=QApplication([])
for scale in (1,1.25,1.5,2):
 class Screen:
  def geometry(self):return QRect(-800,0,400,300)
  def grabWindow(self,_):
   p=QPixmap(round(400*scale),round(300*scale));p.fill(QColor('white'));p.setDevicePixelRatio(scale);return p
 overlay=RegionOverlay(Screen());found=[];overlay.selected.connect(found.append);overlay.show();app.processEvents()
 QTest.mousePress(overlay,Qt.MouseButton.LeftButton,pos=QPoint(40,40))
 QTest.mouseRelease(overlay,Qt.MouseButton.LeftButton,pos=QPoint(139,99))
 assert len(found)==1
 image=QImage.fromData(found[0]);assert image.width()==round(100*scale) and image.height()==round(60*scale),(scale,image.size())
 overlay.deleteLater()
print('Crop mapping passed at 100/125/150/200 percent, including negative monitor origin.')
results=[]
for path in sorted((ROOT/'build/ocr-screening').glob('*.png')):
 start=time.perf_counter()
 r=subprocess.run([str(ROOT/'dist/OCRWorker/OCRWorker.exe'),str(ROOT/'build/ocr-assets')],input=path.read_bytes(),capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
 assert r.returncode==0,r.stdout
 text=json.loads(r.stdout)['text'];assert text.strip()
 results.append(dict(image=path.name,seconds=time.perf_counter()-start,text=text))
# Empty and malformed input must not result in invented speech.
blank=QImage(300,200,QImage.Format.Format_RGB32);blank.fill(QColor('white'))
from PySide6.QtCore import QBuffer,QIODevice
b=QBuffer();b.open(QIODevice.OpenModeFlag.WriteOnly);blank.save(b,'PNG')
r=subprocess.run([str(ROOT/'dist/OCRWorker/OCRWorker.exe'),str(ROOT/'build/ocr-assets')],input=bytes(b.data()),capture_output=True,timeout=30)
assert json.loads(r.stdout)['text']==''
r=subprocess.run([str(ROOT/'dist/OCRWorker/OCRWorker.exe'),str(ROOT/'build/ocr-assets')],input=b'not an image',capture_output=True,timeout=30)
assert r.returncode!=0 and 'error' in json.loads(r.stdout)
with tempfile.TemporaryDirectory() as tmp:
 os.environ['SKRIVI_TTS_DATA']=tmp
 import main
 reader=main.Reader(app,preview=True)
 reader.show();app.processEvents();reader.grab().save(str(ROOT/'build/ocr-screening/reader-ui.png'))
 calls=[];reader.start_reading=lambda text,source:calls.append((text,source))
 reader.capture_generation=8;reader.ocr_received(7,'Stale text','');assert not calls
 reader.ocr_received(8,'A valid recognised paragraph.','');assert calls==[('A valid recognised paragraph.','Screen region')]
 reader.stop();reader.ocr_received(8,'Cancelled text','');assert len(calls)==1
 reader.finish_quit()
(ROOT/'docs/OCR_FROZEN_CHECKS.json').write_text(json.dumps(dict(results=results,median_seconds=statistics.median(x['seconds'] for x in results),checks=['DPI crop geometry','empty image','malformed image','stale result','cancelled result','reader dispatch']),ensure_ascii=False,indent=2),encoding='utf-8')
print('Frozen worker and reader dispatch checks passed. Median complete worker time:',statistics.median(x['seconds'] for x in results))
