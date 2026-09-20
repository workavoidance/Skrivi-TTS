"""Shared Skrivi navigation patterns around Lytt's reading workflow."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QTextEdit,
    QWidget,
    QTabWidget,
    QTreeWidget,
    QProgressBar,
    QScrollArea,
    QFrame,
)
import os
from core import VERSION, STORE_BUILD, DATA, KOKORO_VOICES
from i18n import tr
from windows_reader import shortcut_parts


class ShortcutButton(QPushButton):
    def __init__(self, value, changed):
        super().__init__(tr("Change shortcut…"))
        self.setProperty("sourceText", "Change shortcut…")
        self.value = value
        self.changed = changed
        self.capturing = False
        self.clicked.connect(self.capture)

    def capture(self):
        self.capturing = True
        self.setText(tr("Press a key or combination…"))
        self.grabKeyboard()

    def finish(self):
        self.releaseKeyboard()
        self.capturing = False
        self.setText(tr("Change shortcut…"))

    def hideEvent(self, event):
        if self.capturing:
            self.finish()
        super().hideEvent(event)

    def keyPressEvent(self, event):
        if not self.capturing:
            return super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Escape:
            self.finish()
            return
        if event.key() in (
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
        ):
            return
        value = QKeySequence(event.keyCombination()).toString(
            QKeySequence.SequenceFormat.PortableText
        )
        try:
            shortcut_parts(value)
        except ValueError:
            self.setText(tr("Use Ctrl or Alt with a letter, Space or F6–F12."))
            return
        self.finish()
        self.changed(value)


def text(value, role=None):
    label = QLabel(value)
    label.setWordWrap(True)
    if role:
        label.setProperty("uiRole", role)
    return label


def link(label, url):
    button = QPushButton(label)
    button.clicked.connect(lambda: os.startfile(url))
    return button


def build_reader(self):
    self.resize(760, 680)
    self.setMinimumSize(640, 520)
    outer = QVBoxLayout(self)
    outer.setContentsMargins(24, 22, 24, 18)
    outer.setSpacing(14)
    outer.addWidget(text("Skrivi Lytt", "eyebrow"))
    outer.addWidget(text("Read aloud", "windowTitle"))
    self.tabs = QTabWidget()
    self.tabs.tabBar().hide()
    outer.addWidget(self.tabs, 1)
    read = QWidget()
    self.tabs.addTab(read, "Read")
    layout = QVBoxLayout(read)
    row = QHBoxLayout()
    row.addWidget(text("Reading language"))
    self.language = QComboBox()
    for key, name in [
        ("auto", "Automatic"),
        ("no", "Norwegian Bokmål"),
        ("en", "English"),
    ]:
        self.language.addItem(name, key)
    row.addWidget(self.language)
    layout.addLayout(row)
    voices = QHBoxLayout()
    voices.addWidget(text("English voice"))
    self.voice = QComboBox()
    for key, name in KOKORO_VOICES.items():
        self.voice.addItem(name, key)
    voices.addWidget(self.voice)
    voices.addWidget(text("Reading speed"))
    self.speed = QDoubleSpinBox()
    self.speed.setRange(0.5, 2)
    self.speed.setSingleStep(0.1)
    self.speed.setSuffix(" ×")
    self.speed.setValue(1)
    voices.addWidget(self.speed)
    layout.addLayout(voices)
    self.route_label = text("")
    layout.addWidget(self.route_label)
    self.text = QTextEdit()
    self.text.setAcceptRichText(False)
    self.text.setMinimumHeight(120)
    self.text.setAccessibleName("Text to read")
    layout.addWidget(self.text, 1)
    row = QHBoxLayout()
    for attr, label, callback in [
        ("read_button", "Read aloud", self.read_editor),
        ("stop_button", "Stop", self.stop),
        ("sample_button", "Try a sample", self.sample),
        ("save_button", "Save audio…", self.save_audio),
    ]:
        button = QPushButton(label)
        setattr(self, attr, button)
        button.clicked.connect(callback)
        row.addWidget(button)
    self.read_button.setProperty("uiRole", "primary")
    self.stop_button.setEnabled(False)
    self.save_button.setEnabled(False)
    layout.addLayout(row)
    self.region_button = QPushButton("Read screen region")
    self.region_button.clicked.connect(self.capture_region)
    layout.addWidget(self.region_button)
    self.shortcut_hint = text("")
    layout.addWidget(self.shortcut_hint)
    layout.addWidget(
        text("Closing this window keeps Skrivi Lytt in the tray. Text is not saved.")
    )
    self.settings_button = QPushButton("Settings")
    self.settings_button.clicked.connect(self.open_settings)
    outer.addWidget(self.settings_button)
    self.status_label = text("Ready.")
    outer.addWidget(self.status_label)
    self.error_actions = QWidget()
    error_layout = QHBoxLayout(self.error_actions)
    self.retry_button = QPushButton("Retry")
    self.retry_button.clicked.connect(
        lambda: self.retry_action() if self.retry_action else None
    )
    self.error_settings = QPushButton("Settings")
    self.error_settings.clicked.connect(self.open_settings)
    self.details_button = QPushButton("Details")
    self.details_button.clicked.connect(
        lambda: self.error_detail.setVisible(not self.error_detail.isVisible())
    )
    for b in (self.retry_button, self.error_settings, self.details_button):
        error_layout.addWidget(b)
    self.error_detail = text("")
    self.error_detail.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
    )
    outer.addWidget(self.error_actions)
    outer.addWidget(self.error_detail)
    self.error_actions.hide()
    self.error_detail.hide()
    self.retry_action = None
    self.progress = QProgressBar()
    self.progress.setRange(0, 0)
    self.progress.setMaximumHeight(4)
    self.progress.setTextVisible(False)
    self.progress.hide()
    outer.addWidget(self.progress)
    self.settings_dialog = QDialog(self)
    self.settings_dialog.setWindowTitle("Skrivi Lytt · Settings")
    self.settings_dialog.resize(760, 680)
    self.settings_dialog.setMinimumSize(640, 520)
    root = QVBoxLayout(self.settings_dialog)
    root.setContentsMargins(24, 22, 24, 18)
    header = QHBoxLayout()
    copy = QVBoxLayout()
    copy.addWidget(text("Skrivi Lytt", "eyebrow"))
    copy.addWidget(text("Settings", "windowTitle"))
    copy.addWidget(text("Choose how Skrivi Lytt reads, looks and starts.", "secondary"))
    header.addLayout(copy, 1)
    icon = QLabel()
    icon.setPixmap(self.windowIcon().pixmap(46, 46))
    header.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
    root.addLayout(header)
    self.settings_error = text("")
    self.settings_error.hide()
    root.addWidget(self.settings_error)
    self.settings_tabs = QTabWidget()
    root.addWidget(self.settings_tabs)
    pages = []
    for name in ("General", "Shortcuts", "Models", "Privacy", "About"):
        page = QWidget()
        page.setObjectName("settingsPage")
        box = QVBoxLayout(page)
        box.setSpacing(14)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.settings_tabs.addTab(scroll, name)
        pages.append(box)
    general, shortcuts, models, privacy, about = pages
    self.ui_language = QComboBox()
    for label, key in [
        ("Automatic (Windows display language)", "auto"),
        ("English", "en"),
        ("Norsk bokmål", "nb"),
    ]:
        self.ui_language.addItem(label, key)

    def settings_card(title):
        frame = QFrame()
        frame.setProperty("uiRole", "card")
        box = QVBoxLayout(frame)
        box.setContentsMargins(18, 16, 18, 17)
        box.addWidget(text(title, "sectionTitle"))
        general.addWidget(frame)
        return box

    reading = settings_card("Reading")
    self.fallback = QComboBox()
    self.fallback.addItem("Norwegian Bokmål", "no")
    self.fallback.addItem("English", "en")
    self.layout_mode = QComboBox()
    self.layout_mode.addItem("Paragraph / single column", 6)
    self.layout_mode.addItem("Automatic page layout (columns)", 3)
    form = QFormLayout()
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    form.addRow("When detection is uncertain", self.fallback)
    form.addRow("Image layout", self.layout_mode)
    reading.addLayout(form)
    reading.addWidget(
        text(
            "For columns, select the main text without shared headings or footers.",
            "secondary",
        )
    )
    application = settings_card("Application")
    form = QFormLayout()
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    form.addRow("Interface language", self.ui_language)
    application.addLayout(form)
    self.startup = QCheckBox("Start quietly in the tray when I sign in")
    application.addWidget(self.startup)
    self.overlay = QCheckBox("Show activity indicator")
    application.addWidget(self.overlay)
    if STORE_BUILD:
        application.addWidget(
            link("Manage startup in Windows Settings", "ms-settings:startupapps")
        )
    general.addStretch()
    self.shortcut_label = text("")
    self.region_shortcut_label = text("")
    self.shortcut_button = ShortcutButton(
        self.preferences["hotkey"], self.change_shortcut
    )
    self.region_shortcut_button = ShortcutButton(
        self.preferences["region_hotkey"], self.change_region_shortcut
    )
    for title, value, button, reset in [
        (
            "Selected-text shortcut",
            self.shortcut_label,
            self.shortcut_button,
            lambda: self.change_shortcut("Ctrl+Alt+Space"),
        ),
        (
            "Screen-region shortcut",
            self.region_shortcut_label,
            self.region_shortcut_button,
            lambda: self.change_region_shortcut("Ctrl+Alt+Shift+Space"),
        ),
    ]:
        shortcuts.addWidget(text(title, "sectionTitle"))
        row = QHBoxLayout()
        row.addWidget(value)
        row.addWidget(button)
        b = QPushButton("Restore default")
        b.clicked.connect(reset)
        row.addWidget(b)
        shortcuts.addLayout(row)
    shortcuts.addWidget(
        text(
            "Esc cancels active work. Keep Right Ctrl or Left Ctrl + Windows for Skrivi Snakk. Avoid Ctrl + Alt as its dictation shortcut when using Lytt."
        )
    )
    shortcuts.addStretch()
    self.model_table = QTreeWidget()
    self.model_table.setColumnCount(3)
    self.model_table.setHeaderLabels(["Model", "Size", "Availability"])
    self.model_table.setRootIsDecorated(False)
    self.model_table.setColumnWidth(0, 290)
    models.addWidget(self.model_table)
    row = QHBoxLayout()
    for attr, label, callback in [
        ("download_button", "Download model", lambda: self.model_action(False)),
        ("import_button", "Locate existing files…", lambda: self.model_action(True)),
        ("cancel_download", "Cancel download", self.library_cancel.set),
    ]:
        button = QPushButton(label)
        setattr(self, attr, button)
        button.clicked.connect(callback)
        row.addWidget(button)
    self.cancel_download.setEnabled(False)
    models.addLayout(row)
    self.verify_button = QPushButton("Verify files")
    self.verify_button.clicked.connect(self.verify_models)
    models.addWidget(self.verify_button)
    self.download_status = text("Two local models, kept through updates.")
    models.addWidget(self.download_status)
    self.advanced_button = QPushButton("Advanced model details")
    models.addWidget(self.advanced_button)
    self.model_folder = link("Open model folder", str(DATA / "models"))
    self.model_folder.hide()
    self.advanced_button.clicked.connect(
        lambda: self.model_folder.setVisible(not self.model_folder.isVisible())
    )
    models.addWidget(self.model_folder)
    for heading, body in [
        (
            "Your words stay yours.",
            "Reading and screen recognition happen on this PC. No account, telemetry or cloud speech service.",
        ),
        (
            "Selection and screen capture",
            "Reading selected text may briefly use and restore the clipboard. Screen-region images are processed in memory and are not saved.",
        ),
        (
            "Audio and saved files",
            "Temporary speech audio is removed on normal exit. Save audio creates a file only when you choose to save it. Other apps may save or sync your text.",
        ),
    ]:
        privacy.addWidget(text(heading, "sectionTitle"))
        privacy.addWidget(text(body))
    privacy.addWidget(
        link(
            "Read full privacy details",
            "https://github.com/workavoidance/Skrivi-TTS#updates-and-privacy",
        )
    )
    privacy.addStretch()
    about.addWidget(text("Skrivi Lytt " + VERSION + " · Test release", "sectionTitle"))
    about.addWidget(text("Local reading. Part of the Skrivi family."))
    self.update_button = QPushButton("Check for updates")
    self.update_button.clicked.connect(self.check_updates)
    about.addWidget(self.update_button)
    for label, url in [
        ("Release notes", "https://github.com/workavoidance/Skrivi-TTS/releases"),
        ("Help", "https://skrivi.no/help/"),
        ("Give feedback", "https://github.com/workavoidance/Skrivi-TTS/issues"),
        ("Source code", "https://github.com/workavoidance/Skrivi-TTS"),
        (
            "Third-party licences",
            "https://github.com/workavoidance/Skrivi-TTS/blob/main/THIRD_PARTY_NOTICES.md",
        ),
        ("Explore Skrivi Snakk", "https://skrivi.no/dictation/"),
    ]:
        about.addWidget(link(label, url))
    about.addStretch()
    root.addWidget(text("Changes are saved automatically"))
    footer = QHBoxLayout()
    footer.addStretch()
    close = QPushButton("Close")
    close.clicked.connect(self.settings_dialog.hide)
    footer.addWidget(close)
    root.addLayout(footer)
    for widget, name in [
        (self.language, "Reading language"),
        (self.voice, "English voice"),
        (self.speed, "Reading speed"),
        (self.ui_language, "Interface language"),
        (self.fallback, "When detection is uncertain"),
        (self.layout_mode, "Image layout"),
    ]:
        widget.setAccessibleName(name)
    self.language.currentIndexChanged.connect(self.language_changed)
    self.text.textChanged.connect(self.update_route)
    self.voice.currentIndexChanged.connect(self.save_preferences)
    self.speed.valueChanged.connect(self.save_preferences)
    self.fallback.currentIndexChanged.connect(self.save_preferences)
    self.layout_mode.currentIndexChanged.connect(self.save_preferences)
    self.ui_language.currentIndexChanged.connect(self.change_ui_language)
    self.startup.toggled.connect(self.change_startup)
    self.overlay.toggled.connect(self.save_preferences)
