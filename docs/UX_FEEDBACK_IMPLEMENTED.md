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
cancellation and small-window layout. Windows signed builds are the next gate.

This is a replacement acceptance candidate. Do not publish a GitHub release,
change website download links or submit Store packages until the user approves.
