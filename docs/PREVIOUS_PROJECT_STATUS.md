# TTS project status — 8 September 2026

## Current decision and working location

The September 8 handoff update (`f54532b`) supersedes the old inaccessible-NbAiLab
requirement. **Public OpenBMB VoxCPM2 is approved.** The task is to extend the
existing multi-model shootout, preserve the full-WAV quality path, then assess
performance and additional compatible engines. The user chooses the listening winner.

The initial five handoff documents were read at `52413a9`. A final branch check
found the newer Reader source/continuation commit, which was fast-forwarded and
read before this continuation was completed. The early private-checkpoint access
check is historical evidence only; it no longer blocks this project.

Current worktree: `C:/Users/jon/.codex/visualizations/2026/09/08/01a07fdc-16e7-7330-83a6-cbdec9f59c1d/reader-lab/handoff-repo`,
branch `tts-handoff`, remote `https://github.com/workavoidance/Skrivi.git`.

The shared `Skrivi Local` checkout switched to `feature/spell-checker-benchmark`
during concurrent work. Its source, branch, untracked AGENTS.md and edits were
preserved. No TTS branch was merged into main. No Skrivi runtime, website,
installer, settings, model storage or speech processes were changed.

## Reused source inventory

| Source | Existing location / state | Reuse |
| --- | --- | --- |
| Multi-model Shootout v5 | `C:/Users/jon/Downloads/Norwegian_TTS_Model_Shootout_v5/Norwegian_TTS_Model_Shootout_v5` | Original UI and all three backend files copied source-only and extended here; original remains unchanged |
| Earlier shootouts v3/v4 | Corresponding `Norwegian_TTS_Model_Shootout_*` Downloads directories | Located; v5 selected as the newest existing multi-model tester |
| Quality Tester v4 | `C:/Users/jon/Downloads/Norwegian_TTS_Quality_Tester_v4_No_UV_Installs/Norwegian_TTS_Quality_Tester_v4_No_UV_Installs` | Inspected; old ONNX runner selects FP32 files, no Chatterbox ONNX environment existed |
| Piper Reader 0.4 | `C:/Users/jon/Downloads/Reader_POC_Alpha_0_4_Native_Voice_Speed/Reader_POC_Alpha_0_4_Native_Voice_Speed` | Native speed and synchronous playback source inspected as reference |
| VoxCPM2 Reader 0.2 | `C:/Users/jon/Downloads/VoxCPM2_Reader_POC_0.2.0_Windows/VoxCPM2_Reader_POC_0.2.0` | Delivered assemblies and CPU runtime reused by a headless host; source preserved in the handoff |
| New extension source | [shootout-source](docs/tts-handoff/voxcpm2-reader/shootout-source/LOCAL_EXTENSION.md) | Retained v5 interface with explicit VoxCPM2 Q4 CPU and Chatterbox Q4 ONNX CPU choices |

The original v5 `shootout.py` SHA-256 was
`951e245940e7da7bdc4f2342cf1b8be64ce80dd92df386e6532319561f753163` before extension.
The original file was not overwritten. Existing historical source notes are kept
alongside the extension notes to distinguish old installer behavior from new setup.

## Persistent data and dependencies

- Shootout v5 Piper environment: `<existing v5>/envs/piper`; `.ready` marker and
  Python are present. Cached NVCC voice: `<existing v5>/models/piper/no_NO-nvcc-medium.onnx`,
  76,770,227 bytes, with its native JSON configuration. Talesyntese is also cached.
- Existing v5 Chatterbox PyTorch environment: `envs/chatterbox_v3src_nogit`, preserved;
  no PyTorch Chatterbox work or MOSS environment debugging was resumed.
- Vox model: `%LOCALAPPDATA%/VoxCPM2ReaderPOC/models/voxcpm2-q4_k.gguf`,
  1,689,498,432 bytes, SHA-256
  `502efe74f6a59c370b3abf5a3fcfd7c3955ca6c167b411c8aee3977e9e46c079`.
  Reused and reverified; no new Vox model download.
- Existing Vox voices and settings remain under `%LOCALAPPDATA%/VoxCPM2ReaderPOC`.
  These comparison runs use the default voice and do not change saved settings.
- Independent lab: parent directory of this worktree, `reader-lab`.
  ONNX models are in `models/chatterbox-q4`; dedicated Python environment in `.venv`;
  copied Reader assemblies/runtime and new host in `vox-engine`; WAVs in `results`;
  interactive tester outputs in `shootout-outputs`.
- The ignored `shootout-source/local-paths.json` already points to these locations.
  A portable example and dependency lock are committed. No weights, WAVs, venvs or
  binaries are committed. ONNX setup uses no PyTorch, Transformers or librosa.

## Actual machine and measurements

Ryzen 7 7700 (8 cores, 16 logical CPUs), 33,452,666,880 bytes physical RAM.
RTX 4060, 8,188 MiB VRAM, NVIDIA driver 591.86. **All measured inference here is CPU.**
The new choices explicitly say CPU; no unsupported GPU toggle is advertised.
Vox uses the existing adapter's `--no-gpu`; ONNX sessions report CPUExecutionProvider.

