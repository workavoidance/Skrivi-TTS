# Skrivi TTS — working application, 8 September 2026

## Durable home

- GitHub: https://github.com/workavoidance/Skrivi-TTS (private, separate from Skrivi).
- Local source: `C:/Users/jon/.codex/visualizations/2026/09/08/01a07fdc-16e7-7330-83a6-cbdec9f59c1d/skrivi-tts`.
- Current version: **0.1.0**, Windows x64. Source, build recipes, tests and release
  artifact are maintained in this repository. Start future work here, not by
  rebuilding an earlier shootout from conversation memory.
- Installed executable: `%LOCALAPPDATA%/SkriviTTS/versions/0.1.0/SkriviTTS.exe`.
  Start menu and desktop shortcuts: **Skrivi TTS**.
- Permanent library: `%LOCALAPPDATA%/SkriviTTS`; models in `models`, voices in
  `voices`, presets in `presets`, generated WAV/JSON in `outputs`.

## Implemented

The user requested a maintained application rather than more disposable POCs.
The existing v5 shootout workflow and tested inference code were reused and split
into UI, persistent library, model catalog and persistent engine process. The old
Skrivi checkout, handoff checkout, Reader installations and model caches remain intact.

Four real CPU models: public VoxCPM2 Q4_K, Chatterbox multilingual Q4 ONNX, Piper
NVCC and Piper Talesyntese. Actual inference controls are exposed per engine,
including reference voices where supported. Defaults preserve prior quality settings.
Named presets, per-model settings, past-run settings restoration, saved WAVs and
timing records, user quality ratings and cold/warm indicators are implemented.

Model downloads are explicit, pinned and checksum-verified. Existing models were
copied locally once into the permanent library, without any network model download.
The original copies remain unchanged. App reinstall copies app/runtime files only;
models, settings, presets, reference voices and audio are outside the version folder.
No dependency on Codex's Python or the old tester folders exists in the installed app.

Vox uses the reused C# engine with authenticated loopback and owned native process.
Chatterbox/Piper use the frozen dependency worker. The worker stays loaded between
requests with identical settings; model or settings changes reload it. Stop cancels
the owned process tree. Full WAVs play synchronously with no post-processing or
premature purge. Input text is not persisted; settings/results are.

## Hardware and verified evidence

Ryzen 7 7700, 8 cores / 16 logical CPUs, roughly 32 GB physical RAM. RTX 4060 with
8,188 MiB VRAM, driver 591.86 is present, but all current adapters explicitly use CPU.

`tests/check_engines.py` ran against the **installed frozen worker runtime**, using
the same short Norwegian sentence twice per model. Native WAV headers/durations,
cold/warm state and cancellation passed. Results in
`%LOCALAPPDATA%/SkriviTTS/verification/engine-results.json`:

| Model | Cold load s | Cold generate s | Warm generate s | Warm audio s |
| --- | ---: | ---: | ---: | ---: |
| VoxCPM2 Q4 | 1.681 | 7.160 | 6.414 | 3.400 |
| Chatterbox Q4 ONNX | 41.326 | 6.487 | 6.424 | 3.000 |
| Piper NVCC | 0.567 | 0.338 | 0.083 | 3.111 |
| Piper Talesyntese | 0.721 | 0.064 | 0.080 | 3.007 |

Warm loading was effectively zero for all four. Piper native stochastic generation
can produce different durations; no fixed-seed claim is made. This is a small smoke
comparison, not a statistically robust benchmark or user quality verdict. Playback
quality was validated in earlier full-WAV tests; this engine test validates synthesis
and metadata without automatically playing every sample.

Five unit checks pass: reinstall-style library reuse without any network call,
wrong-file rejection, cancellation before registration, preservation of a future
library schema, and settings/reference validation. A real Windows PowerShell
reinstall preserved all 19 existing model/registry files and their timestamps.
The installer was corrected to use .NET SHA-256 directly so it works without relying
on Get-FileHash availability. The installed desktop window is responsive. Controls
fit the 1100x850 window, including Chatterbox's larger settings panel.

Build output: application approximately 32.7 MB unpacked; reusable Python engine
runtime 162.5 MB; native Vox runtime 19.3 MB. Complete initial installer ZIP about
104 MB, excluding model weights (~3.39 GB combined). Exact ZIP checksum accompanies
the release. Models are never Git or release assets.

## Build / update workflow

See README for the exact commands. `requirements-build.lock` records the complete
Python 3.12 build environment. `scripts/build.ps1` compiles native code with the
Windows .NET Framework compiler and creates the two frozen executables.
`scripts/package.py` assembles an installer and checksum manifest from those builds
and an existing pinned CrispASR runtime. `runtime-manifest.json` records its upstream
archive URL/hash; download it only if missing, verify SHA-256, then extract its four
runtime files. `INSTALL.bat` invokes the included PowerShell installer.

For application-only updates, reuse the existing engine runtime build. If dependency
contents change, introduce a new runtime profile ID and preserve the old profile
for installed app versions. Do not change models.json revision/hash without an
explicit model update experiment. Do not delete existing models to fix setup.

GitHub Actions runs the fast library tests. Actual model/device/audio checks remain
local opt-in tests because CI does not contain multi-GB weights or this hardware.

## Known limits and next work

- CPU only; GPU is the next separate measured performance experiment, not a toggle
  with unverified behavior. Warm reuse eliminates repeated loads, not inference cost.
- Four built-in models, with a registry/adapter structure for adding more. Arbitrary
  unsupported model formats are not loadable simply by browsing to a file.
- Vox retains the existing 4,096-character adapter limit. Sentence-aware long text
  handling remains work to do without losing native cadence or word endings.
- Chatterbox has greedy decoding and a configurable token safety limit; it fails
  rather than saving truncated speech when no natural stop is reached.
- Reference controls are wired to the existing implementations; broad voice-reference
  quality comparisons and non-default parameter benchmarks are next experiments.
- No background automatic updater, weight training, tray reader/global hotkey or
  selected-text capture is included in this application version. Inference tuning
  and model comparison are the current scope.
- CPU/RAM metrics describe the actual adapter/runtime, but physical audio onset
  and GPU VRAM utilization are not measured. User listening ratings select quality.

Next: use the maintained app to save comparable presets and listening judgments,
then implement and verify a GPU adapter on the RTX 4060. Preserve this CPU/full-WAV
baseline. Do not return to MOSS dependency debugging, broad model surveys or Piper
polish without a concrete new reason. Prior experiments and rationale are retained
in `docs/PREVIOUS_PROJECT_STATUS.md` and `docs/ARCHITECTURE.md`.
