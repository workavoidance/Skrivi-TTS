"""Fetch checksum-pinned build inputs; reuse local archives and model files."""
import argparse,hashlib,json,os,shutil,sys,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from core import Library,catalog
parser=argparse.ArgumentParser()
parser.add_argument('--models',action='store_true',help='Prepare the two bundled voices, downloading only missing files')
args=parser.parse_args()
manifest=json.loads((ROOT/'legacy-bundle.json').read_text())
archive=ROOT/'build/Skrivi-TTS-0.1.0-Windows-x64.zip'
archive.parent.mkdir(parents=True,exist_ok=True)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
if not archive.exists():
 temporary=archive.with_suffix('.download')
 with urllib.request.urlopen(manifest['url'],timeout=60) as response,temporary.open('wb') as target:shutil.copyfileobj(response,target)
 if digest(temporary)!=manifest['sha256']:raise SystemExit('Legacy runtime archive checksum mismatch')
 temporary.replace(archive)
if digest(archive)!=manifest['sha256']:raise SystemExit('Legacy runtime archive checksum mismatch')
with zipfile.ZipFile(archive) as package:
 for entry in package.infolist():
  for prefix,destination in [('runtimes/python-engine-v1/',ROOT/'dist/SkriviWorker'),('runtimes/vox-0.8.32/',ROOT/'build/vox-0.8.32')]:
   if not entry.filename.startswith(prefix) or entry.is_dir():continue
   relative=Path(entry.filename[len(prefix):]);target=(destination/relative).resolve()
   if not target.is_relative_to(destination.resolve()):raise SystemExit('Unexpected archive path')
   data=package.read(entry)
   if target.exists():
    if target.read_bytes()!=data:raise SystemExit('Existing immutable runtime differs: '+str(target))
   else:
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
if args.models:
 library=Library()
 for model in catalog():
  if model['id'] in ('piper-talesyntese','kokoro-v1.0-onnx'):library.install(model,progress=print)
print('Pinned build inputs ready. Existing model files are preserved.')
