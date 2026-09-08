# Third-party components and source provenance

Skrivi TTS application source is MIT; see LICENSE. Third-party models and runtimes
keep their own licenses. Model weights are downloaded separately and are not part
of the application archive or Git repository.

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
