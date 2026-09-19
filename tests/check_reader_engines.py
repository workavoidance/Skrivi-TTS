"""Opt-in frozen worker smoke test; uses cached weights and never downloads."""
import json,os,subprocess,sys,threading,time,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from core import DATA,catalog,defaults

def main():
    folder=ROOT/'build/reader-verification';folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    for mid,runtime,text,rate in [
        ('kokoro-v1.0-onnx',ROOT/'dist/KokoroWorker/KokoroWorker.exe','The rain had stopped by the time we reached the station.',24000),
        ('piper-talesyntese',DATA/'runtimes/python-engine-v1/SkriviWorker.exe','Dette er en norsk tekst som blir lest opp paa datamaskinen.',22050)]:
        model=next(m for m in catalog() if m['id']==mid)
        process=subprocess.Popen([str(runtime),str(ROOT/'engines/worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        timeout=threading.Timer(180,process.kill);timeout.start()
        try:
            for index in range(2):
                target=folder/(mid+'-'+str(index)+'.wav')
                request=dict(model=model,assets=str(DATA/'models'/mid),settings=defaults(model['engine']),text=text,output=str(target),voices=str(DATA/'voices'))
                started=time.perf_counter();process.stdin.write(json.dumps(request)+'\n');process.stdin.flush()
                response=json.loads(process.stdout.readline());assert response['ok'],response
                row=response['result'];row['total_wait_seconds']=time.perf_counter()-started
                assert row['warm']==bool(index),row
                with wave.open(str(target)) as wav:
                    assert wav.getframerate()==rate and wav.getnframes()>0 and wav.getnchannels()==1
                row['output']=target.name;rows.append(row);print(json.dumps(row),flush=True)
        finally:
            process.stdin.close();process.wait(timeout=15);timeout.cancel()
    (folder/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')

if __name__=='__main__':main()
