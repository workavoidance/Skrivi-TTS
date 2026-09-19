"""Offline ASR screen, not a pronunciation score. No target text is prompted."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--folder', required=True, type=Path)
    parser.add_argument('--file', help='Transcribe only this WAV and preserve other results')
    args = parser.parse_args()
    from faster_whisper import WhisperModel
    with (args.model / 'model.bin').open('rb') as stream:
        fingerprint = hashlib.file_digest(stream, 'sha256').hexdigest()
    model = WhisperModel(str(args.model), device='cpu', compute_type='int8',
                         cpu_threads=8, local_files_only=True)
    report_path = args.folder / 'transcripts.json'
    results = json.loads(report_path.read_text(encoding='utf-8'))['results'] if args.file and report_path.exists() else []
    for path in sorted(args.folder.glob('*.wav')):
        if args.file and path.name != args.file:
            continue
        results = [r for r in results if r['file'] != path.name]
        start = time.perf_counter()
        segments, info = model.transcribe(str(path), language='no', task='transcribe',
            beam_size=5, temperature=0, condition_on_previous_text=False,
            vad_filter=False, word_timestamps=True)
        segments = list(segments)
        result = dict(file=path.name, text=' '.join(s.text.strip() for s in segments),
            seconds=time.perf_counter()-start,
            segments=[dict(start=s.start, end=s.end, text=s.text,
                           avg_logprob=s.avg_logprob) for s in segments])
        results.append(result)
        report = dict(asr_model=str(args.model), model_sha256=fingerprint,
            packages={k:importlib.metadata.version(k) for k in ('faster-whisper','ctranslate2','av')},
            settings=dict(language='no', task='transcribe', compute_type='int8', device='cpu',
                beam_size=5, temperature=0, condition_on_previous_text=False,
                vad_filter=False, initial_prompt=None),
            limitation='ASR can normalize Nynorsk to Bokmal or repair mispronunciation. '
                       'Disagreements are candidates for human listening, not confirmed TTS errors.',
            results=results)
        (args.folder/'transcripts.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),encoding='utf-8')
        print(json.dumps(result, ensure_ascii=True), flush=True)

if __name__ == '__main__':
    main()
