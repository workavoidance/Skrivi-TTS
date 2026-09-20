# UX feedback implementation and acceptance hold

The main windows now explain the anywhere workflow and show current shortcuts.
The text editor and dictation practice box are explicitly optional alternatives.
Each app has a single bilingual welcome screen, shown on the first normal opening,
with Get started, Skip introduction and direct shortcut settings. Tray Help → How
to use and the main-window help button reopen it. Sign-in startup stays quiet.
The marker is separate from speech preferences; no settings schema migration or
model redownload is introduced. If the marker cannot be saved, the introduction
can appear again on the next launch.

Mouse-wheel input over selectors/spin boxes scrolls the settings page rather than
changing values, including when the control has keyboard focus. Popup selection
and keyboard controls remain available. Controls have bounded widths; automatic
dialog defaults no longer move orange emphasis between ordinary buttons.

Snakk removes General status, names the model family (Whisper), uses a model table
with size and availability/active state, aligns shortcut labels, and scrolls the
model page at small heights. Lytt removes the sample button and routing/fallback
details from home, explains detection in General, exposes the model-folder action
directly, and uses Snakk's Privacy cards and About structure. Shortcut capture is
a separate cancellable prompt; global reading shortcuts pause during capture.

Both installers show information before installation without a separate licence
acceptance gate. MIT licence and third-party notices remain included. Installation
paths, Store identities, models, settings and user audio remain unchanged.

Validation: 218 Snakk tests plus lint/format checks; 25 Lytt unit tests and offline
GUI checks. Rendered both languages at 760×680 and 640×520. Added regression checks
for wheel scrolling, onboarding persistence, current shortcut copy, capture
cancellation and small-window layout. Signed Windows builds passed; PC acceptance is the remaining gate.

This is a replacement acceptance candidate. Do not publish a GitHub release,
change website download links or submit Store packages until the user approves.

## Signed candidates verified

Snakk 0.3.2 was built from `25283f0ef486e82508b7cf912dda7a5ccb0de854`:
https://github.com/workavoidance/Skrivi-STT/actions/runs/35537489391

Lytt 0.4.3 was built from `bc84d5fdd687ed745df37799775f1a8bd319350c`:
https://github.com/workavoidance/Skrivi-STT/actions/runs/35537490895
The later Lytt change only repairs the historical 0.2.1 installer test filename.

Both signed Windows workflows and PR checks passed. Downloaded artifacts were
verified against GitHub digests and release checksums. Both EXE signatures are
valid and timestamped, with publisher Open Source Developer Jonathan Wright.
Lytt's installed English/Bokmaal voice checks passed; reinstall and uninstall
preserved all 4,291 test data files. All 4,800 signed Lytt payload files match
inside the Store package.

| Candidate | Installer SHA-256 | Store version |
| --- | --- | --- |
| Snakk 0.3.2 | f677842a6a5896b8ca99f1533a23386bdb9866dafbed5fd33824291b9384c3e7 | 1.3.12.0 |
| Lytt 0.4.3 | 20dad4bb13bf4b80e5d5338e4ce73909313eda00ac6a4c2544e8282a26ae3499 | 1.4.8.0 |

The local workspace holds installers, Store packages, verification JSON and the
PC test checklist under `output/test-builds/round-2/`. User acceptance testing is
still pending. Promote these exact tested assets when approved. Do not merge the
Snakk version change into main prematurely: its release workflow can publish on
main pushes. No release publication, website change or Store submission is
part of this acceptance step.
