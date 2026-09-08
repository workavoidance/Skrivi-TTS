# Skrivi TTS

A Windows application for local text-to-speech and repeatable model comparisons.
It continues the existing Norwegian TTS shootout and VoxCPM2 Reader work, in a
separate repository from Skrivi's speech-to-text application.

## Install or update

Download the Windows ZIP from [Releases](https://github.com/workavoidance/Skrivi-TTS/releases),
extract it, and double-click **INSTALL.bat**. No administrator account or separately
installed Python is required. Start **Skrivi TTS** from the Start menu or desktop.

Models, presets, reference voices, settings and generated audio live permanently in
`%LOCALAPPDATA%\SkriviTTS`. App versions are separate under `versions`. Installing
another version does not delete the library or download models again. The engine
runtime is cached separately under `runtimes` and unchanged files are reused.
The installer itself makes no network requests. Model downloads happen only when
you choose **Download selected** inside the app.

## Read and compare

Choose a model, enter text, adjust its settings, and click **Generate & listen**.
The complete WAV plays through Windows at its original sample rate. Models stay
loaded while you use the same settings; the history distinguishes cold and warm
runs. Changing model/settings reloads the engine. **Stop / unload model** cancels
generation or playback and releases model memory.

Save named presets, replay past results, rate listening quality from 1 to 5, and
restore a past run's settings. Each audio file has a JSON record of the model
revision, settings, application version, CPU device, timings and rating. Input text
is not logged or persisted. Audio and reference voices necessarily contain speech;
keep the local library somewhere appropriate for your recordings.

The Model library tab can download a pinned model, import existing files into the
permanent library, or verify checksums. Imports copy once and preserve the originals.
No synthesis request uploads text or audio. VoxCPM2 uses authenticated loopback
communication with its locally owned runtime.

## Version 0.1.0 engines

| Model | Controls | Native output |
| --- | --- | --- |
| Public VoxCPM2 Q4 | Seed, diffusion steps, guidance, CPU threads, optional reference WAV | 48 kHz |
| Chatterbox Multilingual Q4 ONNX | Seed, CPU threads, Norwegian/English, exaggeration, repetition penalty, token safety limit, optional reference WAV | 24 kHz |
| Piper NVCC | Ten speakers, speed relative to native cadence, noise scale and width | 22.05 kHz |
| Piper Talesyntese | Native-relative speed, noise scale and width | 22.05 kHz |

All current adapters use **CPU**. GPU support will be added only after an actual
compatible runtime has been measured. The adapter registry is designed for more
models; these four are the implemented engines, not a promise that arbitrary model
formats can be loaded. Controls tune inference; this app does not train model weights.

VoxCPM2 defaults to seed 42, 10 steps, guidance 2 and native speed. It retains the
existing adapter's 4,096-character limit; longer-text handling remains planned.
Chatterbox uses greedy decoding and refuses to save audio if the token safety limit
is reached without a natural ending. First load can take around 40 seconds on the
tested PC; warm readings avoid that repeated load. A seed does not guarantee a
particular gender or identical results across runtime versions.

Reference WAVs must be mono PCM16, 2–20 seconds, under 2 MB. Vox accepts 16–48 kHz;
Chatterbox requires native 24 kHz. No automatic resampling is applied. Use your own
voice or one you have permission to use, and identify shared output as AI-generated.

## Development

Windows x64 with Python 3.12 and .NET Framework 4.8:

```powershell
python -m venv .build-env
.\.build-env\Scripts\python.exe -m pip install -r requirements-build.lock
.\.build-env\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
.\scripts\build.ps1
.\.build-env\Scripts\python.exe scripts/package.py --vox-runtime C:\path\to\pinned-crispasr-runtime
```

The package script takes the already available CrispASR v0.8.32 runtime directory
(binary, OpenBLAS and notices). It never downloads model weights. Runtime/source
provenance and the recovery instructions are in `docs/ARCHITECTURE.md` and
`THIRD_PARTY_NOTICES.md`. For ordinary code changes, reuse the published dependency
runtime; update its profile ID when changing bundled dependencies.

`tests/check_engines.py` is an opt-in real-model test against the installed library.
`scripts/import_existing.py` performs a one-time import from the previous local
shootout/Reader caches, with no network calls. Launch from source with
`.\.build-env\Scripts\python.exe app/main.py` after installing the native runtime.

See **PROJECT_STATUS.md** before continuing work. The prior inventory is retained
in `docs/PREVIOUS_PROJECT_STATUS.md`; do not restart old model research or replace
the engine implementations merely because a new conversation lacks context.
