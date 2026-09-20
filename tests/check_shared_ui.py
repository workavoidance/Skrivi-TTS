"""Disposable, offline GUI checks: no hotkeys, audio, downloads or user library."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
temporary = tempfile.TemporaryDirectory(prefix="skrivi-ux-check-")
os.environ["SKRIVI_TTS_DATA"] = temporary.name
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(ROOT / "app"))
from PySide6.QtWidgets import QApplication
from main import Reader
from i18n import configure

app = QApplication([])
from PySide6.QtGui import QFontDatabase, QFont
from theme import application_stylesheet

QFontDatabase.addApplicationFont(
    str(Path(os.environ["WINDIR"]) / "Fonts" / "segoeui.ttf")
)
app.setFont(QFont("Segoe UI", 10))
app.setStyleSheet(application_stylesheet(app.palette()))
reader = Reader(app, preview=True)
reader.ui_language.setCurrentIndex(reader.ui_language.findData("en"))
assert [reader.settings_tabs.tabText(i) for i in range(5)] == [
    "General",
    "Shortcuts",
    "Models",
    "Privacy",
    "About",
]
assert not (Path(temporary.name) / "reader-settings.json").exists()
reader.preview = False
with patch("main.write_json", side_effect=OSError("Read-only settings")):
    reader.speed.setValue(1.3)
assert reader.speed.value() == 1.0
assert reader.preferences["speed"] == 1.0
reader.preview = True
reader.change_region_shortcut("Ctrl+Shift+F9")
assert reader.preferences["region_hotkey"] == "Ctrl+Shift+F9"
reader.change_shortcut("Ctrl+Shift+F9")
assert reader.preferences["hotkey"] == "Ctrl+Alt+Space"
owner = reader.hotkeys
owner.current = "Ctrl+Alt+Space"
identifier = owner.identifier
with (
    patch("windows_reader.user32.RegisterHotKey", return_value=False),
    patch("windows_reader.user32.UnregisterHotKey") as release,
):
    try:
        owner.register("Ctrl+Alt+R")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Conflicting shortcut accepted")
    release.assert_not_called()
assert owner.current == "Ctrl+Alt+Space" and owner.identifier == identifier
owner.current = None
reader.overlay.setChecked(False)
assert not reader.pill.enabled
reader.ui_language.setCurrentIndex(reader.ui_language.findData("nb"))
assert reader.settings_tabs.tabText(1) == "Hurtigtaster"
assert reader.settings_tabs.tabText(3) == "Personvern"
assert reader.speed.accessibleName() == "Lesehastighet"
reader.ui_language.setCurrentIndex(reader.ui_language.findData("en"))
assert reader.speed.accessibleName() == "Reading speed"
reader.open_settings()
reader.set_status("Ready.")
reader.error_actions.hide()
reader.error_detail.hide()
app.processEvents()
output = ROOT / "build" / "ux-preview"
output.mkdir(parents=True, exist_ok=True)
reader.settings_dialog.grab().save(str(output / "lytt-settings.png"))
reader.open_reader()
app.processEvents()
reader.grab().save(str(output / "lytt-reader.png"))
reader.settings_dialog.hide()
reader.hide()
reader.pill.hide()
reader.temp.cleanup()
temporary.cleanup()
print(
    "PASS: shared navigation, settings rollback, shortcut conflicts, indicator choice, bilingual UI"
)
