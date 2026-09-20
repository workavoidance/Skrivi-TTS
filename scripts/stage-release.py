"""Prepare an unsigned payload. Sign copies, then seal manifest and installer."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
from core import VERSION
out=root/'build/release-payload'
if out.exists():raise SystemExit('Release staging already exists; use a clean build directory.')
shutil.copytree(root/'dist/SkriviTTS',out/'app')
shutil.copytree(root/'app',out/'app/app',ignore=shutil.ignore_patterns('__pycache__','shootout.py'))
(out/'app/engines').mkdir()
for file in ('worker.py','kokoro_engine.py'):shutil.copy2(root/'engines'/file,out/'app/engines'/file)
models=[m for m in json.loads((root/'models.json').read_text(encoding='utf-8')) if m['id'] in ('piper-talesyntese','kokoro-v1.0-onnx')]
(out/'app/models.json').write_text(json.dumps(models,indent=2),encoding='utf-8')
(out/'app/native').mkdir()
for name in ('Selection.exe','VerifyPackage.exe'):shutil.copy2(root/'native'/name,out/'app/native'/name)
profiles={'python-engine-v1':'python-engine-signed-v1','kokoro-engine-v1':'kokoro-engine-signed-v1','tesseract-5.5.2-v2':'tesseract-5.5.2-signed-v2'}
(out/'app/runtime-profiles.json').write_text(json.dumps(profiles,indent=2),encoding='utf-8')
pin_file=root/'docs/SIGNED_RUNTIME_ARCHIVE.json'
if pin_file.exists():
 pin=json.loads(pin_file.read_text(encoding='utf-8'))
 if pin['profiles']!=profiles:raise ValueError('Signed runtime profile mapping changed; update the release pin explicitly')
 signed_input=root/'build/signed-runtime-input'
 manifest=json.loads((signed_input/'runtime-manifest.json').read_text(encoding='utf-8'))
 for name,digest in manifest['files'].items():
  f=(signed_input/name).resolve()
  if not f.is_relative_to(signed_input.resolve()):raise ValueError('Unsafe runtime input path')
  with f.open('rb') as stream:
   if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('Signed input changed after preparation: '+name)
 for profile in profiles.values():shutil.copytree(signed_input/'runtimes'/profile,out/'runtimes'/profile)
else:
 for original in ('python-engine-v1','kokoro-engine-v1'):shutil.copytree(root/'build/release-input/runtimes'/original,out/'runtimes'/profiles[original])
 shutil.copytree(root/'dist/OCRWorker',out/'runtimes'/profiles['tesseract-5.5.2-v2'])
shutil.copytree(root/'build/release-input/models',out/'models')
shutil.copytree(root/'build/ocr-assets',out/'models/ocr-tessdata-fast-v1')
for name in ('INSTALL.ps1','INSTALL.bat','LICENSE','THIRD_PARTY_NOTICES.md','README.md'):shutil.copy2(root/name,out/name)
for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):shutil.copy2(root/name,out/'app'/name)
shutil.copy2(root/'docs/SOURCES.md',out/'app/SOURCES.md')
for origin in (root/'build/release-input/app/licenses',root/'licenses'):shutil.copytree(origin,out/'app/licenses',dirs_exist_ok=True)
shutil.copytree(root/'build/release-input/app/third_party_licenses',out/'app/third_party_licenses')
for env in (root/'.build-env',root/'build/ocr-env'):
 for dist in (env/'Lib/site-packages').glob('*.dist-info'):
  for file in dist.rglob('*'):
   if file.is_file() and any(w in file.name.lower() for w in ('license','copying','notice')):
    dest=out/'app/third_party_licenses'/dist.name/file.relative_to(dist);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
(out/'package.json').write_text(json.dumps(dict(version=VERSION,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),files={})),encoding='utf-8')
print(out)
