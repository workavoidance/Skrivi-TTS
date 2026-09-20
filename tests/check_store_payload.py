"""Check a Microsoft-MakeAppx-unpacked Store payload against its signed release."""
import argparse, hashlib, json, os, subprocess, sys, tempfile, threading, wave
import xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--unpacked',type=Path,required=True)
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];unpacked=a.unpacked.resolve()
manifest=json.loads(a.manifest.read_text(encoding='utf-8'))
identity=json.loads((root/'store/identity.json').read_text(encoding='utf-8'))
xml=ET.parse(unpacked/'AppxManifest.xml').getroot()
ns={'p':'http://schemas.microsoft.com/appx/manifest/foundation/windows10'}
actual=xml.find('p:Identity',ns)
assert actual.get('Name')==identity['name']
assert actual.get('Publisher')==identity['publisher']
assert actual.get('ProcessorArchitecture')=='x64'
assert actual.get('Version').split('.')[-1]=='0'
assert xml.find('p:Properties/p:DisplayName',ns).text=='Skrivi Lytt'
assert xml.find('p:Properties/p:PublisherDisplayName',ns).text==identity['publisher_display_name']
assert json.loads((unpacked/'app/store-build.json').read_text(encoding='utf-8'))=={'store':True,'associated':True}
assert not any('microphone' in (e.get('Name') or '').lower() for e in xml.iter())
count=0
for name,digest in manifest['files'].items():
 if not name.startswith(('app/','models/','runtimes/')):continue
 target=(unpacked/name).resolve()
 assert target.is_relative_to(unpacked),name
 with target.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest,name
 count+=1
pin=json.loads((root/'build/signed-runtime-input/runtime-manifest.json').read_text(encoding='utf-8'))
expected_runtimes={k:v for k,v in pin['files'].items() if k.startswith('runtimes/')}
actual_runtimes={k:v for k,v in manifest['files'].items() if k.startswith('runtimes/')}
assert actual_runtimes==expected_runtimes,'Runtime bytes changed under existing immutable profile names'
# Exercise the actual packaged GUI without changing the user's existing settings.
with tempfile.TemporaryDirectory() as temporary:
 env=dict(os.environ,SKRIVI_TTS_DATA=temporary)
 result=subprocess.run([str(unpacked/'app/SkriviTTS.exe'),'--check-startup'],env=env,capture_output=True,text=True,timeout=30)
 assert result.returncode==0,(result.returncode,result.stderr)
# Check the final signed OCR worker and bundled nor+eng data with a synthetic image.
fixture=root/'build/ocr-columns/en-arial.ttf-plain.png'
assert fixture.is_file(),'Generate the synthetic column fixture with tests/ocr_columns.py first'
result=subprocess.run([str(unpacked/'runtimes/tesseract-5.5.2-signed-v2/OCRWorker.exe'),str(unpacked/'models/ocr-tessdata-fast-v1'),'3'],input=fixture.read_bytes(),capture_output=True,timeout=30)
assert result.returncode==0,result.stderr.decode(errors='replace')
response=json.loads(result.stdout)
assert 'error' not in response,response
text=response['text'];assert text.index('Oslo')<text.index('Afternoon'),text
# Exercise Store asset routing and actual offline synthesis from the extracted package.
voice_results=[]
with tempfile.TemporaryDirectory() as temporary:
 os.environ['SKRIVI_TTS_DATA']=temporary
 sys.path.insert(0,str(unpacked/'app/app'))
 import core,client
 assert core.STORE_BUILD and core.ROOT==unpacked/'app'
 library=core.Library()
 for model in [m for m in core.catalog() if m['id'] in ('piper-talesyntese','kokoro-v1.0-onnx')]:
  assert library.ready(model)
  worker=client.Client()
  try:
   for repeat in range(2):
    output=Path(temporary)/(model['id']+str(repeat)+'.wav');events=[]
    request=dict(model=model,assets=str(library.path(model)),settings=core.defaults(model['engine']),text='This is a short reading test.' if model['engine']=='kokoro' else 'Dette er en kort tekst.',output=str(output),voices=str(Path(temporary)/'voices'))
    result=worker.generate(request,threading.Event(),events.append)
    assert 'generating' in events and ('loading' in events)==(repeat==0),events
    with wave.open(str(output)) as audio:
     assert audio.getnframes()>0 and audio.getnchannels()==1
     assert audio.getframerate()==(24000 if model['engine']=='kokoro' else 22050)
    voice_results.append(dict(model=model['id'],repeat=repeat,events=events,generation_seconds=result['generation_seconds']))
  finally:worker.stop()
report=dict(voice_results=voice_results,version=manifest['version'],source_commit=manifest['source_commit'],package_name=actual.get('Name'),publisher=actual.get('Publisher'),package_version=actual.get('Version'),payload_hashes_verified=count,immutable_runtime_hashes_verified=len(actual_runtimes),gui_startup=True,signed_ocr_columns=True,packaged_installation_tested=False,windows_app_certification_kit_run=False)
a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))

