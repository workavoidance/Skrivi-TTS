"""Opt-in packaged-runtime audit of production adapter vs original direct Piper API.

Replay identical raw ONNX outputs through the baseline API to avoid mistaking
normal stochastic variation for application differences. No user text is logged.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import wave
import numpy as np
from piper import PiperVoice, SynthesisConfig

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ['LOCALAPPDATA']) / 'SkriviTTS'
installed = DATA / 'versions/0.1.0'
spec = importlib.util.spec_from_file_location('production_worker', installed/'engines/worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
models = json.loads((installed/'models.json').read_text(encoding='utf-8'))
out = DATA / 'verification/nvcc-audit'
out.mkdir(parents=True, exist_ok=True)
TEXT = ('Skolen begynner klokken åtte. Elevene leser teksten og svarer på spørsmålene. '
        'Boka kostet 349 kroner. Hun avsluttet setningen tydelig.')

def hash_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

class RecordingSession:
    def __init__(self, session):
        self.session = session
        self.calls = []
        self.replay = False
        self.index = 0
    def run(self, names, feeds, *args, **kwargs):
        if not self.replay:
            result = self.session.run(names, feeds, *args, **kwargs)
            self.calls.append(({k: v.copy() for k, v in feeds.items()}, [v.copy() for v in result]))
            return result
        expected, result = self.calls[self.index]
        self.index += 1
        assert feeds.keys() == expected.keys()
        for key in feeds:
            assert np.array_equal(feeds[key], expected[key]), 'Changed inference input: ' + key
        return [v.copy() for v in result]
    def __getattr__(self, name):
        return getattr(self.session, name)

reports = []
for model_id, speaker in [('piper-nvcc', 3), ('piper-nvcc', 6), ('piper-talesyntese', 3)]:
    model = next(m for m in models if m['id'] == model_id)
    assets = DATA / 'models' / model_id
    for file in model['files']:
        assert hash_file(assets / file['path']) == file['sha256'], file['path']
    original_load = PiperVoice.load
    def load(*args, **kwargs):
        voice = original_load(*args, **kwargs)
        voice.session = RecordingSession(voice.session)
        return voice
    session = worker.Session()
    target = out / f'{model_id}-speaker{speaker}-app.wav'
    PiperVoice.load = staticmethod(load)
    try:
        result = session.run({'model': model, 'assets': str(assets), 'output': str(target), 'text': TEXT,
                             'settings': {'speaker': speaker, 'speed': 1, 'noise_scale': '', 'noise_w_scale': ''}})
    finally:
        PiperVoice.load = staticmethod(original_load)
    voice = session.engine
    missing = sorted({phoneme for sentence in voice.phonemize(TEXT) for phoneme in sentence
                      if phoneme not in voice.config.phoneme_id_map})
    chunks = []
    for feeds, outputs in voice.session.calls:
        raw = outputs[0].squeeze()
        chunks.append({'frames': len(raw), 'scales': feeds['scales'].tolist(),
                       'speaker_id': feeds.get('sid', np.array([])).tolist(),
                       'raw_tail_peak_20ms': float(np.max(np.abs(raw[-441:]))),
                       'raw_tail_rms_20ms': float(np.sqrt(np.mean(raw[-441:]**2)))})
    voice.session.replay = True
    baseline = out / f'{model_id}-speaker{speaker}-direct.wav'
    with wave.open(str(baseline), 'wb') as wav:
        voice.synthesize_wav(TEXT, wav, syn_config=SynthesisConfig(speaker_id=speaker if model_id == 'piper-nvcc' else None))
    assert hash_file(target) == hash_file(baseline), 'Adapter changes the WAV'
    with wave.open(str(target)) as wav:
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
        assert wav.getnframes() == sum(c['frames'] for c in chunks), 'Dropped generated frames'
        details = {'model': model_id, 'speaker': speaker, 'seconds': result['audio_seconds'],
                   'app_equals_direct_byte_for_byte': True, 'all_generated_frames_written': True,
                   'unmapped_phonemes': missing, 'sample_rate': wav.getframerate(),
                   'saturated_fraction': float(np.mean((pcm == 32767) | (pcm == -32768))),
                   'chunks': chunks}
    reports.append(details)
    print(json.dumps(details), flush=True)
    session.close()
(out/'report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
print('PASS: installed adapter exactly matches direct Piper for identical inference outputs.')
