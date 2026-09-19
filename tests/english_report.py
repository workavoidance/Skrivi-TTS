"""Render saved English comparison and archive machine-readable evidence."""
from pathlib import Path
import difflib
import html
import json
import re
import shutil
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build'/'english-2026-09-19'
rows=json.loads((folder/'synthesis.json').read_text(encoding='utf-8'))
asr=json.loads((folder/'transcripts.json').read_text(encoding='utf-8'))
transcripts={r['file']:r['text'] for r in asr['results']}
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>English TTS comparison</title>',
'<style>body{font:18px system-ui;max-width:960px;margin:40px auto;padding:0 24px;background:#f5f6f8;color:#18232d}article{background:white;padding:22px;margin:18px 0;border-radius:12px}audio{width:100%}small{color:#536171}blockquote{margin:16px 0;padding:12px;border-left:3px solid #687adb}</style>',
'<h1>English TTS comparison</h1><p>19 September 2026. Six voice configurations, four model families. CPU, native sample rates and speed.</p>',
'<p><b>Automated screening, not a human voice-quality rating.</b> Listen for naturalness, stress, missing words and number/email pronunciation. Whisper can repair bad speech or mishear correct speech. Timings are single diagnostic runs and exclude initial loading.</p>']
for row in sorted(rows,key=lambda r:(r['case'],r['model_id'])):
    parts.append('<article><h2>'+html.escape(row['model'])+' — '+row['case']+'</h2>')
    if 'error' in row:
        parts.append('<p>'+html.escape(row['error'])+'</p></article>');continue
    name=Path(row['output']).name
    row['automatic_transcript']=transcripts.get(name,'')
    if row['case']=='reading':
        normalize=lambda s: re.findall(r"[a-z]+(?:'[a-z]+)?",s.lower())
        expected=normalize(row['text']);observed=normalize(row['automatic_transcript'])
        row['reading_exact_transcript_match']=expected==observed
        row['reading_token_count']=len(expected)
        row['reading_differences']=[dict(expected=' '.join(expected[i:j]),observed=' '.join(observed[k:l])) for op,i,j,k,l in difflib.SequenceMatcher(a=expected,b=observed,autojunk=False).get_opcodes() if op!='equal']
    parts.extend(['<blockquote>'+html.escape(row['text'])+'</blockquote>',
        '<audio controls preload="none" src="'+name+'"></audio>',
        '<p><small>Generation %.2f s; audio %.2f s; %.1f times faster than playback.</small></p>'%(row['generation_seconds'],row['audio_seconds'],row['audio_seconds']/row['generation_seconds']),
        '<p><b>Automatic transcript:</b> '+html.escape(row['automatic_transcript'])+'</p></article>'])
parts.append('</html>')
(folder/'listen.html').write_text('\n'.join(parts),encoding='utf-8')
(ROOT/'docs'/'ENGLISH_SCREENING.json').write_text(json.dumps(dict(synthesis=rows,asr=asr,limitation='Single runs; ASR agreement is not acoustic correctness, naturalness, or a benchmark-wide accuracy score.'),ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(folder/'kokoro-requirements.txt',ROOT/'docs'/'english-kokoro-requirements.txt')
for row in rows:
    print(row['model_id'],row['case'],row.get('generation_seconds'),row.get('audio_seconds'),row.get('reading_differences'),row.get('automatic_transcript',row.get('error')))
