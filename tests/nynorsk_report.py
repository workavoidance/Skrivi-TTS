"""Render the saved Nynorsk screening run for local listening."""
from pathlib import Path
import hashlib
import html
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'build' / 'nynorsk-2026-09-19'
synthesis = json.loads((folder / 'synthesis.json').read_text(encoding='utf-8'))
asr = json.loads((folder / 'transcripts.json').read_text(encoding='utf-8'))
transcripts = {r['file']: r['text'] for r in asr['results']}
parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Nynorsk listening comparison</title>',
    '<style>body{font:18px system-ui;max-width:950px;margin:40px auto;padding:0 24px;background:#f5f6f8;color:#18232d}article{background:white;padding:22px;margin:18px 0;border-radius:12px}audio{width:100%}small{color:#536171}blockquote{margin:16px 0;padding:12px;border-left:3px solid #687adb}</style>',
    '<h1>Nynorsk listening comparison</h1><p>19 September 2026. Native audio, default settings, CPU.</p>',
    '<p><b>Preliminary automated screen, not a pronunciation certificate.</b> Whisper may rewrite Nynorsk as Bokmal or mishear good speech. Its transcript is shown as a listening aid, not ground truth. No human quality rating has been assigned.</p>',
    '<p>Listen for: eg, ikkje, kva, ho, dei, kjem, me, hoyre, roysta, kvifor, nokon, borna, sjolv; then check every number and the sentence endings.</p>']
for row in synthesis:
    parts.append('<article><h2>'+html.escape(row.get('model',row['model_id']))+' — '+row['case']+'</h2>')
    if 'error' in row:
        parts.append('<p>No saved audio: '+html.escape(row['error'])+'</p></article>')
        continue
    file = Path(row['output']).name
    row['wav_sha256'] = hashlib.sha256((folder/file).read_bytes()).hexdigest()
    parts.extend(['<blockquote>'+html.escape(row['expected_text'])+'</blockquote>',
        '<audio controls preload="none" src="'+file+'"></audio>',
        '<p><small>Generated in %.2f s; audio %.2f s; load %.2f s.</small></p>' % (row['generation_seconds'], row['audio_seconds'], row['load_seconds']),
        '<p><b>Automatic transcript:</b> '+html.escape(transcripts.get(file,'Not transcribed'))+'</p></article>'])
parts.append('</html>')
(folder/'listen.html').write_text('\n'.join(parts),encoding='utf-8')
report = dict(synthesis=synthesis, asr=asr,
    methodology='Two synthetic Nynorsk passages; no text normalization or output processing. Installed 0.1.0 engine code verified identical. No target-text ASR prompt. Word accuracy and pronunciation remain unconfirmed pending listening.',
    timing_caveat='Diagnostic single runs, not controlled benchmarks. Dependency setup and, near the end of the failed Chatterbox word run, ASR overlapped that run. Completed Piper/Vox synthesis preceded ASR.',
    audio_folder=str(folder))
(ROOT/'docs'/'NYNORSK_SCREENING.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(folder/'asr-requirements.txt',ROOT/'docs'/'nynorsk-asr-requirements.txt')
