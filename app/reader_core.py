"""One-language-per-request routing and reader preferences."""
from functools import lru_cache
from pathlib import Path
import re
from core import DATA, read_json, write_json

PREFERENCES = dict(language='auto', fallback='no', english_voice='af_heart', speed=1.0,
                   hotkey='Ctrl+Alt+Space', model_override='', startup=False, ocr_layout=6, ui_language='auto')

def load_preferences():
    values=PREFERENCES.copy()
    values.update(read_json(DATA/'reader-settings.json',{}))
    if values['language'] not in ('auto','no','en'): values['language']='auto'
    if values['english_voice'] not in ('af_heart','am_michael','bf_emma'): values['english_voice']='af_heart'
    if values['fallback'] not in ('no','en'): values['fallback']='no'
    if values['hotkey'] not in ('Ctrl+Alt+Space','Ctrl+Alt+R','Ctrl+Shift+F8'): values['hotkey']=PREFERENCES['hotkey']
    if values['model_override'] not in ('','piper-nvcc','voxcpm-q4','chatterbox-q4'): values['model_override']=''
    if values['ui_language'] not in ('auto','en','nb'):values['ui_language']='auto'
    if values['ocr_layout'] not in (3,6):values['ocr_layout']=6
    try: values['speed']=max(.5,min(2.,float(values['speed'])))
    except (TypeError,ValueError): values['speed']=1.
    return values

@lru_cache(maxsize=1)
def detector_factory():
    import langdetect
    from langdetect.detector_factory import DetectorFactory
    factory=DetectorFactory()
    folder=Path(langdetect.__file__).parent/'profiles'
    factory.load_json_profile([(folder/lang).read_text(encoding='utf-8') for lang in ('no','en')])
    factory.set_seed(0)
    return factory

def choose_language(text, mode='auto', fallback='no'):
    if mode in ('no','en'): return mode, False
    # Avoid strong claims for a name, a number or a tiny selection.
    if len(re.findall(r"[^\W\d_]+",text,flags=re.UNICODE))<3:
        return fallback, True
    try:
        detector=detector_factory().create()
        detector.append(text[:12000])
        probabilities=detector.get_probabilities()
        if probabilities and probabilities[0].prob>=.80:
            return probabilities[0].lang, False
    except Exception:
        pass
    return fallback, True

def model_for_language(language):
    return 'kokoro-v1.0-onnx' if language=='en' else 'piper-talesyntese'
