import hashlib
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from core import Library, validate, write_json, read_json

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'weights.bin').write_bytes(b'known model')
        self.model = {'id': 'test', 'revision': 'pinned', 'files': [{'path': 'weights.bin', 'bytes': 11,
            'sha256': hashlib.sha256(b'known model').hexdigest(), 'url': 'https://invalid.example/model'}]}
    def tearDown(self):
        self.temp.cleanup()
    def test_upgrade_reuses_models_settings_and_presets_without_network(self):
        first = Library(self.root / 'library')
        first.install(self.model, source=self.source)
        write_json(first.root / 'settings.json', {'seed': 123})
        write_json(first.root / 'presets' / 'mine.json', {'steps': 8})
        stamp = (first.path(self.model) / 'weights.bin').stat().st_mtime_ns
        upgraded = Library(first.root)
        with patch('urllib.request.urlopen', side_effect=AssertionError('Unexpected download')):
            upgraded.install(self.model)
        self.assertTrue(upgraded.ready(self.model))
        self.assertEqual(stamp, (upgraded.path(self.model) / 'weights.bin').stat().st_mtime_ns)
        self.assertEqual(read_json(first.root / 'settings.json'), {'seed': 123})
        self.assertEqual(read_json(first.root / 'presets' / 'mine.json'), {'steps': 8})
    def test_wrong_file_is_never_registered(self):
        (self.source / 'weights.bin').write_bytes(b'bad weights')
        library = Library(self.root / 'library')
        with self.assertRaises(ValueError):
            library.install(self.model, source=self.source)
        self.assertFalse(library.ready(self.model))
        self.assertNotIn('test', library.registry['models'])
    def test_cancel_does_not_register_partial_model(self):
        library = Library(self.root / 'library')
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(InterruptedError):
            library.install(self.model, cancel=cancel, source=self.source)
        self.assertFalse(library.ready(self.model))
    def test_preserves_future_schema_instead_of_resetting(self):
        folder = self.root / 'library'
        write_json(folder / 'library.json', {'schema': 100, 'models': {'precious': {}}})
        with self.assertRaises(ValueError):
            Library(folder)
        self.assertIn('precious', read_json(folder / 'library.json')['models'])
    def test_reference_requires_permission_and_settings_are_bounded(self):
        with self.assertRaises(ValueError):
            validate('voxcpm', {'reference': 'voice-test.wav', 'consent': False})
        with self.assertRaises(ValueError):
            validate('voxcpm', {'threads': 100})
        self.assertEqual(validate('piper', {})['speed'], 1)

if __name__ == '__main__':
    unittest.main()
