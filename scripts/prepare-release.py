"""Prepare verified published speech assets for a new signed release."""
import json,hashlib,urllib.request,zipfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
archive=root/'build/Skrivi-TTS-0.2.1-Windows-x64.zip'
expected='076beea27234c6442c7f782948c2680422176eb8a172e1aef16b2f96c4e58050'
if not archive.exists():
 urllib.request.urlretrieve('https://github.com/workavoidance/Skrivi-TTS/releases/download/v0.2.1/'+archive.name,archive)
with archive.open('rb') as f:
 if hashlib.file_digest(f,'sha256').hexdigest()!=expected:raise RuntimeError('Published bundle checksum mismatch')
target=root/'build/release-input'
with zipfile.ZipFile(archive) as z:
 manifest=json.loads(z.read('package.json'))
 for name,digest in manifest['files'].items():
  if not (name.startswith(('models/piper-talesyntese/','models/kokoro-v1.0-onnx/','runtimes/python-engine-v1/','runtimes/kokoro-engine-v1/','app/licenses/','app/third_party_licenses/'))):continue
  dest=(target/name).resolve()
  if not dest.is_relative_to(target.resolve()):raise ValueError('Invalid path')
  if dest.exists():
   if hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:raise ValueError('Existing build input differs')
   continue
  data=z.read(name)
  if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Input checksum mismatch')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
print('Published speech runtimes and models verified; no user-library changes.')
