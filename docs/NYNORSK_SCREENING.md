# Nynorsk screening — 19 September 2026

## Result

Preliminary automated screening only; no human pronunciation verdict. None of the
three models is certified accurate for Nynorsk by this experiment. Talesyntese is
still the best candidate to listen to first, based on speed, prior user preference,
and retention of the numeric values in the automatic transcript.

Two synthetic passages were generated with native defaults and no reference voice.
Piper and Vox produced both WAVs. Chatterbox exhausted its 2048-token budget without
an ending on the words passage, so the application correctly refused to save it.
A separate Chatterbox run completed the numbers passage with a natural stop.

| Model | Words generation / audio | Numbers generation / audio | Automatic screening |
|---|---|---|---|
| Talesyntese | 0.574 / 10.228 s | 0.278 / 10.077 s | All intended numeric values recovered. Suspect phrases around kvifor, roysta di, byrjar and final words. |
| VoxCPM2 Q4 | 23.396 / 10.280 s | 28.221 / 12.800 s | Several word disagreements; 349 recovered as 340 plus spurious text. |
| Chatterbox Q4 ONNX | Failed: no natural stop | 21.970 / 12.040 s | Numbers and several phrases not recovered reliably. |

Times exclude model loading. Chatterbox's successful run loaded in 61.767 s.
These are single diagnostic runs, not controlled performance benchmarks.

## Method and limitations

Used the actual frozen installed TTS worker and existing weights; source worker,
Chatterbox adapter and Vox native host were hash-checked against installed 0.1.0
and matched. Model downloads, app settings and runtime dependencies were unchanged.
No audio trimming, speed changes or synthesis resampling were applied.

ASR: existing Systran/faster-whisper-medium cache, revision
08e178d48790749d25932bbc082711ddcfdfbc4f. Model SHA-256:
9b45e1009dcc4ab601eff815b61d80e60ce3fd8c74c1a14f4a282258286b51ae.
Ran CPU INT8, 8 threads, beam 5, temperature 0, language no, transcription,
no VAD, no initial prompt, and no conditioning on previous text. ASR internally
converts input audio to its required format; original playback WAVs are preserved.
Dependencies were installed in isolated build/nynorsk-asr-env; no model weights
were downloaded. Exact package versions are saved alongside this report.

Whisper rewrote some Nynorsk as Bokmal. That is not evidence that the TTS itself
translated the text. It may also mishear good speech or repair bad speech. Thus
no WER/accuracy percentage or phonetic correctness claim is appropriate here.
The garbled transcripts identify listening targets, not confirmed TTS errors.
Only one run per passage/model was attempted, with no statistical generalization.
Talesyntese is stochastic; fixed seed applies only where the adapter exposes one.

The initial failed Chatterbox test's cleanup hit a process-wait timeout. Its error
was recovered from captured output and recorded in synthesis.json. The runner now
uses graceful EOF shutdown after completed requests. No orphan from this test was
left; a pre-existing user application worker was preserved. No product code changed.
Dependency setup overlapped some initial synthesis, and the first ASR screen
started near the end of the failed Chatterbox run; do not use its runtime as a
performance benchmark. Piper/Vox finished before ASR started.

## Artifacts and repeatability

- tests/nynorsk_accuracy.py: original passages, default settings and resumable generation.
- tests/nynorsk_transcribe.py: offline transcription using a supplied local model directory.
- tests/nynorsk_report.py: builds the local HTML comparison and evidence JSON.
- docs/NYNORSK_SCREENING.json: timings, settings, revisions, transcripts and WAV hashes.
- build/nynorsk-2026-09-19/listen.html: local listening report with all five WAVs.

Run synthesis with the existing build Python. Existing results are skipped; use a
new output directory in the script for a genuinely new experimental run. ASR needs
the isolated environment recorded in nynorsk-asr-requirements.txt and the existing
local medium model. No weights or WAVs are committed to Git.

Next: native Nynorsk listening review of Talesyntese first, especially kvifor,
roysta di, byrjar and endings. Compare Vox/Chatterbox without treating automatic
Bokmal spelling as proof of wrong pronunciation. Long-passage Chatterbox failure
is a reproducible-input lead, not evidence that every Nynorsk sentence fails.
