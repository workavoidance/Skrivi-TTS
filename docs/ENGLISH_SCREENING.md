# English TTS comparison — 19 September 2026

## Recommendation from this limited test

Kokoro v1.0 FP32 ONNX is the first candidate for integration into the maintained
app: American female Heart, American male Michael, and British female Emma all
completed both passages, with exact story transcripts and recovery of the intended
numeric/email details. All ran about six times faster than playback on CPU.
This is an automated word-recovery result, NOT a human naturalness preference.

Piper LJSpeech is a useful lightweight single-female-voice baseline: 1.26–1.99 s
for 10.24–16.80 s of audio. Its story was recovered exactly, but the detail passage
was transcribed as $112.50 instead of $12.50. That is a suspected error requiring
listening, not confirmed acoustic evidence.

VoxCPM2 Q4 produced exact story text but was slower than playback: 24.29 s for
11.12 s audio; details 29.42 s for 14.08 s. Its money/adjacent wording was misheard
as '12 VASPs to read three books'. It remains a reference-voice candidate, but
reference voices and GPU acceleration were not tested here.

Chatterbox multilingual Q4 ONNX produced an exact story transcript, 17.27 s for
9.64 s audio (68.82 s first load). On the numeric/email passage it failed to
reach a natural stop within 2048 tokens after 73.73 s; no truncated audio saved.
This applies to our current greedy ONNX adapter; do not generalize it to all
Chatterbox variants, including Turbo, which was researched but not tested.

## Kokoro timings (CPU, 8 threads, native speed 1.0)

| Voice | Story generation / audio seconds | Details generation / audio seconds |
|---|---|---|
| af_heart, American female | 1.772 / 11.000 | 2.670 / 16.175 |
| am_michael, American male | 2.015 / 12.175 | 2.862 / 17.750 |
| bf_emma, British female | 1.623 / 10.075 | 2.402 / 14.825 |

Kokoro ONNX session/voice loading took 1.03 s. First Python/library import and
Misaki frontend initialization are separate, not included in generation timings.
Story and detail inputs are stored in tests/english_shootout.py and evidence JSON.
All six voice configurations matched the story under lowercase/word token
comparison; this single easy passage is not a benchmark-wide accuracy score.

## Reproducibility and native-quality handling

- Existing Vox and Chatterbox weights/runtime were reused. Chatterbox language was
  explicitly en. Native model settings otherwise unchanged.
- Piper LJSpeech high-path export and Kokoro FP32 ONNX were downloaded once into
  %LOCALAPPDATA%/SkriviTTS/models/piper-ljspeech-high and kokoro-v1.0-onnx.
  The test models are cached but NOT registered in the app dropdown yet.
- Published GitHub SHA-256 digests verified both Kokoro artifacts. HF LFS SHA-256
  verified Piper weights; its config/card used pinned Git blob hashes. All exact
  URLs, sizes and final SHA-256 hashes are in ENGLISH_MODEL_MANIFEST.json.
- Kokoro-onnx 0.4.9 has an input-dtype mismatch with the release graph: its newer
  export path supplies speed as int32, while the graph requires float32. The test
  session wrapper casts only this input to float32, preserving speed=1.0. Initial
  setup attempts failed before any Kokoro WAV existed; successful results replace
  those setup errors. No model weight patch or precision downgrade was used.
- Misaki 0.9.4 G2P with espeak fallback, en_core_web_sm 3.8.0. British frontend for
  Emma and American frontend for Heart/Michael. Kokoro's default silence trimming
  was explicitly disabled (trim=False); native 24 kHz PCM16 saved. Piper 22.05 kHz
  and Vox 48 kHz also preserved. No post-synthesis resampling or speed alteration.
- Kokoro uses an isolated build/english-env, pinned installed packages saved in
  english-kokoro-requirements.txt. Installed application runtime was not modified.
- Synthesis was serial; speech recognition started only after all synthesis ended.
  These are single diagnostic timings, not repeated or controlled benchmarks.
- Offline Systran/faster-whisper-medium used the already cached model and the same
  provenance as NYNORSK_SCREENING.md; language=en, CPU INT8, beam 5, temperature 0,
  no prompt/VAD/previous-text conditioning. No generated audio was uploaded.
- ASR can repair bad speech or mishear good speech. Formatting differences such as
  '@' versus 'at', or '9:30' versus '9, 30', are not assumed TTS errors. Prosody,
  accent authenticity, date ordinal wording and pleasantness need human listening.
- Validated eleven native mono PCM16 WAVs, twelve result records including one
  synthesis failure, and all audio links in the local listening page.

## Sources and licensing

- Kokoro official card: https://huggingface.co/hexgrad/Kokoro-82M — Apache 2.0
  weights, including use in commercial products. Voice choices:
  https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- ONNX runtime wrapper: https://github.com/thewh1teagle/kokoro-onnx — MIT wrapper,
  Apache 2.0 model. Additional dependency licences still need shipping notices,
  including espeak-ng; do not label the entire dependency stack Apache-only.
- Piper model card:
  https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/high/MODEL_CARD
  identifies public-domain LJ Speech training data. Existing piper-tts runtime is
  GPL-3.0; observe its redistribution obligations. Lessac was not selected because
  its card points to a separate dataset licence needing review.
- Existing Chatterbox MIT / Vox Apache 2.0 provenance is in the main catalog.

## Run again / continue

1. tests/cache_english_models.py explicitly downloads missing assets and verifies
   hashes, reusing existing files. Its cache-only rerun passed without downloads.
2. tests/english_shootout.py --group installed (existing build Python) and
   --group kokoro (isolated English Python). Completed cases are skipped. For a
   new experimental run, use a new folder rather than replacing the saved baseline.
3. tests/english_transcribe.py --model <cached medium directory> --folder
   build/english-2026-09-19 (the existing isolated ASR environment).
4. tests/english_report.py renders build/english-2026-09-19/listen.html and archives
   docs/ENGLISH_SCREENING.json. Model downloads and audio are excluded from Git.

Next: user listening preference between Heart, Michael and Emma; then add a tested
Kokoro adapter/catalog entry and package a maintained app update. This turn added
reusable evaluation scripts/evidence, not a new application release.
