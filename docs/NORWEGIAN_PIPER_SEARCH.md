# Norwegian Piper variants — focused search, 8 September 2026

User explicitly requested other Norwegian-trained Piper models after strong
Talesyntese feedback and poor NVCC results. No broader TTS model survey was restarted.
No weights downloaded, no models installed, no training or third-party contact.

## Distinct training leads

- [NbAiLab Norwegian Piper Trimmed](https://huggingface.co/NbAiLab/nb-tts-norwegian-piper-trimmed):
  indexed model card describes a Norwegian ONNX export; the accompanying
  [demo source](https://huggingface.co/spaces/NbAiLab/nb-tts-norwegian-piper-demo/blob/main/app.py)
  identifies NST speech training and direct Piper CPU inference. Export name includes
  `olivia_piper_nsttts`; do not infer speaker gender or quality from that name alone.
  This was a candidate in the old shootout, not a newly invented model and not a
  successfully validated local voice. Fresh anonymous model metadata and config
  requests returned HTTP 401. Indexed documentation does not establish current
  download access. The Space API reports RUNNING on cpu-basic at revision
  ff60d48d223654a7cfdb12c572b8dd2824fc1835, with a ready public domain:
  https://nbailab-nb-tts-norwegian-piper-demo.hf.space/ . No synthesis call was made;
  a running Space does not prove its inference succeeds.
- [Community female-voice training effort](https://github.com/rhasspy/piper/issues/658):
  author TheStigh reported approximately 13 hours / 10,000 clips of Norwegian studio
  recordings and plans for a female voice in November 2024. This is a training
  discussion. No released model/checkpoint was verified through the issue or focused
  author searches. Do not present it as an installable voice.

## Existing models and conversions

The current [official catalog](https://huggingface.co/rhasspy/piper-voices/blob/main/voices.json)
lists Talesyntese medium and NVCC medium as the Norwegian entries. Other catalogs
often repeat these; a different repository or display name does not prove new training.

Hugging Face metadata was inspected for seven plausible alternative repositories:

| Repository | Finding |
| --- | --- |
| Derur/piper-tts-models | Norwegian Talesyntese weight SHA-256 exactly matches our installed model |
| serahgw/piper-model-original | Same Norwegian Talesyntese weight hash and configuration |
| xelcior/piper-tts-gpu | Original CPU weight hash matches Talesyntese; separate GPU-targeted graph, no verified new voice training |
| gyroing/PiperTTS-NCNN-Models | NCNN conversion of Talesyntese; ~29.1 MB ZIP, different runtime format, not another speaker |
| IhorShevchuk/piper1-voices-fp16-quantized | FP16 Talesyntese, 31,951,473 bytes; README explicitly identifies conversion from original Piper voices |
| speaches-ai/piper-no_NO-talesyntese-medium | Talesyntese packaging repository; no new training established |
| csukuangfj/vits-piper-no_NO-talesyntese-medium | Sherpa-oriented Talesyntese export, not a verified new voice |

[FP16 source](https://huggingface.co/IhorShevchuk/piper1-voices-fp16-quantized) and
[NCNN source](https://huggingface.co/gyroing/PiperTTS-NCNN-Models) could be useful for
future footprint experiments, but do not satisfy the request for new Norwegian speakers.
Their compatibility, audio quality and speed were not tested.

## Decision boundary

No additional independently trained, publicly downloadable Norwegian female Piper
voice was verified in this search beyond the already installed NVCC speakers.
This is a bounded search result, not a claim that none exists anywhere. The useful
leads are NbAiLab access/demo and the unpublished community effort. If neither yields
a usable voice, a new single-speaker fine-tune is the remaining direct route. Preserve
Talesyntese as the quality/speed baseline; do not replace it with repackaged duplicates.
