# Exact bundled model check - 19 September 2026

The 0.2.1 full ZIP contains only models/kokoro-v1.0-onnx and
models/piper-talesyntese. It does NOT bundle akhbar/chatterbox-tts-norwegian,
VoxCPM2, Chatterbox model weights, NVCC weights, or user audio. Optional engine
adapters and catalog links are source code, not those model downloads.

Kokoro ONNX upstream explicitly distinguishes MIT wrapper / Apache-2.0 model:
https://github.com/thewh1teagle/kokoro-onnx#license
The original model also declares Apache-2.0:
https://huggingface.co/hexgrad/Kokoro-82M/blob/main/README.md
Exact exported model and voice-vector hashes are in models.json. Both files come
from the author's model-files-v1.1 release linked by the wrapper README.

Talesyntese's pinned model card declares CC0 for its dataset:
https://huggingface.co/rhasspy/piper-voices/blob/1162a9173d0ce503555aed757976b7a9912eae4c/no/no_NO/talesyntese/medium/MODEL_CARD
The containing voice repository declares MIT in its pinned README metadata:
https://huggingface.co/rhasspy/piper-voices/blob/1162a9173d0ce503555aed757976b7a9912eae4c/README.md
Earlier shorthand "CC0 voice" in project notes refers to this voice's dataset;
repository/model licensing and dataset licensing should be distinguished.

Bundled runtimes retain GPL/LGPL and other dependency terms; full license texts,
notices and corresponding-source/build links accompany the package. See
THIRD_PARTY_NOTICES.md and docs/SOURCES.md. The earlier conversation about
redistribution restrictions concerned a different model, not either bundled model.

Automatic approval review rejected the first public binary upload because it
flagged the prior redistribution discussion and requested exact artifact approval.
No release asset was uploaded by that rejected command. Sources remain public.

After the exact upstream licenses and archive inventory were checked, approval
review permitted the same upload. GitHub received both ZIPs with matching SHA-256
values; release v0.2.1 is now public. The initial rejection is resolved.
