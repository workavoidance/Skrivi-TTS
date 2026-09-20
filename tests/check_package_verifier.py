"""Exercise the compiled verifier against disposable library fixtures."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
exe=root/'native/VerifyPackage.exe'
with tempfile.TemporaryDirectory() as folder:
 base=Path(folder);library=base/'library';library.mkdir();manifest=base/'package.json'
 model=library/'models/voice/model.bin';model.parent.mkdir(parents=True);model.write_bytes(b'existing model')
 original=model.read_bytes();sha=hashlib.sha256(original).hexdigest()
 for name,digest,expected in [('models/voice/model.bin',sha,0),('models/voice/model.bin','0'*64,1),('models/not-downloaded.bin',sha,0),('models/../../outside.bin',sha,1)]:
  manifest.write_text(json.dumps({'files':{name:digest}}),encoding='utf-8')
  run=subprocess.run([str(exe),str(manifest),str(library)],capture_output=True,text=True,timeout=10)
  assert run.returncode==expected,(name,run.returncode,run.stdout,run.stderr)
  assert model.read_bytes()==original
print('Native verifier: matching/missing files accepted, conflicts/traversal refused; data preserved.')
