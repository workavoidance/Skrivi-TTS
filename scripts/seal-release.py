"""Hash the final signed bytes; never sign after sealing the payload."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];payload=root/'build/release-payload'
p=payload/'package.json';m=json.loads(p.read_text(encoding='utf-8'));m['files']={}
for f in payload.rglob('*'):
 if f.is_file() and f!=p:
  with f.open('rb') as stream:m['files'][f.relative_to(payload).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
p.write_text(json.dumps(m,indent=2),encoding='utf-8')
