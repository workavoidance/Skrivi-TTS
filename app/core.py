"""Stable library and model registry. Application upgrades never own model data."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading
import urllib.request
import uuid
import sys

VERSION = '0.3.0'
KOKORO_VOICES = {'af_heart': 'Heart — American female', 'am_michael': 'Michael — American male', 'bf_emma': 'Emma — British female'}
ROOT = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get('SKRIVI_TTS_DATA', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'SkriviTTS')))

def read_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(temp, path)

def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def catalog():
    return read_json(ROOT / 'models.json')

class Library:
    def __init__(self, root=DATA):
        self.root = Path(root)
        for folder in ('models', 'voices', 'outputs', 'presets'):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / 'library.json'
        self.registry = read_json(self.registry_path, {'schema': 1, 'models': {}})
        if self.registry.get('schema') != 1:
            raise ValueError('This library needs a newer application version. Its files were preserved.')

    def path(self, model):
        entry = self.registry['models'].get(model['id'])
        return Path(entry['path']) if entry else self.root / 'models' / model['id']

    def ready(self, model):
        entry = self.registry['models'].get(model['id'])
        root = self.path(model)
        return bool(entry and entry.get('revision') == model['revision'] and all(
            (root / f['path']).is_file() and (root / f['path']).stat().st_size == f['bytes']
            for f in model['files']))

    def register(self, model, source, progress=lambda _: None, cancel=None):
        source = Path(source).resolve()
        for item in model['files']:
            if cancel and cancel.is_set():
                raise InterruptedError('Cancelled')
            target = source / item['path']
            progress('Verifying ' + item['path'])
            if not target.is_file() or target.stat().st_size != item['bytes'] or sha256(target) != item['sha256']:
                raise ValueError('Model verification failed: ' + item['path'])
        self.registry['models'][model['id']] = {'path': str(source), 'revision': model['revision']}
        write_json(self.registry_path, self.registry)

    def install(self, model, progress=lambda _: None, cancel=None, source=None):
        """Copies existing assets or downloads missing files; atomically validates each file."""
        cancel = cancel or threading.Event()
        target_root = self.root / 'models' / model['id']
        target_root.mkdir(parents=True, exist_ok=True)
        for item in model['files']:
            if cancel.is_set():
                raise InterruptedError('Cancelled')
            target = target_root / item['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.stat().st_size == item['bytes'] and sha256(target) == item['sha256']:
                progress('Reusing ' + item['path'])
                continue
            part = target.with_name(target.name + '.partial')
            if source:
                origin = Path(source) / item['path']
                progress('Importing ' + item['path'])
                with origin.open('rb') as src, part.open('wb') as dst:
                    while chunk := src.read(4 * 1024 * 1024):
                        if cancel.is_set():
                            raise InterruptedError('Cancelled')
                        dst.write(chunk)
            else:
                request = urllib.request.Request(item['url'], headers={'User-Agent': 'SkriviTTS/0.1'})
                with urllib.request.urlopen(request, timeout=30) as response, part.open('wb') as dst:
                    received = 0
                    while chunk := response.read(1024 * 1024):
                        if cancel.is_set():
                            raise InterruptedError('Cancelled')
                        dst.write(chunk)
                        received += len(chunk)
                        progress(f"Downloading {item['path']}: {received / 1e6:.0f} / {item['bytes'] / 1e6:.0f} MB")
            if part.stat().st_size != item['bytes'] or sha256(part) != item['sha256']:
                raise ValueError('Downloaded/imported file checksum mismatch: ' + item['path'])
            os.replace(part, target)
        self.register(model, target_root, progress, cancel)

def defaults(engine):
    return {
        'kokoro': {'voice': 'af_heart', 'speed': 1.0, 'threads': 8},
        'voxcpm': {'seed': 42, 'steps': 10, 'guidance': 2.0, 'threads': 8, 'reference': '', 'consent': False},
        'chatterbox': {'seed': 2607, 'threads': 8, 'language': 'no', 'exaggeration': 0.5,
                       'repetition_penalty': 1.2, 'max_tokens': 2048, 'reference': '', 'consent': False},
        'piper': {'speaker': 3, 'speed': 1.0, 'noise_scale': '', 'noise_w_scale': ''},
    }[engine].copy()

def validate(engine, values):
    result = defaults(engine)
    result.update(values)
    ranges = {
        'voxcpm': {'seed': (1, 999999, int), 'steps': (4, 20, int), 'guidance': (1, 4, float), 'threads': (1, 16, int)},
        'chatterbox': {'seed': (1, 999999, int), 'threads': (1, 16, int), 'exaggeration': (0, 2, float),
                       'repetition_penalty': (1, 2, float), 'max_tokens': (128, 8192, int)},
        'kokoro': {'speed': (0.5, 2, float), 'threads': (1, 16, int)},
        'piper': {'speaker': (0, 9, int), 'speed': (0.5, 2, float)},
    }[engine]
    for key, (low, high, kind) in ranges.items():
        value = kind(result[key])
        if not low <= value <= high:
            raise ValueError(f'{key} must be between {low} and {high}')
        result[key] = value
    for key in ('noise_scale', 'noise_w_scale'):
        if key in result and result[key] != '':
            result[key] = float(result[key])
            if not 0 <= result[key] <= 2:
                raise ValueError(f'{key} must be between 0 and 2, or blank for native default')
    if engine == 'kokoro' and result['voice'] not in KOKORO_VOICES:
        raise ValueError('Choose Heart, Michael or Emma for the English voice.')
    if engine == 'chatterbox' and result['language'] not in ('no', 'en'):
        raise ValueError('Choose no or en for language')
    if result.get('reference') and not result.get('consent'):
        raise ValueError('Confirm permission to use the reference voice.')
    return result
