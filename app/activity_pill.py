"""Non-activating, theme-aware reading status anchored to the invoking monitor."""
from PySide6.QtCore import Qt,QTimer,QRectF,Signal,QPropertyAnimation
from PySide6.QtGui import QPainter,QPen,QColor,QFont
from PySide6.QtWidgets import QWidget,QLabel,QPushButton,QHBoxLayout,QVBoxLayout,QApplication
from theme import theme_colors
from i18n import tr

class ActivityPill(QWidget):
    cancelled=Signal()
    def __init__(self):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName('Reading progress')
        self.enabled=True
        self.screen_target=None;self.angle=0;self.animating=True
        self.setMinimumWidth(300);self.setMaximumWidth(480)
        row=QHBoxLayout(self);row.setContentsMargins(56,17,18,17);row.setSpacing(18)
        copy=QVBoxLayout();copy.setSpacing(4)
        self.title=QLabel();self.title.setFont(QFont('Segoe UI',11,QFont.Weight.DemiBold))
        self.subtitle=QLabel();self.subtitle.setFont(QFont('Segoe UI',9));self.subtitle.setWordWrap(True)
        copy.addWidget(self.title);copy.addWidget(self.subtitle);row.addLayout(copy,1)
        self.cancel_button=QPushButton('Esc · Cancel');self.cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor);self.cancel_button.clicked.connect(self.cancelled)
        row.addWidget(self.cancel_button)
        self.timer=QTimer(self);self.timer.setInterval(40);self.timer.timeout.connect(self.tick)
        self.fade=QPropertyAnimation(self,b'windowOpacity',self);self.fade.setDuration(120)
        self.dismiss=QTimer(self);self.dismiss.setSingleShot(True);self.dismiss.timeout.connect(self.hide)
        QApplication.instance().paletteChanged.connect(self.retheme);self.retheme()
    def retheme(self,*_):
        self.colors=theme_colors(QApplication.palette());c=self.colors
        self.title.setStyleSheet('background:transparent;color:'+c['text'])
        self.subtitle.setStyleSheet('background:transparent;color:'+c['muted'])
        self.cancel_button.setStyleSheet('QPushButton {background:'+c['surface_muted']+';color:'+c['text']+';border:1px solid '+c['border']+';border-radius:10px;padding:7px 10px;} QPushButton:hover {border-color:'+c['accent']+';}')
        self.update()
    def present(self,title,subtitle='',screen=None,active=True,error=False):
        if not self.enabled:return
        self.dismiss.stop();self.screen_target=screen or self.screen_target or QApplication.primaryScreen()
        self.title.setText(tr(title));self.subtitle.setText(tr(subtitle));self.subtitle.setVisible(bool(subtitle))
        self.cancel_button.setText(tr('Esc · Stop' if title=='Reading aloud' else 'Esc · Cancel' if active else 'Dismiss'))
        self.animating=active and title!='Reading aloud';self.error=error
        self.adjustSize()
        area=self.screen_target.availableGeometry()
        self.move(max(area.left(),area.center().x()-self.width()//2),max(area.top(),area.bottom()-self.height()-64))
        opening=not self.isVisible()
        self.show()
        if opening:
            self.fade.stop();self.fade.setStartValue(0.0);self.fade.setEndValue(1.0);self.fade.start()
        if self.animating:self.timer.start()
        else:self.timer.stop()
        if not active:self.dismiss.start(8000 if error else 1200)
        self.update()
    def tick(self):self.angle=(self.angle+12)%360;self.update()
    def hideEvent(self,event):self.timer.stop();super().hideEvent(event)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);c=self.colors
        rect=QRectF(self.rect()).adjusted(1,1,-1,-1)
        p.setBrush(QColor(c['surface']));p.setPen(QPen(QColor(c['border']),1));p.drawRoundedRect(rect,20,20)
        color=c['error'] if getattr(self,'error',False) else c['accent']
        p.setPen(QPen(QColor(color),3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        circle=QRectF(23,self.height()/2-10,20,20)
        if self.animating:p.drawArc(circle,-self.angle*16,260*16)
        else:
            p.drawLine(25,int(self.height()/2-4),25,int(self.height()/2+4))
            p.drawLine(32,int(self.height()/2-9),32,int(self.height()/2+9))
            p.drawLine(39,int(self.height()/2-6),39,int(self.height()/2+6))
