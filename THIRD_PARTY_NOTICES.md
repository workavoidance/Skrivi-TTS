# Third-party components and source provenance

Skrivi TTS application source is MIT; see LICENSE. Third-party models and runtimes
keep their own licenses. The 0.2 reader bundle includes Talesyntese (CC0) and Kokoro (Apache-2.0) weights.
Weights are release assets, never Git source files. Optional models download only
on request. See docs/SOURCES.md (SOURCES.md in the app) for source/build links.

- Public OpenBMB VoxCPM2 and cstr Q4_K conversion: Apache-2.0. Exact conversion
  revision and checksum are in models.json.
  https://huggingface.co/cstr/voxcpm2-GGUF/tree/d426b5da661d5f833b45663879b1a0b0573a5b8e
- CrispASR v0.8.32: MIT, source revision 5baf533c9f5038226b4af1cd6bde3454d6bf9316.
  Reused Windows runtime includes LICENSE and THIRD_PARTY_NOTICES.txt, including
  notices for the supplied OpenBLAS and native dependencies.
  https://github.com/CrispStrobe/CrispASR/tree/5baf533c9f5038226b4af1cd6bde3454d6bf9316
- Chatterbox multilingual model and ONNX conversion: MIT.
  https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX/tree/452d3f434aa592098f1eedac9099f33642ab2da5
- Piper TTS 1.7.0: GPL-3.0-or-later; includes eSpeak NG phonemization components.
  Its runtime remains in the separate engine process. Upstream source/build files:
  https://github.com/OHF-Voice/piper1-gpl
  https://github.com/espeak-ng/espeak-ng
  Piper NVCC and Talesyntese voice data are CC0; see the pinned upstream model cards.
- ONNX Runtime 1.22.1: MIT; NumPy: BSD; tokenizers: Apache-2.0;
  soundfile: BSD with LGPL libsndfile; psutil: BSD; Python: PSF license.
- PyInstaller 6.22.2: GPL with bootloader exception. It packages the application
  and reusable dependency host; its license does not replace dependency licenses.

Exact dependency versions are in requirements-build.lock. The Windows package
preserves license files collected from its installed dependency distributions and
the unchanged CrispASR runtime notices. See those files for full texts.

## Reader 0.2 additions

- Kokoro 82M / voice vectors: Apache-2.0, hexgrad and contributors. Unmodified FP32
  ONNX export by thewh1teagle; exact release URLs and SHA-256 in models.json.
- kokoro-onnx 0.4.9: MIT. Misaki 0.9.4: Apache-2.0. spaCy 3.8.16 and
  en_core_web_sm 3.8.0: MIT. ONNX Runtime 1.30.0: MIT.
- phonemizer-fork 3.3.2 and eSpeak NG 1.52.0: GPL-3.0-or-later.
  espeakng-loader 0.2.4: MIT wrapper, GPL speech library.
- PySide6-Essentials, Shiboken and Qt 6.11.2: used under LGPL-3.0, dynamically
  linked and replaceable. Full GPL/LGPL texts are provided in licenses/.
- langdetect 1.0.9: Apache-2.0.
- Reader theme adapted from workavoidance/Skrivi, commit 05ed960, MIT.
  Copyright 2026 Skrivi contributors. See the project MIT LICENSE.
- App speaker icon: original vector drawing in app/branding.py, project MIT.

requirements-kokoro.lock records the isolated English build environment. Torch is
an installation dependency of the frontend but is excluded from the distributed
runtime; English inference uses ONNX Runtime CPU. Runtime license collections may
include notices for build dependencies not shipped in the executable.
