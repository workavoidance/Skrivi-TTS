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

### Latest listening feedback — September 8

The user reports **Piper Talesyntese is "very very good, and fast"** in the maintained
application. This supersedes treating all Piper voices as below the quality target.
Earlier negative Piper/NVCC impressions must not be generalized to Talesyntese.
Treat Talesyntese as a serious lightweight candidate and preserve its current native
settings for further listening comparisons. No final winner or universal quality
conclusion has been declared by the user.

Latest saved Talesyntese run (`20260908-164452-piper-talesyntese-0fa929`) generated
12.167 seconds of audio in 0.318 seconds, total wait 0.324 seconds, warm CPU session,
native 22,050 Hz, speed 1.0, native noise defaults, playback completed. This is about
38 times faster than playback. Another recent short run generated 2.183 seconds in
0.070 seconds. Model weights are 63,201,294 bytes. These measurements substantiate
speed; the positive quality judgment comes from the user. Do not change application
defaults or inference settings solely as a side effect of recording this feedback.

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

The user requested a focused search for other Norwegian Piper trainings. Findings
are in `docs/NORWEGIAN_PIPER_SEARCH.md`: NbAiLab's distinct NST fine-tune is documented
but currently returns 401 for anonymous model access; its demo Space reports running
(synthesis untested). A community female-voice training effort has no verified public
checkpoint. Other inspected repositories mostly mirror or convert Talesyntese.
No new model was installed and no additional female single-speaker download was verified.

### NVCC shortening investigation — September 8

User reports shortened/clipped sounds **throughout sentences**, not just the final
word. This is now investigated rather than assumed to be a generic voice preference.
Recent settings were native speed 1.0 and native noise defaults, including MON ID 6.

`tests/audit_piper_path.py` ran inside the installed frozen dependency host against
the installed production adapter. It checked NVCC speakers 3 and 6, plus Talesyntese,
using a fixed four-sentence Norwegian passage (no user input text). Model/config
hashes match the catalog. Captured ONNX inputs show NVCC's actual native scales
`[0.667, 1.3, 0.5]` and correct speaker IDs. The old erroneous length_scale=1.0
override is absent. No unmapped phonemes were found for the test passage.

The test replayed identical raw ONNX results through the original direct
`PiperVoice.synthesize_wav(..., SynthesisConfig(speaker_id=...))` API. All three WAVs
were byte-identical to the application adapter. Every model-generated frame was
written at native 22,050 Hz. This isolates wrapper/frame handling from stochastic
generation; it is not a claim that two independent neural inference runs match.
NVCC's sentence tails decayed close to silence; amplitude saturation was under
0.002% of samples and does not explain lost syllable duration. These checks do not
establish perceptual correctness or rule out an upstream model/runtime issue.

Evidence: `%LOCALAPPDATA%/SkriviTTS/verification/nvcc-audit/report.json` and paired
`*-app.wav` / `*-direct.wav`; numerical report copied into docs/NVCC_AUDIT.json.
Installed UI code also matches repository source and uses synchronous Windows
playback with purge only on explicit Stop/close. Some recent user run records show
interrupted playback, but another completed and the user describes intra-sentence
shortening, so final-word cancellation is not an adequate explanation.

Focused upstream investigation found a closely matching known-quality report:
https://huggingface.co/rhasspy/piper-voices/discussions/88 . The model author reported
an earlier garbled training result and dissatisfaction with its retrained version;
a Norwegian listener reported mumbling/jumping and poorer quality than the earlier
voice. This is evidence about NVCC, not proof of a particular phoneme-duration bug.
The published model card says NVCC was trained from scratch; Talesyntese's card
records fine-tuning from Lessac. Neither fact alone establishes causation.

No app settings, models or runtime defaults were changed to conceal this symptom.
Talesyntese remains the positively evaluated baseline. NVCC quality work should
next compare an upstream sample/runtime on identical input if pursued, rather than
adding arbitrary playback padding or time-stretching. An exact user-provided failing
sentence would permit a targeted pronunciation/duration investigation.

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


## Nynorsk accuracy screen — 19 September 2026

Completed a two-passage local screen of Talesyntese, VoxCPM2 Q4 and Chatterbox Q4,
using installed weights and unchanged native settings. Five WAVs were produced;
Chatterbox failed to reach a natural stop on the word-focused passage. Offline
Whisper medium (existing cache) recovered all Talesyntese numeric values, but
flagged suspect phrases in both Talesyntese and Vox; Chatterbox's numbers transcript
was badly mismatched. These are ASR disagreements, not certified TTS pronunciation
errors. Whisper normalizes some Nynorsk to Bokmal, so no accuracy percentage or
Nynorsk-support certification is claimed. Human listening remains necessary.

Details, exact synthetic texts, settings, model revisions and evidence:
`docs/NYNORSK_SCREENING.md`, `docs/NYNORSK_SCREENING.json`.
Local listening page and native WAVs: `build/nynorsk-2026-09-19/listen.html`.
Repeatable opt-in runners: `tests/nynorsk_accuracy.py`, `tests/nynorsk_transcribe.py`,
`tests/nynorsk_report.py`. ASR dependencies are isolated under build, with a saved
version list. No application code, user presets, model assets or installed runtime
was changed. Next: listen to Talesyntese's suspected phrases before calling it
accurate Nynorsk; retain the existing positive Bokmal quality verdict separately.


## English comparison — 19 September 2026

Tested Kokoro v1.0 FP32 ONNX (Heart US female, Michael US male, Emma UK female),
Piper LJSpeech, and existing VoxCPM2/Chatterbox on identical English story and
numeric/email passages. Eleven WAVs produced from twelve attempts. All six voice
configurations matched the story in offline Whisper transcripts. Kokoro also
preserved intended numeric/email details, taking 1.6–2.9 s for 10–18 s of audio.
Piper and Vox had suspected money-amount errors in ASR. Chatterbox failed to stop
on the detail passage. See docs/ENGLISH_SCREENING.md and ENGLISH_SCREENING.json.

Recommendation: Kokoro is the strongest next English integration candidate based
on this limited word-recovery/speed test; subjective voice quality remains for
user listening. Local comparison: build/english-2026-09-19/listen.html.
New weights cached once under the permanent library's models/kokoro-v1.0-onnx and
models/piper-ljspeech-high; checksum manifest in docs/ENGLISH_MODEL_MANIFEST.json.
They are NOT yet app dropdown entries. Existing app, presets and runtime unchanged.
Kokoro test dependencies are isolated in build/english-env; installed package lock
and a required speed-input dtype correction are documented. Repeatable test/cache
scripts are checked in. Next: user chooses an English voice, then integrate Kokoro
and package an app update without downloading weights again.
