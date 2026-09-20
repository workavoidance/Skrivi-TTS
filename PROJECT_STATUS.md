# Skrivi Lytt - reader release work

## Naming update — 20 September 2026

Public name: Skrivi Lytt in both languages; dictation companion: Skrivi Snakk.
Current UI, installer and Store display labels are being aligned. Published
0.2.1/0.3.0 artifacts still say Skrivi TTS; do not overwrite old binaries.
Preserve SkriviTTS paths, executable, startup/single-instance identifiers, AppId
and all user assets. No model downloads, voice changes or version bump are part
of this rename. Existing release work and historical records follow unchanged.

## Reader 0.4 work — 20 September 2026

User authorised polished progress pill, active global Escape, true loading vs
synthesis phases, light/dark support, two-model reader, signing and Store packaging.
Implemented source changes; release pipeline validation in progress. Details:
docs/RELEASE_0_4.md. Certum secrets exist in Skrivi-STT only; reusable signing workflow
is in this repo. Do not expose secret values or re-sign immutable installed profiles.
User supplied the reserved Lytt Store identity on 20 September 2026. It is recorded
in store/identity.json: Skrivi.SkriviLytt, publisher
CN=EF3D997F-87B2-4AD0-B65B-877EE1632E65, publisher display name Skrivi.
The next signed workflow must build from the commit containing this association.
Uploadable package validation and Store certification remain pending;
validation-only MSIX must never be described as ready for upload.
Source version 0.4.0; installed version remains 0.3.0 until signed release verification.

Local build dd4721c: frozen GUI starts; both engines pass cold/warm generation with
actual progress events, global Escape registers, frozen OCR layouts 3/6 work and
DPI/stale-result tests pass. docs/READER_0_4_LOCAL_CHECKS.json records evidence.
Restricted local builds injected unrelated Poppler/libheif DLLs despite PATH
cleanup and reproduced QtCore failure. Rebuilding with normal Windows access
restored correct DLL inputs and passed. Do not publish a restricted build that
contains unrelated icuuc.dll/ucrtbase.dll. The CI build uses a clean hosted runner.
STT signing bridge PR 64 merged through normal protections; signed build run
35513969249 checks out dd4721c. No release/installation claimed until it passes.
Store startup extension uses --tray (uap10:Parameters), supported on packaged
desktop apps; identity-associated build is pending CI verification.


### Signing validation progress

STT bridge PR 65 is merged. It pins workflow recipe 26e38f8 and accepts a TTS
source_ref for manual builds. Current run 35514688453 builds source e02a0b2.
First run 35513969249 verified 369 payload signatures and signed engine generation,
then passed first install/startup but refused reinstall (exit 7). It is NOT a
release candidate. The next run includes precise preflight diagnostics, signed
uninstaller verification and a reusable signed-runtime archive. Resolve reinstall
before publishing/installing any candidate.

First artifact downloaded via bounded range requests after gh download timed out;
ignored build/download-artifact-ranges.py uses existing GitHub CLI authentication
only for the GitHub API, never forwards that token to artifact storage, verifies
the artifact digest and extracts validated paths. First test EXE has a valid
Certum developer signature; all model hashes match unchanged local models.
Local MakeAppx structure validation passed (unsigned, UNASSOCIATED; not installable
or certified). SDK/provenance details in docs/RELEASE_0_4.md. --makeappx supports an
explicit SDK binary path without requiring a system-wide SDK installation.

## OCR update 0.3.0 (supersedes OCR future-work notes below)

