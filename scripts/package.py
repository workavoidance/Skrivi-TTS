"""Build the offline reader bundle with two verified models and reusable runtimes."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from core import VERSION

parser = argparse.ArgumentParser()
parser.add_argument('--vox-runtime', type=Path, required=True)
parser.add_argument('--model-library', type=Path, default=Path(os.environ['LOCALAPPDATA'])/'SkriviTTS/models')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
package = root / 'build' / ('Skrivi-TTS-' + VERSION)
if package.exists():
    raise SystemExit('Package already exists. Choose a new version or inspect the existing build first.')
shutil.copytree(root/'dist/SkriviTTS', package/'app')
for name in ['app','engines']:
    shutil.copytree(root/name, package/'app'/name, ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(root/'models.json', package/'app/models.json')
(package/'app/native').mkdir()
for helper in ('VoxHost.exe','Selection.exe'):
    shutil.copy2(root/'native'/helper, package/'app/native'/helper)
shutil.copytree(root/'dist/SkriviWorker', package/'runtimes/python-engine-v1')
shutil.copytree(args.vox_runtime, package/'runtimes/vox-0.8.32')
shutil.copytree(root/'dist/KokoroWorker', package/'runtimes/kokoro-engine-v1')
models=json.loads((root/'models.json').read_text(encoding='utf-8'))
for model in models:
    if model['id'] not in ('piper-talesyntese','kokoro-v1.0-onnx'): continue
    for entry in model['files']:
        source=args.model_library/model['id']/entry['path']
        with source.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=entry['sha256'] or source.stat().st_size!=entry['bytes']:
            raise SystemExit('Bundled model verification failed: '+str(source))
        target=package/'models'/model['id']/entry['path']
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
for name in ['INSTALL.ps1', 'INSTALL.bat', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md']:
    shutil.copy2(root/name, package/name)
for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md']:
    shutil.copy2(root/name, package/'app'/name)
licenses = package/'app/third_party_licenses'
licenses.mkdir()
for distribution in [* (root/'.build-env/Lib/site-packages').glob('*.dist-info'), * (root/'build/english-env/Lib/site-packages').glob('*.dist-info')]:
    for file in distribution.rglob('*'):
        if file.is_file() and any(word in file.name.lower() for word in ('license', 'copying', 'notice')):
            destination = licenses/distribution.name/file.relative_to(distribution)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, destination)
shutil.copytree(root/'licenses',package/'app/licenses')
shutil.copy2(root/'docs/SOURCES.md',package/'app/SOURCES.md')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
manifest = {'version': VERSION, 'source_commit':commit, 'bundled_models':['piper-talesyntese','kokoro-v1.0-onnx'], 'files': {}}
for file in package.rglob('*'):
    if file.is_file():
        manifest['files'][file.relative_to(package).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
(package/'package.json').write_text(json.dumps(manifest, indent=2),encoding='utf-8')
archive = shutil.make_archive(str(root/'build'/f'Skrivi-TTS-{VERSION}-Windows-x64'), 'zip', package)
print(archive)
