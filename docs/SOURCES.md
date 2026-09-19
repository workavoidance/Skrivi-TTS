# Corresponding source and rebuilding

Skrivi TTS source, build scripts, model catalog and dependency locks are in
https://github.com/workavoidance/Skrivi-TTS. Release package.json identifies its
source commit. No private checkout or Codex installation is needed to build it.
See README.md for the Windows build commands.

Third-party libraries are unmodified upstream builds, packaged dynamically in
PyInstaller onedir directories. The Kokoro speed-input correction is in our public
engines/kokoro_engine.py. Model weights are unmodified. There is no signature,
activation check or technical restriction preventing replacement of libraries or
running modified builds. Reverse engineering for debugging modifications to LGPL
components is permitted. No application terms override the upstream licenses.

## Source downloads for the distributed components

These links provide the corresponding upstream source and build files at no charge.
Full license texts are under licenses/ and collected distribution notices are in
third_party_licenses/ in the Windows app folder. Component archives include their
own copyright notices. Versions of all Python dependencies are in the two lock files.

| Component | Source and build instructions |
| --- | --- |
| Piper 1.7.0, GPL-3.0-or-later | https://github.com/OHF-Voice/piper1-gpl/archive/refs/tags/v1.7.0.tar.gz (setup.py, CMakeLists.txt, workflows) |
| Piper's static eSpeak NG, GPL-3.0-or-later | https://github.com/espeak-ng/espeak-ng/archive/724808c.tar.gz (revision specified by Piper CMakeLists.txt) |
| Kokoro eSpeak NG 1.52.0 and loader 0.2.4 | https://github.com/thewh1teagle/espeakng-loader/archive/146599e29be31bf17d99f0bcb7dbb2f92aef3d95.tar.gz (includes espeak-ng sources, build.sh and hatch_build.py) |
| phonemizer-fork 3.3.2, GPL-3.0-or-later | https://files.pythonhosted.org/packages/42/fa/9294d2f11890ca49d0bdac7a4da60cbe5686629bfd4987cae0ad75e051cc/phonemizer_fork-3.3.2.tar.gz |
| Qt Base 6.11.2, LGPL-3.0 | https://download.qt.io/archive/qt/6.11/6.11.2/submodules/qtbase-everywhere-src-6.11.2.tar.xz |
| PySide / Shiboken 6.11.2, LGPL-3.0 | https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/pyside-setup-everywhere-src-6.11.2.tar.xz |
| libsndfile 1.2.2, LGPL-2.1-or-later | https://github.com/libsndfile/libsndfile/archive/refs/tags/1.2.2.tar.gz |
| soundfile 0.13.1 / 0.14.0, BSD | https://github.com/bastibe/python-soundfile (version tags and wheel build scripts) |
| ONNX Runtime 1.22.1 / 1.30.0, MIT | https://github.com/microsoft/onnxruntime (matching version tags) |
| Kokoro ONNX wrapper 0.4.9, MIT | https://github.com/thewh1teagle/kokoro-onnx |
| Misaki 0.9.4, Apache-2.0 | https://github.com/hexgrad/misaki |
| Kokoro 82M / voices, Apache-2.0 | https://huggingface.co/hexgrad/Kokoro-82M (export asset hashes and URLs in models.json) |
| Talesyntese, CC0 | models.json links its pinned upstream model card |
| CrispASR 0.8.32, MIT | https://github.com/CrispStrobe/CrispASR/archive/5baf533c9f5038226b4af1cd6bde3454d6bf9316.tar.gz |

Our MIT reader communicates with separately executable speech workers over a local
JSON-lines interface. The workers include GPL components, which retain GPL terms;
the project MIT license does not relicense those components. The GUI dynamically
loads LGPL Qt libraries. Rebuild Python bindings against a compatible modified Qt,
then replace the onedir libraries or rebuild the app with scripts/build.ps1.
Python speech dependencies can likewise be rebuilt and packaged with the supplied
worker host scripts. Use a new runtime profile when changing dependencies, so an
update never replaces another installed version's cached runtime.

The old 0.1.0 worker is reused byte-for-byte from its checksum-pinned release
archive. Its original build recipe and dependency lock are available at Git tag
v0.1.0. scripts/prepare-build.py retrieves it without requiring an old local install.