User authorised testing Tesseract and integrating if suitable. Source and frozen
worker tests passed: 22/24 development crops exact with nor+eng, 12/12 separate
held-out crops exact. Details and limits: docs/OCR_SCREENING.md and JSON evidence.
Region overlay, separate Ctrl+Alt+Shift+Space, immediate reading, cancellation and
editable recognition text implemented. One monitor per selection, one paragraph/
column recommended. No private screen capture or real HDR/multi-monitor test.
Source: app/screen_region.py, ocr_host.py, scripts/build-ocr.ps1 and
scripts/package-ocr-update.py. Dependencies pinned in requirements-ocr.lock;
weights pinned in docs/OCR_MODEL_MANIFEST.json. Persistent model/runtime IDs:
ocr-tessdata-fast-v1, tesseract-5.5.2-v1. Speech assets are unchanged.
Installed 0.3.0 alongside 0.2.1; installed GUI startup and OCR passed. All 25
pre-existing model/settings/user-data files retained identical contents. Evidence:
docs/OCR_INSTALL_CHECKS.json. Old 0.2.1 session was left running; user should Quit
from tray and reopen to activate 0.3.0. Do not terminate their session blindly.
OCR update package: build/Skrivi-TTS-0.3.0-OCR-update.zip, 63,969,657 bytes,
SHA-256 4efdc9256bb025e2c7664c7be304e680b44ef20573b4a38108775887e26f93ad.
Built application source commit 9d67200. No speech weights are included/redownloaded.
Keep the 0.2.1 fallback. Prior Smart App Control issue is not resolved by OCR.

## Two-column experiment

User confirmed the installed OCR works on another machine. Tested existing Tesseract
modes on 30 synthetic column layouts plus 24 single-column controls, with no app or
model changes. docs/OCR_COLUMNS.md / OCR_COLUMNS.json; tests/ocr_columns.py.
PSM 3 automatic page: 18/18 simple/narrow/staggered columns exact, 3/6 spanning
headings exact, footer placed too early in 6/6. Total 21/30 exact, 27/30 correct body
anchor order. Current PSM 6 interleaved all 30. Single-column accuracy unchanged
(22/24 exact), similar recognition speed. Next easy feature: optional Automatic
page layout; retain current single-block fallback. Do not silently claim robust
whole-page order. No release built or installed for this experiment.

## Previous release authority

- Repository: https://github.com/workavoidance/Skrivi-TTS, separate from Skrivi STT.
  User explicitly requested a public open-source GitHub project; it is now PUBLIC.
  Initial reader source commit 727eced; GitHub Actions passed. Source, tests, build recipes and releases
  belong here, not solely in a local machine folder.
- App version: **0.2.1**, installed, verified and publicly released.
  Download: https://github.com/workavoidance/Skrivi-TTS/releases/tag/v0.2.1.
- Source: `C:/Users/jon/.codex/visualizations/2026/09/08/01a07fdc-16e7-7330-83a6-cbdec9f59c1d/skrivi-tts`.
  No build requires that exact path. README provides fresh-clone instructions.
- Existing installed 0.1.0 and cached models remain available until installation
  verification completes. Persistent data: `%LOCALAPPDATA%/SkriviTTS`.
- User approved **Kokoro Heart (American female)**: "That English one is perfect.
  Let's use that." This supersedes the pending-listening recommendation below.
- Default bundled voices: Talesyntese Bokmaal male and Kokoro Heart, 417 MB weights.
  Kokoro FP32, Misaki 0.9.4, American G2P, speed 1.0, 8 CPU threads, trim=False,
  float32 speed-input correction. No resampling, compression or silence trimming.
- UI is now a PySide6 reader with Skrivi styling (upstream main 05ed960), separate
  orange speaker tray icon, text box, model library and settings. Historical Tk
  comparison UI retained in app/shootout.py; all old user data is preserved.
- Selection shortcut Ctrl+Alt+Space starts immediately; press again to stop.
  Windows accessibility capture falls back to copying/restoring clipboard formats.
  Automatic chooses one English/Bokmaal model for the entire passage; manual tray/UI
  override and uncertain-text fallback. No per-word voice switching.
- OCR/image input is future work; do not add it to this release.
- Dependency profiles: existing python-engine-v1 reused byte-for-byte; new
  kokoro-engine-v1 is separate. Rebuilding/changing a published runtime requires a
  new profile ID. Model files stay outside app versions.
