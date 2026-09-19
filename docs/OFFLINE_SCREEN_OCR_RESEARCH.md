# Offline screen-region reading: research and recommendation

Research date: 19 September 2026. Status: design research, not an implemented feature.
The user explicitly requires fully offline operation, consistent with Skrivi.
No screen contents were captured, OCR models installed, or application binaries changed.

## Recommendation

Add **Read screen region** as another input source for the existing reader:

**Shortcut or tray action → draw a rectangle → local OCR → existing language choice → speech.**

This is feasible for ordinary visible screen content without cooperation from the
application displaying it. The source can be a website image, scanned PDF, presentation,
or application that does not expose selectable text. Recognition operates on pixels;
it does not make the original image into a selectable document.

Use a bundled CPU OCR engine as the preferred product direction. Compare RapidOCR
with a Norwegian-capable PaddleOCR model against Windows' already-installed OCR
before choosing the engine. Include Tesseract as a compact reference. Do not choose
on upstream benchmark claims alone. Windows OCR is an attractive local baseline,
but its documented package-identity requirement needs resolution for our current
unpackaged distribution. No cloud OCR or cloud fallback belongs in this design.

## What existing applications demonstrate

| Application | Established approach | Lesson for Skrivi TTS |
| --- | --- | --- |
| [PowerToys Text Extractor](https://learn.microsoft.com/en-us/windows/powertoys/text-extractor) | Shortcut, rectangular selection, recognition and clipboard output; installed OCR languages determine coverage. | The region-selection interaction is familiar and practical. Replace clipboard output with our reader input. |
| [Text Grab](https://github.com/TheJoeFin/Text-Grab) | Local OCR with Windows OCR and optional alternative engines; text editing and accessibility-based extraction. | Separate capture, recognition and review. Accessible text remains useful for existing selected-text reading, but cannot solve true image text by itself. |
| [Snipping Tool](https://support.microsoft.com/en-US/Windows/Apps/use-snipping-tool-to-capture-screenshots) | Text actions recognise text locally in a captured image. | Users already understand drawing a rectangle. This does not establish a public API for embedding Snipping Tool's private implementation. Snips can be auto-saved depending on settings. |
| [Capture2Text](https://capture2text.sourceforge.net/) | Screen-area OCR with optional speech output and per-language speech settings; Norwegian recognition is listed. | The complete capture-to-speech interaction already has precedent. Treat this older tool as a design reference rather than a required dependency. |
| [NVDA](https://www.nvaccess.org/post/in-process-10th-june-2026/) | OCR of the navigator object; newer options automatically read the result and highlight its location. | Reading immediately and highlighting recognised text are established accessibility patterns. We do not need to bundle a full screen reader. |

PowerToys and Text Grab are MIT-licensed. Their source can inform an implementation,
with required attribution if code is reused. Other applications above are examples,
not proposed code imports. [PowerToys' implementation notes](https://github.com/microsoft/PowerToys/blob/main/doc/devdocs/modules/textextractor.md)
describe screen capture and per-screen overlays; its WPF implementation need not
replace our existing Qt interface.

## OCR engine choices

### Existing Windows OCR: useful baseline, distribution caveat

`Windows.Media.Ocr` runs locally and uses Windows-installed recognition languages.
A read-only inventory on this computer returned **en-GB, en-US and nb (Bokmål)**.
No language download is needed to attempt an English/Bokmål baseline here.

However, Microsoft's [API documentation](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr?view=winrt-26100)
says desktop support requires package identity, describing MSIX deployment. Other
utilities using the API do not remove that support requirement. Our current app is
an unpackaged PyInstaller application. The inventory was obtained in the Codex
execution environment: it proves installed languages, not supported deployment of
our independently launched binary. Investigate packaging/support before relying on
this engine for every user; do not change installer architecture casually.

Missing languages would require explicit OS-managed provisioning. Do not copy
Windows OCR binaries into our model bundle. Its word locations are useful for later
selection/highlighting; do not assume its results include calibrated confidence.

### RapidOCR / PaddleOCR: preferred self-contained candidate

[RapidOCR](https://github.com/RapidAI/RapidOCR) provides local inference, including
ONNX Runtime. Its project and model licensing statements identify Apache-2.0
licensing; retain upstream notices and verify the exact chosen artifacts before shipping.

The current [model catalogue](https://github.com/RapidAI/RapidOCRDocs/blob/main/docs/model_list.md)
includes PP-OCRv6 support from RapidOCR 3.9.0. Compare small and tiny tiers; consider
a mature PP-OCRv5 Latin mobile configuration as an alternative. Pin detection,
recognition, dictionaries and any orientation model together, not just a package name.
Configuration can trigger automatic downloads, which our adapter must prevent.
Explicit local paths and complete bundled assets are mandatory.

[PaddleOCR's PP-OCRv6 documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv6/PP-OCRv6.en.md)
lists English and Norwegian (`no`) among its supported languages. The recognition
model is shared across languages within each tier: selecting English alone does not
necessarily produce a smaller download. Earlier model families require deliberate
selection of a Norwegian-capable recogniser; do not assume a Chinese/English default
is suitable. Upstream language coverage is not a measurement of our screenshot accuracy.

This is the strongest distribution candidate because we can control and preserve
its assets without requiring Windows language packs. Total shipped size, startup
cost and CPU performance still need measurement. Use an isolated OCR dependency
profile rather than changing the working speech runtimes.

### Tesseract: compact, mature comparison

[Tesseract](https://github.com/tesseract-ocr/tesseract) and
[tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) provide Apache-2.0
engine/model options. GitHub file metadata reports `eng.traineddata` at 4,113,088
bytes and `nor.traineddata` at 3,610,079 bytes: about **7.7 MB combined weights**,
excluding the executable, Leptonica and other runtime dependencies.

The [language inventory](https://tesseract-ocr.github.io/tessdoc/Data-Files.html)
includes Norwegian. Its [quality guidance](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)
explains preprocessing and page-segmentation sensitivity. A small screenshot region
is not always a scanned page: short lines, sparse labels, tiny type and columns need
appropriate settings. This makes a useful compact reference and potential fallback,
not an assumed accuracy winner.

### New Windows AI OCR: unsuitable baseline for this PC

Microsoft's [current hardware table](https://learn.microsoft.com/en-us/windows/ai/apis/)
lists Text Recognition as **Copilot+ NPU only**, with neither GPU nor CPU support.
Other Windows AI APIs having broader hardware support does not change this row.
The project's recorded Ryzen 7 7700 / RTX 4060 / 32 GB machine does not meet that
NPU requirement. The graphics card is not a substitute for this API.

The [TextRecognizer API](https://learn.microsoft.com/en-us/windows/ai/apis/text-recognition)
offers useful geometry and confidence data, but model readiness/provisioning must
also be handled. Consider this only as an optional future backend for suitable
hardware, never the sole implementation or a hidden download path.

## Proposed experience and architecture

1. Invoke **Read screen region** from the tray or a separate configurable shortcut.
   Keep the existing selected-text shortcut. Avoid taking over Windows Snipping Tool
   or PowerToys shortcuts by default.
2. Freeze the visible desktop before drawing the selection overlay. Drag a rectangle;
   Escape cancels. Selection must work across monitors with different scale factors.
3. Send the selected pixels to a local worker. Show a brief cancellable recognition
   state. Empty/failed recognition should produce a clear message, not spoken guesses.
4. Submit the resulting passage through the existing reader boundary. Retain whole-
   passage automatic English/Norwegian choice and the user's manual override.
5. Read immediately, with an optional review/correction view. Keep recognised text
   available transiently for correction or rereading, without automatically saving it.

Input providers already sit apart from synthesis in `app/reader_core.py` and
`app/windows_reader.py`; a region provider should use that boundary. Generation IDs
must invalidate stale capture/OCR results, so cancelling never produces delayed speech.
A worker keeps capture/recognition failures and dependencies out of the UI process.

Do not confuse **interface language**, **OCR recognition language**, and **speech
language**. Norwegian recognition is not a promise of a Nynorsk speech voice. None
of the investigated language labels establishes dedicated Nynorsk accuracy. Test
Nynorsk directly, preserve its spelling, and keep the earlier Talesyntese speech
findings separate. Avoid automatic rewriting, translation, or LLM-based correction.

## Fully offline requirement

- Capture, recognition, language routing and synthesis operate locally with network
  access unavailable. No uploads, cloud fallback, telemetry or account requirement.
- Include the chosen OCR assets in the full installer, following the user's preference
  for an understandable initial download. An optional explicit offline asset import
  can be added later. No first-use download surprises.
- Store pinned OCR assets outside versioned app folders, in the persistent model
  library. App-only updates reuse them. A new dependency set gets a new runtime ID.
- Keep screenshots and OCR text in memory/IPC; no screenshot archive, automatic
  clipboard copy, content logs or debug dumps. Explicit user exports are separate.
  A frozen desktop can transiently contain pixels outside the rectangle; discard
  those promptly after selection. This is not a claim to control OS paging/dumps.
- No continuous monitoring. Capture only when invoked. Do not use network model URLs
  as OCR inputs. Verify cold launch and repeated recognition with network blocked.

## Windows capture and accuracy pitfalls

[Qt QScreen](https://doc.qt.io/qt-6/qscreen.html#grabWindow) is a plausible first
capture route for our existing GUI. Its coordinates and returned image scaling
require care: map device-independent selection coordinates to actual pixels,
including negative monitor origins and mixed DPI. Capture before overlay drawing
so recognition does not see our dimming, border or status text.

[Windows.Graphics.Capture](https://learn.microsoft.com/en-us/windows/apps/develop/media-authoring-processing/screen-capture)
is another route if testing exposes limitations. Its asynchronous frame and colour
handling is more involved; HDR content needs appropriate conversion. Neither API
should be selected merely because it is newer.

Only visible pixels can be read. Occluded, scrolled-off or illegibly small words
cannot be reliably recovered. Protected/secure content can be unavailable, including
windows excluded through [display affinity](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity).
Report unsupported capture instead of promising universal access.

Recognition errors can sound convincing. In particular, check numbers, currency,
dates, names, punctuation and æ/ø/å. Joining lines must not merge columns or silently
remove meaningful hyphens. Preserve block geometry for reading order; a simple global
sort by vertical position can interleave columns. Recommend a tight paragraph-sized
selection initially. Tables and arbitrary page layouts need additional evaluation.

## Next experiment, when implementation work is requested

Prepare 24–40 consented or synthetic screen crops with manually checked reference
text: English, Bokmål, Nynorsk and mixed passages; numbers/names; light/dark themes;
small fonts; line wraps; columns; screenshots of scans. Do not collect private
screen contents by default or commit them to GitHub.

Compare Windows OCR, a pinned RapidOCR Norwegian-capable configuration and Tesseract
on identical crops, CPU first. Record character/word errors, critical-number errors,
missing/duplicated text and reading order. Report Nynorsk separately. OCR confidence
is not a substitute for ground truth and scores are not comparable across engines.

Measure cold and warm recognition time, peak memory, shipped weights plus runtime
size, and end-to-end selection-release-to-speech delay on this actual PC. Record
median and slow cases separately. A useful proposed target is warm recognition of
a normal paragraph within about one second; this is a goal, not an observed result.
Keep speech generation time separate from OCR so we know where latency originates.

Verify multi-monitor capture at 100/125/150/200% scaling, cancellation, repeated
requests, HDR where available, fresh installed launch outside Codex, and complete
operation with networking unavailable. Test clean installation and an app-only
update retaining existing voice and OCR assets.

Choose one default OCR backend after those results. Do not bundle several engines
permanently without a demonstrated user benefit. Preserve the two approved voices
and their native synthesis settings throughout.

## Evidence and limits

This report combines primary-source documentation and read-only local inventory.
**No OCR accuracy, capture compatibility or OCR latency benchmark was run.** No
OCR runtime was added to the application. No implementation is promised by 0.2.1.
Upstream source revisions and reported licenses are recorded in
[OCR_RESEARCH_SOURCES.json](OCR_RESEARCH_SOURCES.json); they are research snapshots,
not a shipping dependency lock or complete redistribution audit.

## Licensing follow-up and research readiness

The user paused benchmark setup to request explicit trade-offs and licensing detail.
Research is sufficient to shortlist candidates, not to certify a distributable bundle
or claim a measured accuracy winner. No OCR benchmark has completed.

- RapidOCR and PaddleOCR code: Apache-2.0. RapidOCR's README explicitly applies
  Apache-2.0 to the applicable upstream weights and converted artifacts too.
  However, the linked root MODEL_LICENSES.md returned 404 on 19 September 2026,
  including following the README hyperlink. Exact artifact provenance/hashes/notices
  remain a release gate; do not present the repository license alone as full clearance.
- Tesseract engine and official tessdata_fast repository: Apache-2.0. The precise
  packaged Windows build still needs review of Leptonica, image libraries and wrapper
  notices. The 7.7 MB English/Norwegian figure covers weights, not the full runtime.
- ONNX Runtime: MIT at https://github.com/microsoft/onnxruntime/blob/main/LICENSE.
  Its distribution's third-party notices and exact dependencies still apply.
- Apache-2.0 permits use, modification and redistribution, including free or paid
  distribution. Include the license, preserve required attribution/NOTICE content,
  and identify changed upstream files. It does not require relicensing our whole
  application under Apache-2.0. Permissions are subject to the actual license terms;
  repository licensing does not automatically cover unrelated model downloads.
- Windows OCR is an OS capability, not an open-source model bundle. Invoke the
  supported OS API; do not assume permission to repackage Windows language assets.
  Package-identity support and clean-machine provisioning remain separate questions.
- Existing PowerToys/Text Grab UI code is MIT if reused with its notices. Their
  project licenses do not relicense Microsoft's underlying OCR components.

A breadth check also considered EasyOCR (https://github.com/JaidedAI/EasyOCR): its
code is Apache-2.0 and it supports local CPU execution, bounding boxes and confidence.
Its documented Windows setup requires PyTorch/torchvision and chosen weights can
be downloaded automatically. This adds another runtime family to our application;
keep it as a reserve candidate if the primary shortlist underperforms. No exact
EasyOCR weight bundle has been cleared or benchmarked here.

Before publishing OCR binaries: pin every shipped model/runtime file, retain source
and license evidence plus hashes, assemble third-party notices, verify offline cold
launch, and test signed/packaged execution independently of the development host.
The reported English Smart App Control issue is a separate unresolved trust/signing
problem; open-source licensing does not itself establish Windows execution trust.
