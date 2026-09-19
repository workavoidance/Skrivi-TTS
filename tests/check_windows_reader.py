import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from PySide6.QtWidgets import QApplication,QTextEdit
from PySide6.QtCore import QMimeData
from PySide6.QtTest import QTest
from main import Reader
from windows_reader import user32,Hotkeys
app=QApplication([])
reader=Reader(app,preview=True)
source=QTextEdit();source.setWindowTitle('Skrivi selection verification');source.setPlainText('A selected English sentence for the reader.');source.selectAll();source.show();source.activateWindow();source.setFocus();QTest.qWait(500)
received=[];reader.start_reading=lambda text,origin:received.append((text,origin))
reader.capture_selection()
for _ in range(100):
 QTest.qWait(50)
 if received:break
assert received and received[0][0]=='A selected English sentence for the reader.',(received,reader.status_label.text())
print('PASS native selected text capture')
clipboard=app.clipboard();old=clipboard.mimeData();saved=QMimeData()
for fmt in old.formats():saved.setData(fmt,old.data(fmt))
try:
 clipboard.setText('Clipboard preservation marker');received.clear();reader.capturing=True;reader.capture_generation+=1
 reader.selection_received('',(user32.GetForegroundWindow(),reader.capture_generation))
 for _ in range(80):
  QTest.qWait(50)
  if received:break
 assert received and received[0][0]=='A selected English sentence for the reader.',(received,reader.status_label.text())
 assert clipboard.text()=='Clipboard preservation marker',clipboard.text()
 print('PASS copy fallback and clipboard restoration')
finally:
 if clipboard.text()=='Clipboard preservation marker':clipboard.setMimeData(saved)
reader.capture_generation+=1;before=len(received);reader.selection_received('stale selection',(user32.GetForegroundWindow(),reader.capture_generation-1));assert len(received)==before
print('PASS stale capture cancellation')
reader.temp.cleanup();source.close()
