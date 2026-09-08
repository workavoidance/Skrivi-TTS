"""Opt-in installed-runtime test: cold/warm native WAV generation and Stop."""
import json
from pathlib import Path
import sys
import threading
import time
import wave
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from core import Library, DATA, catalog, defaults, write_json
from client import Client

library = Library()
client = Client()
results = []
cancel = threading.Event()
folder = DATA / 'verification'
folder.mkdir(exist_ok=True)
try:
    for model in catalog():
        for index in range(2):
            output = folder / f"{model['id']}-{index}.wav"
            started = time.perf_counter()
            result = client.generate({'model': model, 'assets': str(library.path(model)),
                'settings': defaults(model['engine']), 'text': 'Hei! Dette er en prøve på norsk tale.',
                'output': str(output), 'voices': str(DATA / 'voices'),
                'vox_runtime': str(DATA / 'runtimes' / 'vox-0.8.32')}, cancel)
            result['total_wait_seconds'] = time.perf_counter() - started
            with wave.open(str(output)) as wav:
                assert wav.getframerate() == result['sample_rate']
                assert abs(wav.getnframes()/wav.getframerate()-result['audio_seconds']) < 0.001
            assert result['warm'] == bool(index)
            results.append(result)
            write_json(folder / 'engine-results.json', results)
            print(json.dumps({k:result[k] for k in ('model','warm','load_seconds','generation_seconds','audio_seconds')}), flush=True)
    model = catalog()[0]
    timer = threading.Timer(1, cancel.set)
    timer.start()
    try:
        client.generate({'model': model, 'assets': str(library.path(model)), 'settings': defaults(model['engine']),
            'text': 'Dette er en lengre test. ' * 50, 'output': str(folder/'cancelled.wav'),
            'voices': str(DATA/'voices'), 'vox_runtime': str(DATA/'runtimes/vox-0.8.32')}, cancel)
        raise AssertionError('Cancelled generation unexpectedly completed')
    except InterruptedError:
        assert client.process is None
    finally:
        timer.cancel()
finally:
    client.stop()
print('PASS: 4 real engines, cold/warm reuse, native WAV validation, cancellation.')
