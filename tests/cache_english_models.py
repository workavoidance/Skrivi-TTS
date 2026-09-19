"""Explicit one-time download/cache for the English comparison. Existing hashes reused."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('SKRIVI_TTS_DATA',str(Path(os.environ['LOCALAPPDATA'])/'SkriviTTS')))
manifest=json.loads((ROOT/'docs/ENGLISH_MODEL_MANIFEST.json').read_text(encoding='utf-8'))
for item in manifest:
    target=DATA/'models'/item['model']/item['path']
    target.parent.mkdir(parents=True,exist_ok=True)
    def matches(path):
        if not path.is_file() or path.stat().st_size!=item['bytes']: return False
        with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()==item['sha256']
    if matches(target):
        print('Reusing '+item['path']); continue
    if target.exists(): raise ValueError('Existing model differs; preserve and inspect: '+str(target))
    temporary=target.with_suffix(target.suffix+'.partial')
    urllib.request.urlretrieve(item['url'],temporary)
    if not matches(temporary): raise ValueError('Download integrity failure: '+item['path'])
    temporary.replace(target)
    print('Cached '+item['path'])
folder=ROOT/'build'/'english-2026-09-19'
folder.mkdir(parents=True,exist_ok=True)
(folder/'model-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
