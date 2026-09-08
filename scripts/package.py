"""Package app separately from immutable runtimes; never include model weights."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from core import VERSION

parser = argparse.ArgumentParser()
parser.add_argument('--vox-runtime', type=Path, required=True)
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
shutil.copy2(root/'native/VoxHost.exe', package/'app/native/VoxHost.exe')
shutil.copytree(root/'dist/SkriviWorker', package/'runtimes/python-engine-v1')
shutil.copytree(args.vox_runtime, package/'runtimes/vox-0.8.32')
for name in ['INSTALL.ps1', 'INSTALL.bat', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md']:
    shutil.copy2(root/name, package/name)
for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md']:
    shutil.copy2(root/name, package/'app'/name)
licenses = package/'app/third_party_licenses'
licenses.mkdir()
for distribution in (root/'.build-env/Lib/site-packages').glob('*.dist-info'):
    for file in distribution.rglob('*'):
        if file.is_file() and any(word in file.name.lower() for word in ('license', 'copying', 'notice')):
            destination = licenses/distribution.name/file.relative_to(distribution)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, destination)
manifest = {'version': VERSION, 'files': {}}
for file in package.rglob('*'):
    if file.is_file():
        manifest['files'][file.relative_to(package).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
(package/'package.json').write_text(json.dumps(manifest, indent=2),encoding='utf-8')
archive = shutil.make_archive(str(root/'build'/f'Skrivi-TTS-{VERSION}-Windows-x64'), 'zip', package)
print(archive)
