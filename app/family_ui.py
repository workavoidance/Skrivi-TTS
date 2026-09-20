"""Shared Skrivi navigation patterns around Lytt's reading workflow."""

from PySide6.QtCore import Qt, Signal
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
    QGridLayout,
)
import os
from core import VERSION, STORE_BUILD, DATA, KOKORO_VOICES
from i18n import tr
from windows_reader import shortcut_parts


class ShortcutButton(QPushButton):
    capture_started = Signal()
    capture_finished = Signal()

    def __init__(self, value, changed):
        super().__init__(tr("Change shortcut…"))
        self.setProperty("sourceText", "Change shortcut…")
        self.value = value
        self.changed = changed
        self.capturing = False
        self.clicked.connect(self.capture)

    def capture(self):
        if self.capturing:
            return
        self.capturing = True
        self.capture_started.emit()
        self.dialog = QDialog(self.window())
        self.dialog.setWindowTitle(tr("Change shortcut…"))
        self.dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.dialog.setMinimumWidth(420)
        layout = QVBoxLayout(self.dialog)
        self.prompt = text(tr("Press a key or combination…"))
        layout.addWidget(self.prompt)
        cancel = QPushButton(tr("Cancel"))
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.finish)
        layout.addWidget(cancel)
        self.dialog.rejected.connect(self.finish)
        self.dialog.show()
        self.grabKeyboard()

    def finish(self):
        if not self.capturing:
            return
        self.releaseKeyboard()
        self.capturing = False
        if hasattr(self, "dialog"):
            self.dialog.hide()
        self.setText(tr("Change shortcut…"))
        self.capture_finished.emit()

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
            self.prompt.setText(tr("Use Ctrl or Alt with a letter, Space or F6–F12."))
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
    outer.addWidget(text("Skrivi Lytt", "pageTitle"))
    self.tabs = QTabWidget()
    self.tabs.tabBar().hide()
    outer.addWidget(self.tabs, 1)
    read = QWidget()
    read_scroll = QScrollArea()
    read_scroll.setWidgetResizable(True)
    read_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    read_scroll.setWidget(read)
    self.tabs.addTab(read_scroll, "Read")
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
    row.addStretch()
    layout.addLayout(row)
    self.anywhere = text("", "sectionTitle")
    layout.addWidget(self.anywhere)
    layout.addWidget(
        text(
            "Select text in any app, then use the shortcut. You do not need to copy it here."
        )
    )
    self.screen_hint = text("")
    layout.addWidget(self.screen_hint)
    shortcut_actions = QHBoxLayout()
    self.change_shortcuts_button = QPushButton("Change shortcuts")
    self.change_shortcuts_button.clicked.connect(self.open_shortcuts)
    self.how_button = QPushButton("How to use")
    self.how_button.clicked.connect(lambda: self.introduction(force=True))
    shortcut_actions.addWidget(self.change_shortcuts_button)
    shortcut_actions.addWidget(self.how_button)
    shortcut_actions.addStretch()
    layout.addLayout(shortcut_actions)
    layout.addWidget(text("Or paste or type text below", "secondary"))
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
    self.route_label.hide()
    self.text = QTextEdit()
    self.text.setAcceptRichText(False)
    self.text.setMinimumHeight(120)
    self.text.setAccessibleName("Text to read")
    layout.addWidget(self.text, 1)
    row = QHBoxLayout()
    for attr, label, callback in [
        ("read_button", "Read aloud", self.read_editor),
        ("stop_button", "Stop", self.stop),
        ("save_button", "Save audio…", self.save_audio),
    ]:
        button = QPushButton(label)
        setattr(self, attr, button)
        button.clicked.connect(callback)
        row.addWidget(button)

    self.stop_button.setEnabled(False)
    self.save_button.setEnabled(False)
    layout.addLayout(row)
    self.region_button = QPushButton("Read screen region")
    self.region_button.clicked.connect(self.capture_region)
    layout.addWidget(self.region_button, 0, Qt.AlignmentFlag.AlignLeft)
    self.shortcut_hint = text("")
    self.shortcut_hint.hide()
    layout.addWidget(
        text("Closing this window keeps Skrivi Lytt in the tray. Text is not saved.")
    )
    self.settings_button = QPushButton("Settings")
    self.settings_button.clicked.connect(self.open_settings)
    outer.addWidget(self.settings_button, 0, Qt.AlignmentFlag.AlignLeft)
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
    reading.addWidget(
        text(
            "With Automatic reading language, Lytt detects the language of selected or pasted text. Choose a fallback for uncertain text.",
            "secondary",
        )
    )
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
    for button in (self.shortcut_button, self.region_shortcut_button):
        button.capture_started.connect(self.pause_shortcuts)
        button.capture_finished.connect(self.resume_shortcuts)
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
        heading = QHBoxLayout()
        heading.addWidget(text(title, "sectionTitle"))
        heading.addWidget(value)
        heading.addStretch()
        shortcuts.addLayout(heading)
        row = QHBoxLayout()
        row.addWidget(button)
        b = QPushButton("Restore default")
        b.clicked.connect(reset)
        row.addWidget(b)
        row.addStretch()
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
    models.addWidget(self.verify_button, 0, Qt.AlignmentFlag.AlignLeft)
    self.download_status = text("Two local models, kept through updates.")
    models.addWidget(self.download_status)
    self.model_folder = link("Open model folder", str(DATA / "models"))
    models.addWidget(self.model_folder, 0, Qt.AlignmentFlag.AlignLeft)

    def info_card(heading, body, quiet=True):
        frame = QFrame()
        frame.setProperty("uiRole", "quietCard" if quiet else "card")
        contents = QVBoxLayout(frame)
        contents.setContentsMargins(18, 16, 18, 16)
        contents.addWidget(text(heading, "sectionTitle"))
        contents.addWidget(text(body, "secondary"))
        return frame

    privacy.addWidget(text("Your words stay yours.", "pageTitle"))
    facts = QGridLayout()
    for index, (heading, body) in enumerate(
        [
            (
                "Processed on this PC",
                "Reading and screen recognition happen on this PC. No account, telemetry or cloud speech service.",
            ),
            (
                "Selection and screen capture",
                "Reading selected text may briefly use and restore the clipboard. Screen-region images are processed in memory and are not saved.",
            ),
            (
                "Audio and saved files",
                "Temporary speech audio is removed on normal exit. Save audio creates a file only when you choose to save it.",
            ),
            (
                "Works offline after setup",
                "Installed voices and screen recognition work without an internet connection.",
            ),
        ]
    ):
        facts.addWidget(info_card(heading, body), index // 2, index % 2)
    privacy.addLayout(facts)
    privacy.addWidget(
        info_card(
            "One important boundary",
            "Other apps may save or sync your text according to their own settings.",
            False,
        )
    )
    privacy.addWidget(
        link(
            "Read full privacy details",
            "https://github.com/workavoidance/Skrivi-TTS#updates-and-privacy",
        ),
        0,
        Qt.AlignmentFlag.AlignLeft,
    )
    privacy.addStretch()
    heading = QHBoxLayout()
    icon = QLabel()
    icon.setPixmap(self.windowIcon().pixmap(60, 60))
    heading.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
    copy = QVBoxLayout()
    copy.addWidget(text("Skrivi Lytt", "pageTitle"))
    copy.addWidget(text(VERSION + " · " + tr("Test release"), "secondary"))
    heading.addLayout(copy, 1)
    about.addLayout(heading)
    about.addWidget(
        info_card(
            "Free, local and open source",
            "Local reading. Part of the Skrivi family.",
            False,
        )
    )
    about.addWidget(
        text(
            "Use Skrivi Snakk to turn your speech into text in other apps.", "secondary"
        )
    )
    about.addWidget(
        link("Explore Skrivi Snakk", "https://skrivi.no/dictation/"),
        0,
        Qt.AlignmentFlag.AlignLeft,
    )
    links_card = QFrame()
    links_card.setProperty("uiRole", "quietCard")
    links_layout = QVBoxLayout(links_card)
    links_layout.setContentsMargins(18, 16, 18, 16)
    links_layout.addWidget(text("Learn more", "sectionTitle"))
    links = QGridLayout()
    self.update_button = QPushButton("Check for updates")
    self.update_button.clicked.connect(self.check_updates)
    links.addWidget(self.update_button, 0, 0, Qt.AlignmentFlag.AlignLeft)
    for row, column, label, url in [
        (0, 1, "Website", "https://skrivi.no/read-aloud/"),
        (1, 0, "Source code", "https://github.com/workavoidance/Skrivi-TTS"),
        (
            1,
            1,
            "Third-party licences",
            "https://github.com/workavoidance/Skrivi-TTS/blob/main/THIRD_PARTY_NOTICES.md",
        ),
    ]:
        links.addWidget(link(label, url), row, column, Qt.AlignmentFlag.AlignLeft)
    links_layout.addLayout(links)
    about.addWidget(links_card)
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
    from ux_helpers import polish

    polish(self)
