"""Frozen monitor selection; images stay in memory and never touch the clipboard."""
from PySide6.QtCore import Qt,QRect,QPoint,QBuffer,QIODevice,Signal
from PySide6.QtGui import QPainter,QPen,QColor,QCursor
from PySide6.QtWidgets import QWidget,QApplication

class RegionOverlay(QWidget):
    selected=Signal(bytes)
    cancelled=Signal()
    def __init__(self,screen):
        super().__init__(None,Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.Tool)
        self.image=screen.grabWindow(0)
        if self.image.isNull():raise RuntimeError('Windows could not capture this screen.')
        self.setGeometry(screen.geometry());self.setCursor(Qt.CursorShape.CrossCursor)
        self.anchor=None;self.area=QRect();self.done=False
        self.setMouseTracking(True);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    def paintEvent(self,event):
        p=QPainter(self);p.drawPixmap(self.rect(),self.image)
        p.fillRect(self.rect(),QColor(0,0,0,90))
        if not self.area.isNull():
            p.save();p.setClipRect(self.area);p.drawPixmap(self.rect(),self.image);p.restore()
            p.setPen(QPen(QColor('#ff9d42'),2));p.drawRect(self.area)
        p.setPen(QColor('white'));p.drawText(24,32,'Drag around one paragraph or column. Escape cancels.')
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.anchor=event.position().toPoint()
        elif event.button()==Qt.MouseButton.RightButton:self.abort()
    def mouseMoveEvent(self,event):
        if self.anchor is not None:
            self.area=QRect(self.anchor,event.position().toPoint()).normalized().intersected(self.rect());self.update()
    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton or self.anchor is None:return
        self.area=QRect(self.anchor,event.position().toPoint()).normalized().intersected(self.rect())
        if self.area.width()<8 or self.area.height()<8:self.abort();return
        sx=self.image.width()/self.width();sy=self.image.height()/self.height()
        pixels=QRect(round(self.area.x()*sx),round(self.area.y()*sy),round(self.area.width()*sx),round(self.area.height()*sy))
        crop=self.image.copy(pixels);buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        crop.save(buffer,'PNG');payload=bytes(buffer.data())
        self.done=True;self.close();self.image=None;self.selected.emit(payload)
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:self.abort()
    def abort(self):
        if self.done:return
        self.done=True;self.close();self.image=None;self.cancelled.emit()
