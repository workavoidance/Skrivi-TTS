"""Make a model/runtime-free update from a verified full release package."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('full_package',type=Path);args=parser.parse_args()
source=args.full_package.resolve();old=json.loads((source/'package.json').read_text())
for relative,digest in old['files'].items():
    file=(source/relative).resolve()
    if not file.is_relative_to(source):raise SystemExit('Unsafe package path')
    with file.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=digest:raise SystemExit('Full package checksum mismatch: '+relative)
version=old['version'];target=root/'build'/('Skrivi-TTS-'+version+'-update')
if target.exists():raise SystemExit('Update staging directory already exists; inspect it first.')
shutil.copytree(source/'app',target/'app')
for name in ['INSTALL.bat','README.md','LICENSE','THIRD_PARTY_NOTICES.md']:shutil.copy2(source/name,target/name)
shutil.copy2(source/'INSTALL.ps1',target/'INSTALL-core.ps1')
shutil.copy2(root/'scripts/install-update.ps1',target/'INSTALL.ps1')
manifest=dict(version=version,source_commit=old['source_commit'],packaging_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),kind='app-update',required_runtimes={p:h for p,h in old['files'].items() if p.startswith('runtimes/') and p.endswith('.exe')},files={})
for file in target.rglob('*'):
    if file.is_file():
        with file.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        manifest['files'][file.relative_to(target).as_posix()]=digest
(target/'package.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(shutil.make_archive(str(root/'build'/('Skrivi-TTS-'+version+'-App-Update-Windows-x64')),'zip',target))
