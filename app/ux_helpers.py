"""Small shared desktop interactions; no speech or model changes."""

from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)


class WheelGuard(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(
            obj, (QComboBox, QAbstractSpinBox)
        ):
            parent = obj.parentWidget()
            while parent is not None:
                if isinstance(parent, QAbstractScrollArea):
                    bar = parent.verticalScrollBar()
                    delta = event.pixelDelta().y() or event.angleDelta().y()
                    bar.setValue(bar.value() - delta)
                    break
                parent = parent.parentWidget()
            event.accept()
            return True
        return False


def polish(root):
    app = QApplication.instance()
    if not hasattr(app, "_skrivi_wheel_guard"):
        app._skrivi_wheel_guard = WheelGuard(app)
        app.installEventFilter(app._skrivi_wheel_guard)
    for button in root.findChildren(QPushButton):
        button.setAutoDefault(False)
        button.setDefault(False)
        button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    for combo in root.findChildren(QComboBox):
        combo.setMinimumWidth(0)
        combo.setMaximumWidth(340)
        combo.setMinimumContentsLength(16)
        combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )


class Welcome(QDialog):
    def __init__(self, parent, product, marker, shortcuts, change, tr):
        super().__init__(parent)
        self.marker = Path(marker)
        self.setWindowTitle(product + " · " + tr("How to use"))
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(600, 530)
        self.setMinimumSize(460, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        icon = QLabel()
        icon.setPixmap(QApplication.windowIcon().pixmap(42, 42))
        root.addWidget(icon)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        body = QVBoxLayout(content)
        body.setSpacing(16)

        def add(value, role=None):
            label = QLabel(value)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            if role:
                label.setProperty("uiRole", role)
            body.addWidget(label)

        if product == "Skrivi Snakk":
            add(tr("Speak wherever you write"), "windowTitle")
            add(tr("Use your voice in emails, documents, messages and other apps."))
            add(tr("1. Click where you want your words to appear."))
            add(tr("2. Hold {shortcut} and speak.").format(shortcut=shortcuts[0]))
            add(tr("3. Release the key to insert your words."))
            add(
                tr(
                    "You do not need to open Snakk. "
                    "It stays available in the background."
                )
            )
            add(tr("Press Esc to cancel a dictation."), "secondary")
        else:
            add(tr("Listen to text anywhere"), "windowTitle")
            add(tr("Read text aloud from websites, documents, emails and other apps."))
            add(tr("1. Select the text you want to hear."))
            add(tr("2. Press {shortcut}.").format(shortcut=shortcuts[0]))
            add(
                tr(
                    "Lytt reads your selection aloud. "
                    "You do not need to copy it into this window."
                )
            )
            add(tr("Cannot select the text?"), "sectionTitle")
            add(
                tr(
                    "Press {shortcut}, then drag around the text on your screen."
                ).format(shortcut=shortcuts[1])
            )
            add(tr("Press Esc to stop reading."), "secondary")
        body.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        self.error = QLabel()
        self.error.setWordWrap(True)
        root.addWidget(self.error)
        self.tr = tr
        row = QHBoxLayout()
        start = QPushButton(tr("Get started"))
        start.setProperty("buttonRole", "primary")
        start.clicked.connect(self.accept)
        skip = QPushButton(tr("Skip introduction"))
        skip.clicked.connect(self.reject)
        row.addWidget(start)
        row.addWidget(skip)
        row.addStretch()
        root.addLayout(row)
        edit = QPushButton(tr("Change shortcuts"))
        edit.clicked.connect(lambda: (self.accept(), change()))
        root.addWidget(edit, 0, Qt.AlignmentFlag.AlignLeft)
        polish(self)
        self.finished.connect(self.remember)

    def remember(self, _result):
        try:
            self.marker.parent.mkdir(parents=True, exist_ok=True)
            self.marker.write_text("seen\n", encoding="utf-8")
        except OSError:
            # On a read-only profile, repeat the introduction next launch.
            pass


def show_welcome(owner, product, marker, shortcuts, change, tr, *, force=False):
    current = getattr(owner, "_welcome", None)
    if current is not None and current.isVisible():
        current.raise_()
        return
    if force or not Path(marker).exists():
        owner._welcome = Welcome(owner, product, marker, shortcuts, change, tr)
        owner._welcome.show()
