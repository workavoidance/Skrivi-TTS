# Skrivi Lytt

An open-source Windows reader that turns text into speech on your computer.
A separate application from [Skrivi Snakk](https://github.com/workavoidance/Skrivi-STT),
with a familiar interface and its own orange speaker tray icon.

Both belong to the [Skrivi](https://skrivi.no/) family. Names stay Snakk and Lytt
in Norwegian and English. **Lytt** means listen: **Få teksten lest høyt** /
**Have text read aloud**.

**Name transition:** current source uses Skrivi Lytt. The published 0.2.1
installer and 0.3.0 test update still display **Skrivi TTS**; the instructions
below describe those downloads. Renamed releases preserve settings, voices,
model paths, executable names and upgrade identity.

## Reader 0.4 (release validation in progress)

Version 0.4 adds an immediate, focus-preserving activity pill for selected-text and
screen-region reading. It distinguishes capture, recognition, engine startup, model
loading, speech generation and playback. Escape cancels while a reading is active.
The pill follows Windows light/dark mode. Settings provide interface language
(Windows default, English or Bokmål), optional automatic column layout and a manual
update check. No update check runs automatically.

The release workflow signs application and runtime components, verifies the
installer and builds a separate Microsoft Store package. The reserved Lytt identity
is recorded in `store/identity.json`; its associated build and certification are
pending. UNASSOCIATED validation packages are **not for Store upload**.
See [release status and build process](docs/RELEASE_0_4.md).

## Previously delivered screen-region update (0.3.0)

The OCR update adds **Read screen region** in the reader and tray, or
**Ctrl+Alt+Shift+Space**. Put the pointer on the desired monitor, press the shortcut,
and drag around one paragraph or column. Release to read; Escape cancels selection.
Recognised text appears in the reader for review. Everything runs offline.

Install the full 0.2.1 package first, then extract the 0.3.0 OCR update and run
INSTALL.bat. Quit the existing tray app and reopen after updating. Speech models
are reused; the two OCR language files add about 7.7 MB plus the OCR runtime.
The previous app version is retained. This is a test update, with results and
limitations in [OCR_SCREENING.md](docs/OCR_SCREENING.md).

## Install and read

Download **Skrivi-TTS-0.2.1-windows-x64-setup.exe** from
[Releases](https://github.com/workavoidance/Skrivi-TTS/releases/tag/v0.2.1),
open it and follow the setup wizard. Quit Skrivi TTS before installing or updating.
Start **Skrivi TTS** from the Start menu
or desktop. No administrator account or separately installed Python is needed.
The 0.2 bundle includes the two default models (about 417 MB of weights), plus
application and engine dependencies. First installation works offline after downloading.
The ZIP remains an alternative: extract all files and run **INSTALL.bat**.
The EXE offers Norwegian/English setup and an optional desktop shortcut. Its
uninstaller removes the app and shortcuts, but keeps models, reusable runtimes,
settings and saved audio. No automatic startup is enabled by setup.

- Type or paste text, then choose **Read aloud** (or Ctrl+Enter).
- Select text in another application and press **Ctrl+Alt+Space** to read immediately.
  Press the shortcut again to stop. Alternative shortcuts are available in Settings.
- **Automatic** selects English or Norwegian for the whole passage. Mixed text is
  read with one voice. Choose a language in the reader or tray menu to override it.
  Very short or uncertain text uses the configured fallback, Norwegian by default.
- Close the window to keep the tray app running. Choose **Quit Skrivi TTS** to exit.
- Save a finished reading as a WAV if wanted. Text is not saved; temporary readings
  are removed when the app quits normally.

| Included voice | Native output | Model weights |
| --- | --- | --- |
| Piper Talesyntese, Norwegian Bokmaal male | 22.05 kHz | 63 MB |
| Kokoro Heart, American English female | 24 kHz | 354 MB including voice vectors |

Heart is the English voice approved in the listening comparison. Michael (American
male) and Emma (British female) share the same Kokoro download. Original speed and
untrimmed native speech are the defaults. Language detection is a convenience,
not a guarantee; these are Bokmaal and English voices, not a claimed Nynorsk model.

The 0.4 reader offers just Talesyntese and Kokoro. Other models remain available
in the earlier comparison app (`app/shootout.py` and version 0.1.0). Existing
downloads, presets and history are preserved; they are not deleted by this update.

## Updates and privacy

For the first installation, choose the **Windows setup EXE** (or full Windows ZIP).
After the 0.2.1 full
installation, choose **App-Update-Windows-x64.zip** for code-only releases using
the same runtimes. The update archive contains no model weights or engine runtimes.
It checks for the required runtimes and asks for the full package if they are missing.

Models, presets, reference voices and settings live in `%LOCALAPPDATA%\SkriviTTS`,
outside app versions. Reinstalling skips identical model/runtime files and never
redownloads models. Existing mismatched files are preserved and reported rather
than silently replaced. No synthesis request uploads text or audio. No telemetry,
cloud synthesis, microphone capture or automatic model downloads are implemented.

Selection capture uses Windows accessibility, with a copy/restore clipboard fallback
for applications that do not expose selection. Applications with protected content
or different privilege levels may require pasting text into the reader. Screen-area OCR runs locally using Tesseract and bundled Norwegian/English
language data. Startup at sign-in is opt-in.

All adapters currently run on CPU. Windows x64 is required; optional VoxCPM2 also
requires AVX2. Earlier releases are unsigned. The 0.4 signing workflow is being validated;
signing is not a guarantee of Windows reputation or Store certification.

## Build from GitHub

Windows x64, Python 3.12, .NET Framework 4.8. From a clone of this repository:

```powershell
python -m venv .build-env
.\.build-env\Scripts\python.exe -m pip install -r requirements-build.lock
.\.build-env\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
.\.build-env\Scripts\python.exe scripts/prepare-build.py --models
python -m venv build/english-env
.\build\english-env\Scripts\python.exe -m pip install -r requirements-kokoro.lock
.\scripts\build-kokoro.ps1
.\scripts\build.ps1
.\.build-env\Scripts\python.exe tests/check_reader_engines.py
.\.build-env\Scripts\python.exe scripts/package.py --vox-runtime build/vox-0.8.32
.\.build-env\Scripts\python.exe scripts/package-update.py build/Skrivi-TTS-0.2.1
```

`prepare-build.py` retrieves the checksum-pinned 0.1 engine runtime from GitHub;
`--models` explicitly allows preparing missing default models. Existing caches are
reused. Packaging reads the verified model cache and needs no private/local-only
source. Do not change an immutable runtime profile without assigning a new profile
ID. Later app-only updates should reuse the published runtime rather than rebuild it.
The full Kokoro environment includes build-only Torch dependencies; the distributed
English worker excludes Torch and runs the FP32 ONNX model.

GitHub Actions runs model-preservation and language-routing tests on pushes and PRs.
Real-model tests are opt-in and require weights. Recorded tests, settings, hardware
and prior listening results are under `docs/`; start at **PROJECT_STATUS.md** before
continuing development. Do not restart the old research from conversation memory.

## Build the Windows setup executable

Install Inno Setup 6, then run `./scripts/build-installer.ps1` on Windows.
This recipe downloads the published 0.2.1 full ZIP only if missing, verifies its
pinned SHA-256 and every manifest entry, and packages the exact app/voice/runtime
bytes without rebuilding them. Existing conflicting model/runtime files cause
setup to stop without overwriting them. The original ZIP remains unchanged.

`dist/installer/` contains the EXE, its separate checksum file and provenance JSON
(installer source commit, application source commit, input archive hash and
compiler version). The `Windows installer` workflow builds and exercises it on a
disposable GitHub-hosted Windows runner; `tests/check_installer.ps1` deliberately
refuses to run against a personal computer's installed data.

## Licenses

Application source and icon: MIT. Bundled Talesyntese weights: CC0. Kokoro weights:
Apache-2.0. Speech runtimes include GPL components; Qt uses LGPL. These retain their
own terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and
[corresponding sources and build instructions](docs/SOURCES.md).
