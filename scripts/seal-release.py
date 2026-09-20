"""Hash the final signed bytes; never sign after sealing the payload."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];payload=root/'build/release-payload'
p=payload/'package.json';m=json.loads(p.read_text(encoding='utf-8'));m['files']={}
for f in payload.rglob('*'):
 if f.is_file() and f!=p:
  with f.open('rb') as stream:m['files'][f.relative_to(payload).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
p.write_text(json.dumps(m,indent=2),encoding='utf-8')

# Preserve these exact signed runtimes for subsequent code-only releases.
output=root/'dist/signed';output.mkdir(parents=True,exist_ok=True)
archive=output/('Skrivi-TTS-'+m['version']+'-signed-runtimes.zip')
paths=[f for f in m['files'] if f.startswith(('runtimes/','app/licenses/','app/third_party_licenses/')) or f in ('app/LICENSE','app/THIRD_PARTY_NOTICES.md','app/SOURCES.md')]
files={f:m['files'][f] for f in paths}
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in sorted(paths):z.write(payload/name,name)
 z.writestr('runtime-manifest.json',json.dumps(dict(source_commit=m['source_commit'],files=files),indent=2))
with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
(output/'SIGNED-RUNTIME-ARCHIVE.json').write_text(json.dumps(dict(archive=archive.name,sha256=digest,source_commit=m['source_commit'],profiles=json.loads((payload/'app/runtime-profiles.json').read_text(encoding='utf-8'))),indent=2),encoding='utf-8')