The baseline was established with the original v5 Piper backend/environment before
editing the tester. Its short Oslo/KON sample succeeded with native SynthesisConfig,
no length_scale override, in 3.695 s including interpreter startup and model load.
That total-process number is not comparable to warm generation-only timings below.

| Model | Session load | Warm short: generate / audio | Paragraph: generate / audio | Peak RAM |
| --- | ---: | ---: | ---: | ---: |
| Public VoxCPM2 Q4_K, Reader 0.2 engine | 0.580 s | 6.486 / 3.40 s | 42.260 / 19.96 s | 2.803 GB runtime |
| Chatterbox Multilingual Q4 ONNX | 42.501 s | 6.698 / 3.00 s | 40.648 / 20.88 s | 2.841 GB process |

Vox paragraph was a separate freshly loaded session (load 0.542 s); its first
short inference took 7.218 s. ONNX first short inference took 7.511 s, and its
conditional decoder accounted for 40.532 s of loading and 29.293 s of paragraph
generation. Vox short warm RTF was 1.908; ONNX short warm RTF 2.233. Paragraph RTFs
were 2.117 and 1.947 respectively. Both CPU paths are slower than real time.
These are small controlled observations, not statistically robust percentiles.

Both used identical fixed Norwegian short/paragraph inputs. Vox retained seed 42,
10 steps, guidance 2.0 and native 48 kHz output. Chatterbox retained the exporter
example's default voice, greedy decoding, repetition penalty 1.2, exaggeration 0.5
and native 24 kHz output. Default voices are compared separately; no shared-reference
or female-voice similarity claim is made. Output duration differences matter when
comparing raw generation times.

Vox model+existing app/runtime is about 1.71 GB per its build inventory, excluding
this experiment's extra source copies. Chatterbox assets are exactly 1,555,838,641
bytes; dependency wheels 38,639,024 bytes; dedicated venv 212,441,998 bytes.
Model+venv is 1,768,280,639 bytes, excluding the pre-existing Python interpreter and
stdlib. Chatterbox's companions are FP32; the earlier 800–850 MB estimate does not
apply to this package. Sizes are file/payload bytes, not network overhead or disk
allocation. Peak VRAM was not measured because these paths explicitly use CPU.

All comparison WAVs were complete and played synchronously through Windows. ONNX
samples reached the natural stop token. Frame counts, native rates and hashes were
checked; no custom streaming, output resampling, silence trimming or speed changes
were applied. Physical speaker onset remains unmeasured; sidecars report the
application playback-call timing where available. User listening verdict is pending.

## Changes and verification

- Added two explicit CPU engine choices to the existing v5 UI. All previous model
  choices and Piper speakers remain. Resources point to persistent existing caches.
- `VoxRunner.cs` hosts the delivered `Reader.Windows.VoxEngine` via reflection;
  it does not rewrite the engine, launch the tray shell or register a hotkey.
  Model SHA-256 is checked before use. Native output is validated with Reader.Core.
- Chatterbox uses the measured local ONNX path with pinned Q4 files. New adapters
  save numeric timing sidecars without storing the UI's input text. Only the fixed
  public benchmark vectors are retained in committed evidence.
- Tester playback is synchronous. Stop kills only its owned synthesis process tree;
  normal close waits for cleanup. Incomplete existing environments are preserved
  instead of being deleted by the historical setup routine.
- Three focused tests passed: retained UI/model/speaker selection, isolated routing
  without setup, and cancellation of an owned descendant process. Both new backend
  command routes were exercised against real models and produced valid native WAVs.
- Dedicated dependency integrity check passed; final WAV metadata and completion
  records passed. C# test host compiled with the installed .NET Framework compiler.
  No Reader shell rebuild or comprehensive Windows accessibility/UI review was done.

The original Reader's async playback behavior is preserved in its source snapshot;
the separate test host uses SoundPlayer.PlaySync for quality evaluation. An initial
ONNX harness playback-constant error was fixed and the full run repeated successfully.

## Run and continue

Launch the extended tester:
[RUN_LOCAL.ps1](docs/tts-handoff/voxcpm2-reader/shootout-source/RUN_LOCAL.ps1).
Its configured environment is already installed. The source-only old RUN_SHOOTOUT.bat
is historical; use RUN_LOCAL.ps1 for this extension.

Rebuild only the small existing-engine host with
[BUILD_RUNNER.ps1](docs/tts-handoff/voxcpm2-reader/shootout-source/BUILD_RUNNER.ps1).
It uses the installed Framework compiler and copied delivered assemblies/runtime,
downloads no model and does not alter the original Reader installation.

Evidence: [local-results/2026-09-08](docs/tts-handoff/voxcpm2-reader/local-results/2026-09-08/chatterbox-q4.json).
Full listening files are in the lab's `results/cpu-q4-verified` and `results/voxcpm-q4`.
New UI backend-route verification WAVs are named `shootout-route.wav`.

