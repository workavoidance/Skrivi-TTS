"""Offline, CPU-only Norwegian Chatterbox Q4 quality experiment.

Follows the ONNX exporter inference at b8b5f7f75436de240639e777dce2b7e26a305681.
Preserves its greedy decoding, repetition penalty 1.2, exaggeration 0.5,
native default reference and 24 kHz output. Sessions persist between samples.
No selected-text capture, network access, resampling, trimming or speed control.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

PROCESS_START = time.perf_counter()
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

def offline_guard(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo'}:
        raise RuntimeError('Network access forbidden during this offline benchmark')

sys.addaudithook(offline_guard)
import numpy as np
import onnxruntime as ort
import psutil
import soundfile as sf
from tokenizers import Tokenizer

ROOT = Path(os.environ.get('TTS_LAB_ROOT', Path(__file__).resolve().parent))
ASSETS = ROOT / 'models' / 'chatterbox-q4'
START, STOP = 6561, 6562
SAMPLES = [
    ('short-cold', 'Hei! Dette er en prøve på norsk tale.'),
    ('short-warm', 'Hei! Dette er en prøve på norsk tale.'),
    ('paragraph', 'Dette er en test av norsk talesyntese. Målet er å finne en stemme som er '
     'tydelig, naturlig og behagelig å høre på over lengre tid. I 2026 kostet boka '
     '349 kroner, og eleven skulle lese kapittel sju på side 128. På vei hjem fra '
     'skolen tok han trikken gjennom Oslo sentrum, mens regnet slo mot vinduet.'),
]

def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def folder_bytes(path):
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

def cpu_seconds(proc):
    times = proc.cpu_times()
    return times.user + times.system

class Engine:
    def __init__(self, threads, settings=None):
        self.settings = settings or {'seed': 2607, 'language': 'no', 'exaggeration': 0.5, 'repetition_penalty': 1.2}
        ort.set_seed(self.settings['seed'])
        self.tokenizer = Tokenizer.from_file(str(ASSETS / 'tokenizer.json'))
        self.sessions = {}
        self.load_times = {}
        for name in ['speech_encoder', 'embed_tokens', 'language_model_q4', 'conditional_decoder']:
            print(f'Loading {name}', flush=True)
            options = ort.SessionOptions()
            options.intra_op_num_threads = threads
            options.inter_op_num_threads = 1
            options.log_severity_level = 3
            started = time.perf_counter()
            session = ort.InferenceSession(str(ASSETS / 'onnx' / f'{name}.onnx'),
                                          sess_options=options, providers=['CPUExecutionProvider'])
            if session.get_providers() != ['CPUExecutionProvider']:
                raise RuntimeError('Unexpected execution provider')
            self.sessions[name] = session
            self.load_times[name] = time.perf_counter() - started
        ref, sr = sf.read(self.settings.get('reference') or ASSETS / 'default_voice.wav', dtype='float32')
        if sr != 24000 or ref.ndim != 1:
            raise ValueError('Reference must already be native mono 24 kHz')
        self.reference = ref[None, :]

    def synthesize(self, text, max_tokens=2048):
        ids = np.array([self.tokenizer.encode('[' + self.settings['language'] + ']' + text).ids], dtype=np.int64)
        if ids[0, 0] != 6563 or ids[0, -2:].tolist() != [START, START]:
            raise ValueError('Tokenizer template mismatch')
        positions = np.where(ids >= START, 0, np.arange(ids.shape[1])[None, :] - 1)
        embedding_input = {'input_ids': ids, 'position_ids': positions.astype(np.int64),
                           'exaggeration': np.array([self.settings['exaggeration']], dtype=np.float32)}
        tokens = np.array([[START]], dtype=np.int64)
        token_start = time.perf_counter()
        for index in range(max_tokens):
            embeds = self.sessions['embed_tokens'].run(None, embedding_input)[0]
            if index == 0:
                cond, prompt, speaker, features = self.sessions['speech_encoder'].run(
                    None, {'audio_values': self.reference})
                embeds = np.concatenate((cond, embeds), axis=1)
                batch, length, _ = embeds.shape
                cache = {f'past_key_values.{layer}.{kind}': np.zeros((batch, 16, 0, 64), dtype=np.float32)
                         for layer in range(30) for kind in ('key', 'value')}
                mask = np.ones((batch, length), dtype=np.int64)
            logits, *present = self.sessions['language_model_q4'].run(None, {
                'inputs_embeds': embeds, 'attention_mask': mask, **cache})
            scores = logits[:, -1, :].copy()
            repeated = np.take_along_axis(scores, tokens, axis=1)
            penalty = self.settings['repetition_penalty']
            np.put_along_axis(scores, tokens, np.where(repeated < 0, repeated * penalty, repeated / penalty), axis=1)
            next_token = np.argmax(scores, axis=-1, keepdims=True).astype(np.int64)
            tokens = np.concatenate((tokens, next_token), axis=-1)
            if (next_token == STOP).all():
                break
            embedding_input['input_ids'] = next_token
            embedding_input['position_ids'] = np.full((ids.shape[0], 1), index + 1, dtype=np.int64)
            mask = np.concatenate((mask, np.ones((batch, 1), dtype=np.int64)), axis=1)
            cache = dict(zip(cache, present))
            if index and index % 100 == 0:
                print(f'  Generated {index} speech tokens', flush=True)
        else:
            raise RuntimeError('No natural stop token; refusing to save truncated speech')
        token_seconds = time.perf_counter() - token_start
        decoder_start = time.perf_counter()
        wav = self.sessions['conditional_decoder'].run(None, {
            'speech_tokens': np.concatenate((prompt, tokens[:, 1:-1]), axis=1),
            'speaker_embeddings': speaker, 'speaker_features': features})[0]
        wav = np.squeeze(wav)
        if wav.ndim != 1 or not wav.size or not np.isfinite(wav).all():
            raise ValueError('Invalid generated waveform')
        return wav, {'speech_tokens': tokens.shape[1] - 2, 'natural_stop': True,
                     'token_generation_seconds': token_seconds,
                     'wave_decoder_seconds': time.perf_counter() - decoder_start}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, default=8)
    parser.add_argument('--play', action='store_true', help='Synchronous Windows playback after full WAV')
    parser.add_argument('--short-only', action='store_true')
    parser.add_argument('--run-name', default='cpu-q4')
    args = parser.parse_args()
    output = ROOT / 'results' / args.run_name
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((ROOT / 'download-manifest.json').read_text(encoding='utf-8'))
    if not manifest['complete']:
        raise ValueError('Model download incomplete')
    print('Verifying model asset hashes', flush=True)
    integrity_start = time.perf_counter()
    for item in manifest['files']:
        if file_hash(ASSETS / item['path']) != item['sha256']:
            raise ValueError(f'Asset checksum mismatch: {item["path"]}')
    integrity_seconds = time.perf_counter() - integrity_start
    proc = psutil.Process()
    before_load = cpu_seconds(proc)
    load_start = time.perf_counter()
    engine = Engine(args.threads)
    load_seconds = time.perf_counter() - load_start
    report = {'model': manifest['repository'], 'revision': manifest['revision'],
              'variant': 'language_model_q4 with FP32 companions', 'voice': 'bundled default_voice.wav',
              'platform': sys.platform, 'python': sys.version, 'onnxruntime': ort.__version__,
              'provider': 'CPUExecutionProvider', 'gpu_required': False, 'threads': args.threads,
              'offline': 'Only local assets; Python socket connections and DNS forbidden; ORT telemetry disabled',
              'native_settings': {'language': 'no', 'exaggeration': 0.5, 'repetition_penalty': 1.2,
                                  'decoding': 'greedy as ONNX exporter example', 'ort_seed': 2607,
                                  'postprocessing': 'PCM16 encoding only; no resampling/trim/speed change'},
              'model_asset_bytes': manifest['total_asset_bytes'],
              'environment_bytes': folder_bytes(ROOT / '.venv'),
              'hash_verification_seconds': integrity_seconds, 'model_load_seconds': load_seconds,
              'model_load_cpu_seconds': cpu_seconds(proc) - before_load,
              'session_load_seconds': engine.load_times,
              'script_entry_to_ready_seconds': time.perf_counter() - PROCESS_START,
              'samples': [], 'quality_verdict': 'Awaiting human listening; no female Oslo equivalence claimed'}
    for name, text in SAMPLES[:2] if args.short_only else SAMPLES:
        print(f'Synthesizing {name}', flush=True)
        started = time.perf_counter()
        cpu_started = cpu_seconds(proc)
        wav, details = engine.synthesize(text)
        generation_seconds = time.perf_counter() - started
        cpu_used = cpu_seconds(proc) - cpu_started
        target = output / (name + '.wav')
        sf.write(target, wav, 24000, subtype='PCM_16')
        info = sf.info(target)
        if info.frames != len(wav) or info.samplerate != 24000 or info.channels != 1:
            raise ValueError('WAV does not preserve generated frames')
        ready_seconds = time.perf_counter() - started
        audio_seconds = len(wav) / 24000
        memory = proc.memory_info()
        result = {'name': name, 'text': text, 'generation_seconds': generation_seconds,
                  'wav_ready_seconds': ready_seconds, 'playback_call_seconds': None,
                  'synchronous_playback_completed': False,
                  'physical_time_to_first_audio_seconds': None,
                  'audio_seconds': audio_seconds, 'real_time_factor': generation_seconds / audio_seconds,
                  'audio_seconds_per_second': audio_seconds / generation_seconds,
                  'cpu_seconds': cpu_used, 'average_cpu_cores': cpu_used / generation_seconds,
                  'cpu_percent_machine': 100 * cpu_used / generation_seconds / psutil.cpu_count(),
                  'peak_process_ram_bytes': getattr(memory, 'peak_wset', memory.rss),
                  'working_set_bytes': memory.rss, 'sample_rate': 24000, 'frames': len(wav),
                  'pcm_clipped_sample_fraction': float(np.mean(np.abs(wav) >= 1)),
                  'file': target.name, 'sha256': file_hash(target), **details}
        report['samples'].append(result)
        (output / 'benchmark.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        if args.play:
            import winsound
            result['playback_call_seconds'] = time.perf_counter() - started
            try:
                # Synchronous is the default (flag value zero); Python 3.12 has no SND_SYNC name.
                winsound.PlaySound(str(target), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                result['synchronous_playback_completed'] = True
            except Exception as error:
                result['playback_error'] = str(error)
                raise
            finally:
                (output / 'benchmark.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps({key: result[key] for key in ['name', 'generation_seconds', 'audio_seconds',
              'real_time_factor', 'peak_process_ram_bytes']}, ensure_ascii=True), flush=True)

if __name__ == '__main__':
    ort.disable_telemetry_events()
    main()
