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

# Once the first signed release is published, reuse its immutable runtime bytes.
pin_file=root/'docs/SIGNED_RUNTIME_ARCHIVE.json'
if pin_file.exists():
 pin=json.loads(pin_file.read_text(encoding='utf-8'))
 for name,digest in pin['source_inputs'].items():
  if hashlib.sha256((root/name).read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()!=digest:
   raise RuntimeError('Frozen runtime input changed; assign a new runtime profile before rebuilding: '+name)
 if Path(pin['archive']).name!=pin['archive']:raise ValueError('Unsafe runtime archive name')
 signed_archive=root/'build'/pin['archive']
 if not signed_archive.exists():
  partial=signed_archive.with_suffix('.partial')
  urllib.request.urlretrieve(pin['url'],partial)
  with partial.open('rb') as f:
   if hashlib.file_digest(f,'sha256').hexdigest()!=pin['sha256']:raise ValueError('Signed runtime archive checksum mismatch')
  partial.replace(signed_archive)
 with signed_archive.open('rb') as f:
  if hashlib.file_digest(f,'sha256').hexdigest()!=pin['sha256']:raise ValueError('Cached signed runtime archive differs')
 signed_target=root/'build/signed-runtime-input'
 with zipfile.ZipFile(signed_archive) as z:
  runtime_manifest=json.loads(z.read('runtime-manifest.json'))
  for name,digest in runtime_manifest['files'].items():
   dest=(signed_target/name).resolve()
   if not dest.is_relative_to(signed_target.resolve()):raise ValueError('Unsafe signed runtime path')
   data=dest.read_bytes() if dest.exists() else z.read(name)
   if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Signed runtime input differs: '+name)
   if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 (signed_target/'runtime-manifest.json').write_text(json.dumps(runtime_manifest),encoding='utf-8')
 print('Published signed runtimes verified and reused without re-signing.')
