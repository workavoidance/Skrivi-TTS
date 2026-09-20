import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from release_updates import select_release
from shortcut_keys import shortcut_parts
from reader_core import load_preferences


class SharedUXTests(unittest.TestCase):
    def test_test_channel_includes_prereleases_and_never_downgrades(self):
        releases = [
            {"tag_name": "v0.2.1"},
            {"tag_name": "v0.4.2", "prerelease": True},
            {"tag_name": "v9.0.0", "draft": True},
        ]
        self.assertEqual(
            select_release(releases, "0.4.1", test_releases=True)["tag_name"], "v0.4.2"
        )
        self.assertIsNone(select_release(releases, "0.4.1", test_releases=False))
        self.assertIsNone(select_release(releases, "0.4.2", test_releases=True))

    def test_shortcuts_validate_modifier_and_key(self):
        self.assertEqual(shortcut_parts("Ctrl+Alt+Shift+Space"), (7, 32))
        self.assertEqual(shortcut_parts("Ctrl+Shift+F8"), (6, 119))
        for value in ("A", "Shift+A", "Ctrl+Ctrl+A", "Ctrl+Escape", "Ctrl+Alt+Delete"):
            with self.assertRaises(ValueError):
                shortcut_parts(value)

    def test_existing_preferences_gain_defaults_without_losing_custom_settings(self):
        with patch(
            "reader_core.read_json",
            return_value={"hotkey": "Ctrl+Alt+R", "speed": 1.3, "startup": True},
        ):
            values = load_preferences()
        self.assertEqual(values["hotkey"], "Ctrl+Alt+R")
        self.assertEqual(values["speed"], 1.3)
        self.assertEqual(values["region_hotkey"], "Ctrl+Alt+Shift+Space")
        self.assertTrue(values["overlay_enabled"])

    def test_saved_conflicting_shortcuts_recover_to_distinct_defaults(self):
        with patch(
            "reader_core.read_json",
            return_value={"hotkey": "Alt+Ctrl+R", "region_hotkey": "Ctrl+Alt+R"},
        ):
            values = load_preferences()
        self.assertNotEqual(
            shortcut_parts(values["hotkey"]), shortcut_parts(values["region_hotkey"])
        )
