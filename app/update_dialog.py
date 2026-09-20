"""Explicit, non-modal update check using the shared Skrivi release policy."""

import threading
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from core import VERSION, STORE_BUILD
from i18n import tr
from release_updates import check_release


class UpdateEvents(QObject):
    result = Signal(str, str)


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        self.message = QLabel()
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.notes = QPushButton(tr("Release notes and download"))
        self.notes.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url)))
        layout.addWidget(self.notes)
        self.retry = QPushButton(tr("Check for updates"))
        self.retry.clicked.connect(self.check)
        layout.addWidget(self.retry)
        self.events = UpdateEvents(self)
        self.events.result.connect(self.received)
        self.busy = False
        self.url = "https://github.com/workavoidance/Skrivi-TTS/releases"

    def check(self):
        if STORE_BUILD:
            QDesktopServices.openUrl(QUrl("ms-windows-store://downloadsandupdates"))
            return
        self.setWindowTitle(tr("Check for updates"))
        self.show()
        self.raise_()
        if self.busy:
            return
        self.busy = True
        self.retry.setEnabled(False)
        self.message.setText(tr("Checking for updates…"))

        def work():
            try:
                available = check_release("Skrivi-TTS", VERSION)
                self.events.result.emit(available or "", "")
            except Exception:
                self.events.result.emit(
                    "",
                    "Could not check for updates. Check your connection and try again.",
                )

        threading.Thread(target=work, daemon=True).start()

    def received(self, version, error):
        self.busy = False
        self.retry.setEnabled(True)
        self.url = "https://github.com/workavoidance/Skrivi-TTS/releases" + (
            f"/tag/v{version}" if version else ""
        )
        message = (
            tr(error)
            if error
            else tr("Version {version} is available.").format(version=version)
            if version
            else tr("You have the latest test release.")
        )
        self.message.setText(
            tr("Installed version: {version} · Test release").format(version=VERSION)
            + "\n\n"
            + message
        )
