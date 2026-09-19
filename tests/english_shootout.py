"""Opt-in English comparison using permanent cached weights; no downloads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from core import DATA, catalog, defaults, write_json
from client import Client
FOLDER = ROOT / 'build' / 'english-2026-09-19'
PASSAGES = {
    'reading': "The rain had stopped by the time we reached the station. Sarah looked at the empty platform and smiled. We had missed the last train, but neither of us was in a hurry to go home.",
    'details': "Dr. Smith paid $12.50 for three books on September 21, 2026. The meeting starts at 9:30 a.m. in room 204. Please email support@example.com, and don't forget your ID.",
}

def save(row):
    report = FOLDER / 'synthesis.json'
    rows = json.loads(report.read_text(encoding='utf-8')) if report.exists() else []
    if row.get('output'):
        path = Path(row['output'])
        with path.open('rb') as f:
            row['wav_sha256'] = hashlib.file_digest(f,'sha256').hexdigest()
        with wave.open(str(path)) as f:
            row.update(sample_rate=f.getframerate(), audio_seconds=f.getnframes()/f.getframerate())
    rows = [r for r in rows if not (r['model_id']==row['model_id'] and r['case']==row['case'])]
    rows.append(row)
    write_json(report, rows)
    print(json.dumps(row,ensure_ascii=True),flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', choices=['installed','kokoro'], required=True)
    args = parser.parse_args()
    FOLDER.mkdir(parents=True,exist_ok=True)
    write_json(FOLDER / 'passages.json',PASSAGES)
    report=FOLDER/'synthesis.json'
    done={(r['model_id'],r['case']) for r in json.loads(report.read_text(encoding='utf-8')) if 'error' not in r} if report.exists() else set()
    if args.group == 'installed':
        models = {m['id']:m for m in catalog()}
        manifest=json.loads((FOLDER/'model-manifest.json').read_text(encoding='utf-8'))
        models['piper-ljspeech-high']=dict(id='piper-ljspeech-high',name='Piper LJSpeech',engine='piper',
            revision='1162a9173d0ce503555aed757976b7a9912eae4c',
            files=[f for f in manifest if f['model']=='piper-ljspeech-high' and f['path'].endswith('.onnx')])
        client=Client()
        try:
            for mid in ('piper-ljspeech-high','voxcpm-q4','chatterbox-q4'):
                model=models[mid];settings=defaults(model['engine'])
                if model['engine']=='chatterbox': settings['language']='en'
                for case,text in PASSAGES.items():
                    if (mid,case) in done: continue
                    print('Generating '+mid+' '+case,flush=True)
                    target=FOLDER/(mid+'-'+case+'.wav')
                    start=time.perf_counter()
                    try:
                        row=client.generate(dict(model=model,assets=str(DATA/'models'/mid),settings=settings,
                            text=text,output=str(target),voices=str(DATA/'voices'),
                            vox_runtime=str(DATA/'runtimes'/'vox-0.8.32')),threading.Event())
                        row.update(case=case,text=text,total_wait_seconds=time.perf_counter()-start)
                    except Exception as exc:
                        row=dict(model_id=mid,model=model['name'],case=case,text=text,error=str(exc),
                                 total_wait_seconds=time.perf_counter()-start)
                    save(row)
        finally:
            if client.process and client.process.poll() is None:
                client.process.stdin.close()
                try: client.process.wait(timeout=15)
                except Exception: client.stop()
    else:
        import onnxruntime as ort
        import soundfile as sf
        from kokoro_onnx import Kokoro
        from misaki import en, espeak
        # Explicit CPU, FP32 and unmodified default speed. No GPU or quantization.
        opts=ort.SessionOptions();opts.intra_op_num_threads=8;opts.inter_op_num_threads=1
        ort.disable_telemetry_events()
        start=time.perf_counter()
        assets=DATA/'models'/'kokoro-v1.0-onnx'
        session=ort.InferenceSession(str(assets/'kokoro-v1.0.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
        engine=Kokoro.from_session(session,str(assets/'voices-v1.0.bin'))
        # kokoro-onnx 0.4.9 incorrectly sends int32 speed for this export.
        # Follow the actual ONNX input schema; preserve the value 1.0.
        import numpy as np
        assert next(i.type for i in session.get_inputs() if i.name=='speed')=='tensor(float)'
        class FloatSpeedSession:
            def get_inputs(self): return session.get_inputs()
            def run(self, outputs, inputs):
                inputs=dict(inputs)
                inputs['speed']=np.asarray(inputs['speed'],dtype=np.float32)
                return session.run(outputs,inputs)
        engine.sess=FloatSpeedSession()
        load=time.perf_counter()-start
        for voice,british,label in [('af_heart',False,'Heart, American female'),('am_michael',False,'Michael, American male'),('bf_emma',True,'Emma, British female')]:
            g2p=en.G2P(trf=False,british=british,fallback=espeak.EspeakFallback(british=british))
            mid='kokoro-'+voice
            for case,text in PASSAGES.items():
                if (mid,case) in done: continue
                start=time.perf_counter()
                try:
                    phonemes,_=g2p(text)
                    if '❓' in phonemes: raise ValueError('Unresolved phoneme')
                    audio,sr=engine.create(phonemes,voice=voice,speed=1.0,is_phonemes=True,trim=False)
                    generation=time.perf_counter()-start
                    target=FOLDER/(mid+'-'+case+'.wav')
                    sf.write(str(target),audio,sr,subtype='PCM_16')
                    row=dict(model_id=mid,model='Kokoro '+label,case=case,text=text,phonemes=phonemes,
                        generation_seconds=generation,load_seconds=load,output=str(target),
                        device='CPU',threads=8,voice=voice,speed=1.0,format='FP32 ONNX',
                        frontend='Misaki 0.9.4 en.G2P with espeak fallback',trim=False,speed_dtype_fix='float32 per ONNX schema')
                except Exception as exc:
                    row=dict(model_id=mid,model='Kokoro '+label,case=case,text=text,error=str(exc))
                save(row)

if __name__=='__main__': main()
