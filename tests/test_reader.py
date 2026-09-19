"""Routing and settings regressions; no model downloads or speech output."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from reader_core import choose_language,model_for_language,load_preferences
from core import validate

class ReaderTests(unittest.TestCase):
    def test_detects_whole_passage(self):
        self.assertEqual(choose_language('The rain had stopped by the time we reached the station.'),('en',False))
        self.assertEqual(choose_language('Dette er en norsk tekst som blir lest opp på datamaskinen.'),('no',False))
    def test_manual_language_overrides_detection(self):
        self.assertEqual(choose_language('This is clearly English.','no'),('no',False))
        self.assertEqual(choose_language('Dette er norsk.','en'),('en',False))
    def test_short_or_empty_uses_configured_fallback(self):
        for text in ('','Sarah','2048','Hello Sarah'):
            self.assertEqual(choose_language(text,fallback='en'),('en',True))
    def test_mixed_passage_uses_one_dominant_language(self):
        text='The weather was beautiful and we walked along the river before going home. Takk for i dag.'
        self.assertEqual(model_for_language(choose_language(text)[0]),'kokoro-v1.0-onnx')
    def test_bad_saved_values_do_not_break_reader(self):
        with patch('reader_core.read_json',return_value=dict(language='invalid',hotkey='invalid',model_override='gone',speed='bad')):
            prefs=load_preferences()
        self.assertEqual(prefs['language'],'auto')
        self.assertEqual(prefs['model_override'],'')
        self.assertEqual(prefs['hotkey'],'Ctrl+Alt+Space')
        self.assertEqual(prefs['speed'],1)
    def test_heart_defaults_and_invalid_voice(self):
        settings=validate('kokoro',{})
        self.assertEqual((settings['voice'],settings['speed'],settings['threads']),('af_heart',1,8))
        with self.assertRaises(ValueError):validate('kokoro',dict(voice='unknown'))

if __name__=='__main__':unittest.main()
