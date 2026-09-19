"""Bundle the reader plus new OCR assets; reuse installed 0.2.1 speech assets."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
from core import VERSION
base=root/'build/Skrivi-TTS-0.2.1';old=json.loads((base/'package.json').read_text(encoding='utf-8'))
target=root/'build'/('Skrivi-TTS-'+VERSION+'-OCR-update')
if target.exists():raise SystemExit('Staging directory exists; inspect before rebuilding.')
subprocess.run([str(root/'dist/SkriviTTS/SkriviTTS.exe'),'--check-startup'],check=True,timeout=30)
shutil.copytree(root/'dist/SkriviTTS',target/'app')
for name in ('app','engines'):shutil.copytree(root/name,target/'app'/name,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(root/'models.json',target/'app/models.json')
shutil.copytree(root/'native',target/'app/native',ignore=shutil.ignore_patterns('*.cs'))
shutil.copytree(root/'dist/OCRWorker',target/'runtimes/tesseract-5.5.2-v1')
models=target/'models/ocr-tessdata-fast-v1';models.mkdir(parents=True)
for entry in json.loads((root/'docs/OCR_MODEL_MANIFEST.json').read_text(encoding='utf-8')):
 src=root/'build/ocr-assets'/entry['file']
 if hashlib.sha256(src.read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('OCR asset checksum mismatch')
 shutil.copy2(src,models/entry['file'])
for name in ('INSTALL.bat','README.md','LICENSE','THIRD_PARTY_NOTICES.md'):shutil.copy2(root/name,target/name)
shutil.copy2(root/'INSTALL.ps1',target/'INSTALL-core.ps1');shutil.copy2(root/'scripts/install-update.ps1',target/'INSTALL.ps1')
shutil.copytree(root/'licenses',target/'app/licenses')
for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):shutil.copy2(root/name,target/'app'/name)
for env in (root/'.build-env',root/'build/ocr-env'):
 for distribution in (env/'Lib/site-packages').glob('*.dist-info'):
  for file in distribution.rglob('*'):
   if file.is_file() and any(word in file.name.lower() for word in ('license','copying','notice')):
    dest=target/'app/third_party_licenses'/distribution.name/file.relative_to(distribution)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
manifest=dict(version=VERSION,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),kind='ocr-update',required_runtimes={p:h for p,h in old['files'].items() if p.startswith('runtimes/') and p.endswith('.exe')},files={})
for file in target.rglob('*'):
 if file.is_file():manifest['files'][file.relative_to(target).as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
(target/'package.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
archive=Path(shutil.make_archive(str(target),'zip',target))
print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
