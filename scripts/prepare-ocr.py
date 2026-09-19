"""Explicit build-time download of checksum-pinned OCR language data."""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'build/ocr-assets';folder.mkdir(exist_ok=True)
for entry in json.loads((root/'docs/OCR_MODEL_MANIFEST.json').read_text(encoding='utf-8')):
 target=folder/entry['file']
 if not target.exists():
  temp=target.with_suffix('.download')
  urllib.request.urlretrieve(entry['url'],temp)
  if hashlib.sha256(temp.read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('OCR model checksum mismatch')
  temp.replace(target)
 if hashlib.sha256(target.read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('Existing OCR model differs; preserved.')
print('Pinned OCR models ready.')