- Frozen Kokoro build recipe: scripts/build-kokoro.ps1 and requirements-kokoro.lock.
  GUI/Piper build dependencies: requirements-build.lock. prepare-build.py retrieves
  the checksum-pinned old runtime from GitHub for a fresh clone, without private files.
- Package includes both verified voices and license/source notices. Installer skips
  identical cached models; differing existing model/runtime files cause a clear
  failure rather than overwrite. No installer network calls.

## Conventional Windows setup executable

The user requested a normal EXE installer alongside the existing ZIP, before
publishing the Read Aloud website download. `installer/SkriviTTS.iss` and
`scripts/build-installer.ps1` package the checksum-pinned published 0.2.1 bundle;
they do not rebuild the app, change voices, or modify immutable engine profiles.
Output: `dist/installer/Skrivi-TTS-0.2.1-windows-x64-setup.exe`, separate checksum
and provenance files. Source ZIP SHA-256:
`076beea27234c6442c7f782948c2680422176eb8a172e1aef16b2f96c4e58050`.

Setup is per-user, bilingual English/Norwegian, includes both voices offline,
rejects differing existing model/runtime files, and preserves startup opt-in.
Uninstall tracks app files and shortcuts, but deliberately retains all models,
runtimes, settings, presets and user audio. Installer integration tests only run
on a disposable GitHub-hosted runner, never against the user's existing library.
Windows installer workflow 35456548862 passed on 19 September 2026 (source
bf612d1): conflict preservation, clean per-user install, installed startup,
reinstall with unchanged model/runtime/user-file hashes and timestamps,
Norwegian and English native-rate speech, and uninstall preserving persistent
data (4,244 persistent files preserved). The exact tested EXE is now an additional
v0.2.1 release asset; the original ZIPs and release tag are unchanged. Publication
workflow 35457387613 verified the successful source run, provenance, test evidence
and checksum before upload. Public installer: 605,831,689 bytes, SHA-256
`fec3c510deaedd91e8b53a171ff2dd08134ac65a763bc6dee23165dd7f22e637`.
`INSTALLER-SHA256SUMS.txt` and `INSTALLER-PROVENANCE.json` accompany the EXE;
the existing `SHA256SUMS.txt` continues to cover the original ZIPs.
The bilingual website at https://skrivi.no/read-aloud/ links to this installer.

The speech-to-text repository was renamed to `workavoidance/Skrivi-STT` at the
user's request; old GitHub URLs redirect. Do not reuse the old `Skrivi` repo name.

## Offline screen-region OCR research — 19 September 2026

User requested research, not implementation, and explicitly requires fully offline
capture, OCR and speech. Findings: `docs/OFFLINE_SCREEN_OCR_RESEARCH.md`; upstream
snapshots: `docs/OCR_RESEARCH_SOURCES.json`. Existing app remains 0.2.1, unchanged.
PowerToys/Text Grab establish region OCR; Capture2Text/NVDA establish OCR-to-speech.
Preferred product direction: bundled CPU OCR feeding the existing reader, persistent
assets, no hidden downloads or cloud fallback. Compare RapidOCR/PaddleOCR against
Windows OCR and compact Tesseract before selecting a default. Installed Windows OCR
languages are en-GB, en-US and nb; this is inventory only, not an accuracy test.
Windows.Media.Ocr has a documented package-identity support caveat. New Windows AI
OCR requires a Copilot+ NPU; the recorded Ryzen 7700/RTX4060 PC is not a match.
Next OCR work, when requested: consented/synthetic reference crops; English/Bokmål/
Nynorsk accuracy, actual CPU cold/warm latency, mixed-DPI capture, offline operation
and packaged deployment. No screen capture, model installation or rebuild performed.

OCR licensing follow-up: Apache-2.0 code/model statements checked for RapidOCR and
Tesseract; RapidOCR's linked MODEL_LICENSES.md currently returns 404. Exact shipped
artifact provenance and dependency notices are not yet cleared. User paused the
benchmark setup for this review; no OCR performance/accuracy results exist yet.
See the licensing follow-up in the research report. English Smart App Control report
also remains unresolved; do not confuse an open-source license with code signing.

