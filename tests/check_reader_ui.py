"""Review actual reader/pill rendering, state transitions and focused model list."""
import sys,os,tempfile,json,ctypes
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette,QColor
from PySide6.QtCore import Qt
from theme import application_stylesheet
from i18n import configure
app=QApplication([]);out=root/'build/reader-04-review';out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
 os.environ['SKRIVI_TTS_DATA']=tmp
 import main
 reader=main.Reader(app,preview=True)
 assert {m['id'] for m in reader.models}=={'piper-talesyntese','kokoro-v1.0-onnx'}
 reader.capture_generation=5;reader.cancel.clear()
 foreground=ctypes.windll.user32.GetForegroundWindow()
 base=QPalette(app.palette())
 for mode in ('light','dark'):
  palette=QPalette(base)
  if mode=='dark':
   for role,color in [(QPalette.ColorRole.Window,'#202020'),(QPalette.ColorRole.Base,'#282828'),(QPalette.ColorRole.AlternateBase,'#303030'),(QPalette.ColorRole.WindowText,'#f4f4f4'),(QPalette.ColorRole.Text,'#f4f4f4'),(QPalette.ColorRole.ButtonText,'#f4f4f4'),(QPalette.ColorRole.PlaceholderText,'#bcbcbc'),(QPalette.ColorRole.Mid,'#555555'),(QPalette.ColorRole.Midlight,'#666666')]:palette.setColor(role,QColor(color))
  app.setPalette(palette);app.setStyleSheet(application_stylesheet(palette))
  reader.ensurePolished();reader.grab().save(str(out/(mode+'-reader.png')))
  for stage in ('starting','loading','generating','playing'):
   reader.show_stage(5,stage);app.processEvents();reader.pill.grab().save(str(out/(mode+'-'+stage+'.png')))
  assert ctypes.windll.user32.GetForegroundWindow()==foreground,'Pill stole focus'
 reader.show_stage(4,'loading');assert reader.pill.title.text()!='Loading voice…'
 reader.stop();assert not reader.pill.isVisible();assert reader.escape_hotkeys.current is None
 reader.show_stage(5,'loading');assert not reader.pill.isVisible(),'Cancelled event reopened pill'
 reader.ui_language.setCurrentIndex(reader.ui_language.findData('nb'));assert reader.read_button.text()=='Les høyt'
 reader.ui_language.setCurrentIndex(reader.ui_language.findData('en'));assert reader.read_button.text()=='Read aloud'
 assert reader.layout_mode.findData(3)>=0
 reader.busy=True;reader.show_error('A deliberate test failure.');reader.completed(None);assert reader.pill.isVisible(),'Completion hid error'
 reader.stop();reader.finish_quit()
print('Pill stages, light/dark rendering, no focus theft, stale/cancelled events, error persistence, English/Bokmal switching and two-model UI passed.')
