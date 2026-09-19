"""Opt-in Nynorsk synthesis fixture; uses installed models without downloads.

Generated test text is public synthetic material, not user input. ASR agreement
is a diagnostic, not a pronunciation or Nynorsk certification.
"""
import json
import argparse
from pathlib import Path
import sys
import threading
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from core import DATA, catalog, defaults, write_json
from client import Client

PASSAGES = {
    'words': 'Eg veit ikkje kva ho meiner. Dei kjem heim i morgon. Me ønskjer å høyre røysta di. Kvifor finn de ikkje nøkkelen? Nokon må hjelpe borna våre. Sjølv om det regnar, går eg ein tur.',
    'numbers': 'Møtet byrjar klokka 14.30 den 21. september. Billetten kostar 349 kroner. Me har kjøpt 12 eple og 3 bøker. Toget går frå spor 4.',
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+', default=['piper-talesyntese', 'voxcpm-q4', 'chatterbox-q4'])
    parser.add_argument('--cases', nargs='+', choices=list(PASSAGES), default=list(PASSAGES))
    args = parser.parse_args()
    folder = ROOT / 'build' / 'nynorsk-2026-09-19'
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / 'passages.json', PASSAGES)
    report = folder / "synthesis.json"
    results = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
    client = Client()
    try:
        models = {m['id']: m for m in catalog()}
        for model_id in args.models:
            model = models[model_id]
            settings = defaults(model['engine'])
            for case, text in PASSAGES.items():
                if case not in args.cases:
                    continue
                if any(r.get('model_id', r.get('model')) == model_id and r.get('case') == case for r in results):
                    continue
                output = folder / f'{model_id}-{case}.wav'
                print(f'Generating {model_id}: {case}', flush=True)
                try:
                    result = client.generate({
                        'model': model, 'assets': str(DATA / 'models' / model_id),
                        'settings': settings, 'text': text, 'output': str(output),
                        'voices': str(DATA / 'voices'),
                        'vox_runtime': str(DATA / 'runtimes' / 'vox-0.8.32'),
                    }, threading.Event())
                    with wave.open(str(output)) as wav:
                        assert wav.getnframes() > 0
                        assert wav.getframerate() == result['sample_rate']
                    result.update(case=case, expected_text=text, settings=settings,
                                  revision=model['revision'])
                except Exception as exc:
                    result = dict(model_id=model_id, case=case, error=str(exc))
                results.append(result)
                write_json(folder / 'synthesis.json', results)
                print(json.dumps(result, ensure_ascii=True), flush=True)
    finally:
        if client.process and client.process.poll() is None:
            client.process.stdin.close()
            try:
                client.process.wait(timeout=15)
            except Exception:
                client.stop()

if __name__ == '__main__':
    main()
