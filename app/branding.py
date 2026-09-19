"""Skrivi-family orange speaker mark, distinct from the dictation icon."""
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QIcon,QPainter,QPen,QPixmap,QPolygonF

def speech_pixmap(size=256):
    pix=QPixmap(size,size);pix.fill(Qt.GlobalColor.transparent)
    p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size/100,size/100)
    color=QColor('#F05A24')
    p.setPen(Qt.PenStyle.NoPen);p.setBrush(color)
    p.drawRoundedRect(QRectF(12,37,20,26),5,5)
    p.drawPolygon(QPolygonF([QPointF(27,38),QPointF(49,20),QPointF(49,80),QPointF(27,62)]))
    pen=QPen(color,7);pen.setCapStyle(Qt.PenCapStyle.RoundCap);p.setPen(pen);p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(39,31,32,38),-60*16,120*16)
    p.drawArc(QRectF(35,15,55,70),-56*16,112*16)
    p.end();return pix

def speech_icon():
    icon=QIcon()
    for size in (16,20,24,32,48,64,128,256):icon.addPixmap(speech_pixmap(size))
    return icon