## Verification during reader development

- Eleven unit tests pass: preserved models/settings/presets, bad weights, cancellation,
  future schema, inference bounds, language routing, manual override and fallback.
- Frozen Kokoro CPU cold/warm native WAV smoke tests pass: short sentence generates
  3.275 seconds of audio in 0.519 / 0.506 seconds; total wait 3.287 / 0.512 seconds.
- Frozen Talesyntese CPU cold/warm tests pass: about 2.69 seconds of audio in
  0.127 / 0.075 seconds; total wait 1.408 / 0.081 seconds, native 22,050 Hz.
- tests/check_reader_engines.py is the opt-in runner. Evidence in
  docs/READER_ENGINE_CHECKS.json; local generated WAVs under build/reader-verification.
- Exact accepted English story length remains 11 seconds. Same weights/settings/
  frontend are preserved; waveform bytes differ between inference runs, so do not
  claim byte-identical output or use WAV hashes as a voice-quality guarantee.
- Windows selected-text capture, clipboard fallback/restoration, stale-capture
  cancellation passed against a controlled sample-text window.
- Native Windows audio completion and cancellation passed with a silent test WAV:
  full 1-second playback returned after 1.25 seconds; cancellation returned in 0.22 s.
- Rendered all three reader tabs for visual review. Fixed narrow wrapped heading.
- Publication check scanned 53 historical Git blobs: no credential-pattern findings,
  no tracked file over 2 MB. Weights and user audio stay outside Git.

A packaged-startup failure was caught during installation: PyInstaller took ICU
from an unrelated Poppler directory on the machine PATH, causing QtCore import to
fail. Diagnostic removal of those two DLLs made registration pass. The corrected build uses a fresh 0.2.1 app directory so no failed 0.2.0 DLLs
can remain on its search path. The GUI build now isolates PATH to Windows/system/venv directories, and both build and package
scripts run --check-startup on the actual frozen executable. First failed install
preserved all 24 existing model/settings/voice/preset files and did not change shortcuts.
The reader's computer-use UI runner is unavailable in this tool session; controlled
Windows capture/playback tests passed, but do not claim manual installed-UI coverage.

Corrected 0.2.1 installation passed; automatic routing, both installed workers, full
playback and generation cancellation passed through the reader controller. An
app-only update recipe now excludes all models/runtimes and checks prerequisites.
Full install and app-only reinstall passed: all 24 pre-existing model/settings/
voice/preset files retained hashes and timestamps. Installed startup and second
launch passed. GitHub Actions 35454635582 passed unit tests and a clean Windows
frozen build/startup check, independently of this machine.
Full archive: 639,517,195 bytes; app-only: 40,116,442 bytes, no weights/runtimes.
App source commit 8d1f24a; update packaging 7ec23ba. SHA-256 in build/SHA256SUMS.txt.
The first public binary upload was rejected by automatic approval review, citing
prior redistribution restrictions and exact artifact approval. No release created
by that command. Exact bundled-model license checks: docs/RELEASE_LICENSE_REVIEW.md.
The licensing evidence resolved automatic approval review. Both ZIPs and checksums
were uploaded, GitHub SHA-256 values matched local files, and v0.2.1 is published:
https://github.com/workavoidance/Skrivi-TTS/releases/tag/v0.2.1.
Next: follow docs/ROADMAP.md for explicit manual update checks and Skrivi-style
Application settings, including automatic Windows UI language and manual override.
Startup-at-sign-in is already present and remains off unless the user enables it.
The user requested a manual Check for updates button, with no automatic network
checks, and explicitly said not to rebuild solely for it. docs/ROADMAP.md records
this for the next release. Current Project & updates opens GitHub when clicked.
Future: app-only updates retaining runtime/models, OCR input, wider application
selection compatibility and accessibility testing. Do not restart broad model research.

---

# Historical project record (0.1.0 and screening experiments)

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