Next: get the user's listening judgment on public Vox Q4 vs Chatterbox Q4. Then
verify a compatible GPU runtime on this RTX 4060 and compare it with the preserved
CPU/full-WAV baseline; investigate ONNX decoder load/inference separately if its
quality passes. Higher-precision VoxCPM2 and OmniVoice remain candidates, not tested
adapters. Keep OmniVoice's upstream restrictions visible if pursued. Do not restart
the fine-tune access search, broad model survey, Piper polishing or MOSS setup.

Substantive source and evidence are committed locally on `tts-handoff`; nothing is
pushed, merged into main or published as part of this continuation.

## Ready-to-run listening shootout, September 8 follow-up

User requested a new local shootout to measure and listen personally. The existing
v5 extension now has separate load/generation/audio/total-wait columns, a live wait
counter, persistent result rows, and replay of any selected saved result. Piper NVCC
defaults to KON (index 3). Native synthesis settings and full-WAV playback are retained.
The two cached Piper voices now write timing sidecars too.

Delivered and opened:
`C:\Users\jon\Downloads\Norwegian_TTS_Shootout_September_2026\START_SHOOTOUT.bat`.
Instructions are `TRY_IT.md` beside it; audio and timing records are in `outputs`.
This machine-specific source package references the existing environments/runtime
and caches above. It does not bundle or redownload weights. Its ignored local config
sets `ready_only: true` and `outputs` to the package's own outputs directory. The
four selectable CPU engines are VoxCPM2 Q4, Chatterbox Q4 ONNX, Piper NVCC and Piper
Talesyntese. Each click creates a fresh engine, not a warm persistent session.
Total wait ends at completed audio/metadata read and excludes playback; it is not
a measured physical audio-onset value.

Package source is `docs/tts-handoff/voxcpm2-reader/shootout-source`: copy
`shootout.py`, `new_backends.py`, `onnx_benchmark.py`, `START_SHOOTOUT.bat`,
`LAUNCH.ps1`, `TRY_IT.md`, `backends/piper_backend.py`, and configured
`local-paths.json` into a new folder, creating `outputs`. The historical bootstrap
launcher is deliberately excluded from the delivery. Launch helper uses configured
pythonw and captures startup errors in a uniquely named local log.

Validation: all three `test_extension.py` checks passed, including cancellation of
only the owned child process tree. `check_local_ui.py` additionally generated one
short Norwegian sentence through the actual Tk worker and all four real engines,
checked WAV durations/sample rates against displayed metadata, restored all four
saved rows, and exercised replay selection. Playback was stubbed in this automated
UI check; real full-WAV playback was exercised in the earlier benchmarks. Results:

| Engine | Load s | Generate s | Audio s |
| --- | ---: | ---: | ---: |
| Piper NVCC KON | 0.853 | 0.123 | 3.111 |
| Piper Talesyntese | 1.188 | 0.107 | 2.299 |
| VoxCPM2 Q4 | 0.559 | 7.168 | 3.400 |
| Chatterbox Q4 ONNX | 40.004 | 6.615 | 3.000 |

Delivered launcher was executed and its window process remained running with an
empty startup error log. User listening judgments remain the next input; no GPU
claims or Skrivi integration were added.

## Handoff resumption verification — September 8

Fetched `origin/tts-handoff` again following the renewed continuation request.
Remote remains at `f54532b`; local implementation commits `637d239` and `6d83b34`
were preserved. No incoming changes required a merge or checkout switch. The
active `feature/spell-checker-benchmark` checkout has untracked `AGENTS.md`, which
was inspected and preserved. The isolated TTS checkout was clean before this update.
Re-read the entry prompt and linked earlier handoff documents; the later public
VoxCPM2 approval remains authoritative. Original v5 source SHA-256 still matches
the inventory above, and the existing Vox model file retains its recorded size.

Three new interactive results are present in the delivered shootout's outputs:

| Saved run | Load s | Generate s | Audio s | Total wait s |
| --- | ---: | ---: | ---: | ---: |
| 10:34 VoxCPM2 Q4 | 0.546 | 48.179 | 24.440 | 50.408 |
| 10:37 Piper NVCC KON | 0.843 | 0.530 | 19.807 | 2.068 |
| 10:37 Piper Talesyntese | 1.162 | 0.502 | 19.215 | 2.362 |

These are existing user-session measurements, not newly rerun controlled tests.
Input text was not logged, so identical input across these runs cannot be verified.
WAVs and sidecars remain in place. Vox's sidecar playback flag describes its headless
generation host (`no-play`); it does not establish whether the shootout UI completed
playback. No listening-quality conclusion is inferred from file presence.

Next remains the user's quality comparison, especially Chatterbox Q4 against Vox;
the delivered folder has no saved Chatterbox user-session result yet. Prior controlled
Chatterbox benchmarks remain available in the lab. GPU acceleration is a subsequent
separate experiment, preserving these CPU/native-audio baselines. No new models,
runtime changes or repeat broad research were needed for this resumption.
