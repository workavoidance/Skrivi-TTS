"""Public names must not change data, startup or single-instance identity."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
import i18n


class ProductNamingTests(unittest.TestCase):
    def test_reader_names_and_compatibility(self):
        source = (ROOT / 'app/main.py').read_text(encoding='utf-8')
        self.assertIn("setWindowTitle('Skrivi Lytt')", source)
        self.assertIn("setApplicationDisplayName('Skrivi Lytt')", source)
        self.assertIn("setApplicationName('Skrivi TTS')", source)
        self.assertIn("connectToServer('SkriviTTS-reader-v1')", source)
        self.assertIn("setOrganizationName('Skrivi')", source)

    def test_both_languages_keep_the_product_name(self):
        old = i18n.LANGUAGE
        try:
            for language, expected in [('nb', 'Avslutt Skrivi Lytt'), ('en', 'Quit Skrivi Lytt')]:
                i18n.configure(language)
                self.assertEqual(i18n.tr('Quit Skrivi Lytt'), expected)
                self.assertEqual(i18n.tr('Skrivi Lytt'), 'Skrivi Lytt')
        finally:
            i18n.LANGUAGE = old

    def test_installer_identity_and_shortcuts(self):
        source = (ROOT / 'installer/SkriviTTS.iss').read_text(encoding='utf-8')
        self.assertIn('AppName=Skrivi Lytt', source)
        self.assertIn('AppId={{E9E45873-7840-45F2-B17F-7C66496302C9}', source)
        self.assertIn(r'DefaultDirName={localappdata}\SkriviTTS\versions\{#AppVersion}', source)
        self.assertIn(r'Name: "{userprograms}\Skrivi Lytt"', source)
        self.assertIn('VersionRoot', source)
        self.assertIn('Check: WantDesktopShortcut', source)
        install = (ROOT / 'INSTALL.ps1').read_text(encoding='utf-8')
        self.assertIn("'Skrivi Lytt.lnk'", install)
        self.assertIn("$oldTarget.StartsWith($ownedVersions", install)

    def test_store_template_display_names_not_identity(self):
        root = ET.parse(ROOT / 'store/AppxManifest.xml').getroot()
        for element in root.iter():
            if element.tag.endswith('}DisplayName'):
                self.assertEqual(element.text, 'Skrivi Lytt')
            if 'DisplayName' in element.attrib:
                self.assertEqual(element.get('DisplayName'), 'Skrivi Lytt')
        source = (ROOT / 'store/AppxManifest.xml').read_text(encoding='utf-8')
        self.assertIn('Identity Name="__NAME__"', source)
        self.assertIn('TaskId="SkriviTTSStartup"', source)


if __name__ == '__main__':
    unittest.main()
