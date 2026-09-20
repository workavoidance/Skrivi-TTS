# Skrivi TTS

An open-source Windows reader for local text and screen-image reading. Separate
from [Skrivi dictation](https://github.com/workavoidance/Skrivi-STT), with its own
orange speaker tray icon. Speech and OCR work offline.

## Install the signed 0.4.0 test release

Download **Skrivi-TTS-0.4.0-windows-x64-setup.exe** from
[the 0.4.0 release](https://github.com/workavoidance/Skrivi-TTS/releases/tag/v0.4.0).
Quit Skrivi TTS from its tray menu, run setup, then open it from the Start menu.
No separate Python installation or administrator account is needed.

The full installer includes two speech models (about 417 MB of weights), OCR and
signed engines. Use it once when moving from the previous unsigned engines. It
reuses matching installed model files and refuses to overwrite differing ones.
Models, settings, presets and saved audio remain outside app versions, including
when the application is uninstalled. Signing is not a promise of Windows reputation
or Store certification. This is a test release for real-world feedback.

## Read

- Type or paste text and choose **Read aloud**, or press Ctrl+Enter.
- Select text in another application and press **Ctrl+Alt+Space** for immediate reading.
- For image text, press **Ctrl+Alt+Shift+Space** and drag around a screen region.
- A light/dark activity pill shows capture, recognition, voice startup/loading,
  speech preparation and playback. **Escape** cancels while work is active.
- Automatic chooses one English or Bokmål voice for the whole passage. Override it
  in the reader or tray. Short/uncertain text uses the configured fallback.
- Close the window to keep the tray app running; use **Quit Skrivi TTS** to exit.

Settings offer Windows-default/English/Bokmål interface language, opt-in startup,
reading speed, selected-text shortcut and OCR layout. Paragraph/single-column is
the default. Automatic columns work best when selecting body text without shared
headings or footers; [the column experiment](docs/OCR_COLUMNS.md) records limitations.

| Included model | Voice / native output | Weights |
| --- | --- | --- |
| Piper Talesyntese | Bokmål male, 22.05 kHz | 63 MB |
| Kokoro | Heart, American English female, 24 kHz | 354 MB including voice vectors |

Michael (American male) and Emma (British female) share the Kokoro download.
Native speed and untrimmed speech are the defaults. These are English/Bokmål
voices, not a claimed Nynorsk speech model. The normal reader is limited to these
two models. Earlier comparisons remain in app/shootout.py; their downloads and
user data are preserved.

## Updates and privacy

**Check for updates** contacts GitHub only when clicked and reads release metadata;
it does not install anything. There are no automatic update checks or background
model downloads. Store builds open the Store's update controls instead.

User data lives in `%LOCALAPPDATA%\SkriviTTS`. Future app-only update packages can
reuse the installed signed engines and contain no model/runtime downloads. The
signed-runtimes ZIP in Releases is a developer build input, not a user installer.

No telemetry, cloud synthesis, microphone capture or uploads of text/audio/images.
Selection uses Windows accessibility, with a copy/restore clipboard fallback.
OCR uses Tesseract with bundled Norwegian/English data. Recognition stays on the
device; no screenshot files or selected-text logs are created by OCR. Protected
content or applications at a different privilege level may require pasting text.

## Build and continue development

Start with **PROJECT_STATUS.md**, [architecture](docs/ARCHITECTURE.md) and
[0.4 release details](docs/RELEASE_0_4.md). Reuse the existing adapters and evidence.
Windows x64, Python 3.12 and .NET Framework 4.8 are required.

```powershell
python -m venv .build-env
./.build-env/Scripts/python.exe -m pip install -r requirements-build.lock
python -m venv build/ocr-env
./build/ocr-env/Scripts/python.exe -m pip install -r requirements-ocr.lock
./.build-env/Scripts/python.exe scripts/prepare-release.py
./.build-env/Scripts/python.exe scripts/prepare-ocr.py
./scripts/build.ps1
./scripts/build-ocr.ps1
./.build-env/Scripts/python.exe scripts/stage-release.py
./.build-env/Scripts/python.exe tests/check_release.py
```

Build preparation reuses checksum-pinned public packages; it does not modify a
user's installed library. GUI code can change independently of signed runtimes.
The runtime pin rejects changes to frozen inputs until a new profile is assigned.
Never rebuild/re-sign different bytes under an installed runtime profile name.
Local GUI builds are unsigned; official release signing uses the reusable GitHub
workflow and the maintainer's Certum configuration. Source forks use their own
signing configuration.

The signed workflow verifies payload signatures, signs the installer/uninstaller,
tests installation/reinstallation/uninstallation on a disposable Windows runner,
and creates the Store package. Tests never install over a developer's real library.
The historical 0.2 ZIP/build recipes remain available for provenance.

## Microsoft Store

The separate TTS listing is not reserved yet. The current **UNASSOCIATED** MSIX is
for packaging validation only and **must not be uploaded**. Copy the real listing's
public identity into store/identity.json (see the example), rebuild and test the
associated package before submission. Certification has not been run.

## Licenses

Application source/icon: MIT. Talesyntese weights: CC0. Kokoro: Apache-2.0.
Speech runtimes include GPL components; Qt uses LGPL. Their licenses and source
instructions are retained. See [notices](THIRD_PARTY_NOTICES.md) and
[corresponding sources/build instructions](docs/SOURCES.md).
