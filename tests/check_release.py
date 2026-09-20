"""Smoke-test signed staged engines and protocol; does not touch user settings."""
import sys,os,json,threading,wave,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'app'))
import core
payload=root/'build/release-payload';core.ROOT=payload/'app';core.DATA=payload
import client
client.ROOT=core.ROOT;client.DATA=payload
results=[]
for model in [m for m in core.catalog() if m['id'] in ('piper-talesyntese','kokoro-v1.0-onnx')]:
 c=client.Client()
 try:
  for repeat in range(2):
   output=root/'build'/('release-'+model['id']+str(repeat)+'.wav');events=[]
   req=dict(model=model,assets=str(payload/'models'/model['id']),settings=core.defaults(model['engine']),text='This is a short reading.' if model['engine']=='kokoro' else 'Dette er en kort tekst.',output=str(output),voices=str(payload/'voices'))
   r=c.generate(req,threading.Event(),events.append)
   assert 'generating' in events,events
   assert ('loading' in events)==(repeat==0),events
   with wave.open(str(output)) as wav:assert wav.getnframes()>0
   results.append(dict(model=model['id'],repeat=repeat,events=events,generation_seconds=r['generation_seconds']))
 finally:c.stop()
(root/'build/RELEASE-ENGINE-CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Both signed engines passed cold/warm generation and actual progress events.')
