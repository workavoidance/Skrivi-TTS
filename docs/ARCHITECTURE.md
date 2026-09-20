# Skrivi Lytt architecture

Public name: Skrivi Lytt. Internal `SkriviTTS` identifiers, paths and executable
names remain stable. The separate dictation app is Skrivi Snakk. Historical
architecture snapshots below retain their original names.

## OCR input in 0.3.0

app/screen_region.py freezes the pointer monitor before drawing its overlay; crop
coordinates map Qt logical units to physical pixels. OCR bytes use stdin/stdout of
an isolated frozen ocr_host.py process, with cancellation and timeout. No image is
written to disk. app/main.py rejects stale results through capture_generation and
passes recognised text to the existing synthesis path. Model/runtime assets are
persistent, outside app versions. See docs/OCR_SCREENING.md for scope and evidence.

# Reader 0.2 architecture update

The current front end is app/main.py (PySide6), not Tk. The prior compare/preset/history
front end is retained in app/shootout.py. Models and original inference adapters are
reused. Theme is adapted from Skrivi STT main commit 05ed960; apps have separate
processes, shortcuts, settings and tray icons.

app/reader_core.py owns whole-passage language routing and reader preferences.
app/windows_reader.py owns global shortcuts, clipboard-copy input and native WAV
playback. native/Selection.cs reads accessible selected text without recording it.
Input origin remains separate from synthesis so a future OCR provider can submit
text through the same boundary. OCR is not implemented.

The Qt main thread only handles widgets and Windows clipboard access. Generation,
accessibility helper and model installation run on background threads. Signals
return results; a capture generation number invalidates stale selection results.
A selected-text request does not open or focus the reader before capture. Audio
plays to native device completion or explicit cancellation, not an estimated timer.

engines/kokoro_engine.py uses the approved Misaki frontend and untrimmed 24 kHz
Kokoro FP32 output. kokoro_host.py freezes its dependencies independently from
python-engine-v1, preserving the original Piper/Chatterbox environment. Client
switches worker processes when the dependency profile changes.

reader-settings.json stores reader controls, not input. Temporary native WAVs live
in an owned Windows temporary directory, removed on normal exit; Save audio makes
an explicit permanent copy. Original settings.json, presets and outputs are retained.
The full installer bundles only Talesyntese/Kokoro models, verifies hashes, skips
matching caches, and refuses to overwrite differing models or immutable runtimes.
It registers both models before switching shortcuts. Other model downloads are explicit.

See README and docs/SOURCES.md for public build inputs and dependency licenses.
The historical notes below describe the original comparison application.

---

# Architecture and continuity

## Source lineage

The Tkinter read/compare workflow comes from the original Norwegian TTS Model
Shootout v5 and its September extension (`workavoidance/Skrivi`, `tts-handoff`,
commits 637d239 and 6d83b34). Its source snapshot is retained in
`docs/shootout-v5-extension.py`; it is historical, not a launcher.

`native/Engine.cs`, `OwnedJob.cs`, `VoiceSettings.cs` and `Contracts.cs` are adapted
from the delivered VoxCPM2 Reader 0.2 source at Skrivi commit f54532b. Changes add
explicit voices/runtime locations, CPU thread configuration and a persistent
JSON-line host. Its authentication, native WAV validation and Windows job ownership
are retained. It does not launch the Reader tray shell or register hotkeys.

`engines/chatterbox.py` comes from the verified ONNX benchmark, itself following
ONNX export example revision b8b5f7f75436de240639e777dce2b7e26a305681. It retains
tokenization, Q4 graph selection, native output, natural stop checks and defaults.
The new settings control actual inference parameters. No PyTorch is used.

## Boundaries

- `app/core.py`: schema 1 library registry, atomic JSON persistence, checksum-verified
  downloads/imports, settings validation. A future schema fails without resetting data.
- `app/main.py`: desktop workflow, model management, presets, history, ratings and
  full-WAV Windows playback. Worker threads communicate with Tk through a queue.
- `app/client.py`: owns one persistent worker, waits without blocking Tk, cancels
  only its worker process tree. Normal app close waits for cancellation cleanup.
- `engines/worker.py`: adapters and persistent model session; JSON lines on stdin/stdout.
  Text exists in memory/IPC only. Upstream diagnostic output is discarded.
- `native/Host.cs`: keeps the reused Vox engine alive between requests. CPU only.
- `worker_host.py`: frozen Python/dependency host loading engine code shipped with
  the app. Engine code changes do not require replacing downloaded model files.
- `models.json`: built-in registry of exact model revisions, URLs, bytes and SHA-256.

To add a model using an existing adapter, add a pinned catalog entry and appropriate
settings/validation. For a new architecture, add an isolated adapter and dependency
profile, declare effective device and native rate, then verify full-WAV quality and
performance. Do not guess compatibility from the model file extension.

## Durable storage

```
%LOCALAPPDATA%/SkriviTTS/
  library.json             model locations + exact revisions
  settings.json            per-model settings, no input text
  models/<model-id>/       verified, persistent weights and companions
  voices/                  imported reference WAVs
  presets/                 named settings
  outputs/                 native WAV + settings/timing/rating JSON
  runtimes/python-engine-v1/  frozen dependency host
  runtimes/vox-0.8.32/      pinned CrispASR + notices
  versions/<app-version>/   versioned application files
```

`SKRIVI_TTS_DATA` can override the library in source tests. The Windows installer
always targets the normal LocalAppData location. It verifies the complete package
before copying application/runtime files, never touches models/settings/audio, and
updates shortcuts last. Older app versions remain available for rollback. Runtime
profile names are versioned: dependency changes require a new profile, not deletion
of the existing runtime. Automatic online updating and uninstall UI are not included.

## Measurement

Results include cold/warm state, exact settings/model revision, app version, CPU
device, load, generation, audio duration, generation/audio ratio, total wait and RAM
where available. Total wait ends at complete WAV readiness, before playback; physical
speaker onset is not measured. Warm load is near zero. Changing settings deliberately
reloads the model for a clear comparison boundary. RAM is a process high-water mark,
not an independently sampled per-model peak; Vox additionally reports its child peak.

Quality belongs to the listener. Ratings are user-entered and not inferred from
waveform checks. Chatterbox's seed only controls supported runtime randomness;
greedy token selection is retained. Native voice defaults remain the baseline.
