"""Persistent local engine process. JSON lines in/out; selected text is never logged."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import wave

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'app'))
from core import validate

class Session:
    def __init__(self):
        self.key = None
        self.engine = None
        self.vox = None

    def close(self):
        if self.vox and self.vox.poll() is None:
            self.vox.stdin.close()
            try:
                self.vox.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.vox.kill()
                self.vox.wait()
        self.vox = None
        self.engine = None
        self.key = None

    def run(self, request):
        import psutil
        model = request['model']
        settings = validate(model['engine'], request['settings'])
        assets = Path(request['assets'])
        output = request['output']
        key = (model['id'], str(assets), json.dumps(settings, sort_keys=True))
        warm = key == self.key
        if not warm:
            self.close()
        load = time.perf_counter()
        if model['engine'] == 'voxcpm':
            if not self.vox:
                model_file = assets / model['files'][0]['path']
                with model_file.open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != model['files'][0]['sha256']:
                        raise ValueError('Vox model checksum mismatch. Verify it in Models.')
                environment = os.environ.copy()
                environment['SKRIVI_TTS_RUNTIME'] = request['vox_runtime']
                self.vox = subprocess.Popen([str(ROOT / 'native' / 'VoxHost.exe'), str(model_file), request['voices']],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW, env=environment)
            cfg = {'Seed': settings['seed'], 'Steps': settings['steps'], 'Guidance': settings['guidance'],
                   'Threads': settings['threads'], 'Reference': settings['reference'],
                   'Consent': 'User confirmed permission to use this voice.' if settings['consent'] else ''}
            self.vox.stdin.write(json.dumps({'text': request['text'], 'output': output, 'settings': cfg}) + '\n')
            self.vox.stdin.flush()
            result = json.loads(self.vox.stdout.readline())
            if not result['ok']:
                raise RuntimeError(result['error'])
            result['load_seconds'] = time.perf_counter() - load - result['generation_seconds']
        else:
            if not warm:
                import onnxruntime as ort
                ort.disable_telemetry_events()
                if model['engine'] == 'chatterbox':
                    import chatterbox
                    chatterbox.ASSETS = assets
                    engine_settings = dict(settings)
                    if engine_settings.get('reference'):
                        engine_settings['reference'] = str(Path(request['voices']) / engine_settings['reference'])
                    self.engine = chatterbox.Engine(settings['threads'], engine_settings)
                elif model['engine'] == 'kokoro':
                    from kokoro_engine import Engine
                    self.engine = Engine(assets, settings)
                elif model['engine'] == 'piper':
                    from piper import PiperVoice
                    self.engine = PiperVoice.load(assets / model['files'][0]['path'], use_cuda=False)
                else:
                    raise ValueError('Unknown engine adapter: ' + model['engine'])
            load_seconds = time.perf_counter() - load
            started = time.perf_counter()
            if model['engine'] == 'kokoro':
                import soundfile as sf
                wav, rate = self.engine.synthesize(request['text'])
                sf.write(output, wav, rate, subtype='PCM_16')
                extra = {}
            elif model['engine'] == 'chatterbox':
                import soundfile as sf
                wav, extra = self.engine.synthesize(request['text'], settings['max_tokens'])
                sf.write(output, wav, 24000, subtype='PCM_16')
            else:
                from piper import SynthesisConfig
                # Native speed is deliberately not overridden at 1.0.
                config = SynthesisConfig(speaker_id=settings['speaker'] if model['id'] == 'piper-nvcc' else None,
                    length_scale=None if settings['speed'] == 1 else self.engine.config.length_scale / settings['speed'],
                    noise_scale=None if settings['noise_scale'] == '' else settings['noise_scale'],
                    noise_w_scale=None if settings['noise_w_scale'] == '' else settings['noise_w_scale'])
                with wave.open(output, 'wb') as stream:
                    self.engine.synthesize_wav(request['text'], stream, syn_config=config)
                extra = {}
            generation = time.perf_counter() - started
            with wave.open(output) as stream:
                duration = stream.getnframes() / stream.getframerate()
                sample_rate = stream.getframerate()
            result = {'load_seconds': load_seconds, 'generation_seconds': generation,
                      'audio_seconds': duration, 'sample_rate': sample_rate, **extra}
        self.key = key
        result.update(warm=warm, settings=settings, model_id=model['id'], model=model['name'],
                      revision=model['revision'], device='CPU', real_time_factor=result['generation_seconds'] / result['audio_seconds'],
                      worker_peak_ram_bytes=psutil.Process().memory_info().peak_wset, output=output)
        return result

def main():
    session = Session()
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                # Upstream progress messages must not corrupt the protocol or expose input.
                with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                    result = session.run(request)
                response = {'ok': True, 'result': result}
            except Exception as error:
                session.close()
                response = {'ok': False, 'error': str(error)}
            print(json.dumps(response), flush=True)
    finally:
        session.close()

if __name__ == '__main__':
    main()
