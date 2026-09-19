"""CI-only smoke test of both unmodified engines installed by the EXE."""
import json
import os
from pathlib import Path
import subprocess
import sys
import wave

if os.environ.get("GITHUB_ACTIONS") != "true":
    raise SystemExit("Run only in the disposable installer CI job.")
library = Path(os.environ["LOCALAPPDATA"]) / "SkriviTTS"
app = library / "versions/0.2.1"
sys.path.insert(0, str(app / "app"))
from core import catalog, defaults

output = Path(__file__).resolve().parents[1] / "build/installer-tests"
rows = []
for model_id, worker, text, rate in (
    ("piper-talesyntese", "python-engine-v1/SkriviWorker.exe",
     "Dette er en norsk tekst som blir lest opp.", 22050),
    ("kokoro-v1.0-onnx", "kokoro-engine-v1/KokoroWorker.exe",
     "This is a short reading test on a clean Windows computer.", 24000),
):
    target = output / (model_id + ".wav")
    model = next(m for m in catalog() if m["id"] == model_id)
    request = dict(model=model, assets=str(library / "models" / model_id),
                   settings=defaults(model["engine"]), text=text,
                   output=str(target), voices=str(library / "voices"))
    result = subprocess.run(
        [str(library / "runtimes" / worker), str(app / "engines/worker.py")],
        input=json.dumps(request) + "\n", capture_output=True, text=True,
        encoding="utf-8", timeout=180, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        raise RuntimeError(f"{model_id}: worker exit {result.returncode}")
    response = json.loads(result.stdout.strip())
    assert response["ok"], response
    with wave.open(str(target)) as audio:
        assert audio.getframerate() == rate and audio.getnframes() > 0
        assert audio.getnchannels() == 1
    rows.append(dict(model=model_id, sample_rate=rate, result=response["result"]))
(output / "voices.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("Installed Norwegian and English voices passed.")
