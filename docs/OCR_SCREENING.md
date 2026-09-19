# Tesseract screen-region reading: 19 September 2026

Implemented for version 0.3.0 as a local test update. Tesseract 5.5.2, tesserocr
2.10.0, official tessdata_fast eng/nor, single-block segmentation (PSM 6).

## Results on this PC

- 24 synthetic paragraphs: English, Bokmal, Nynorsk and mixed text; Arial/Times;
  18/30/44 pixel fonts. With nor+eng, 22/24 exact after whitespace normalisation;
  aggregate character error rate 0.0765%. The two failures were Norwegian letters
  in 18-pixel Times. Numerical strings in these samples were preserved.
- English-first eng+nor was tried first and yielded 14/24 exact, CER 0.612%.
  Norwegian-first was selected using this development set; these are not unbiased
  held-out results. Original English-first console findings are recorded here;
  detailed final results: OCR_SCREENING.json.
- Twelve separate held-out crops (four new passages, clean/JPEG85/dark variants,
  Calibri 28) were all exact with the unchanged production worker. OCR_HOLDOUT.json.
- Median recognition with an already loaded API: 0.059 seconds. Median full frozen
  worker launch+recognition: 0.214 seconds (development crops); 0.179 seconds on the
  held-out crops. These do not include speech generation/playback or human dragging.
- Geometry tests cover 100/125/150/200% scaling and negative monitor origin with
  synthetic screen objects. Empty/malformed input, stale/cancelled results and
  reader dispatch passed. Evidence: OCR_FROZEN_CHECKS.json.
- Existing 11 unit tests and frozen Norwegian/English synthesis smoke tests passed.

These are small synthetic screens, not real-document accuracy certification.
Nynorsk OCR recognition does not change the supported pronunciation of Talesyntese.
No private screen content was captured. No real multi-monitor/HDR test was performed.
OCR code uses local files and pipes only; no firewall-enforced offline test claimed.

## Use

Ctrl+Alt+Shift+Space (or Read screen region in the window/tray) captures the monitor
under the pointer after hiding the reader. Drag one paragraph or column. Release
to recognise and read immediately. Escape cancels selection; the same shortcut or
Stop cancels recognition/speech. Recognised text is available in the reader.
Selection across monitor boundaries is not supported in this first version.
Zoom in when the image is small. Protected content may not be capturable.

The monitor image is frozen in memory before overlay drawing. Only the cropped
PNG bytes go to the separate OCR worker over a pipe. The worker returns text; no
image file or clipboard copy is created. Recognition times out after 30 seconds.
Reading uses the existing whole-passage language routing and native voices.

## Reproduce

Create build/ocr-env with Python 3.12 and install requirements-ocr.lock. Explicitly
run scripts/prepare-ocr.py once, then tests/ocr_screening.py with that environment.
Build scripts/build-ocr.ps1, run tests/ocr_holdout.py in the OCR environment and
tests/check_ocr.py in .build-env. Build the GUI using scripts/build.ps1.
Synthetic fixture PNGs live in ignored build/ocr-screening and contain no user data.

The OCR update requires the full 0.2.1 installation. It contains new GUI and OCR
assets only, no speech models or replacement speech runtimes. Persistent paths:
models/ocr-tessdata-fast-v1 and runtimes/tesseract-5.5.2-v1 under the normal library.
The prior 0.2.1 version remains available. Windows signing/trust is not established
by these developer-host tests; the reported English Smart App Control issue remains
separate and unresolved. No security settings are changed.
