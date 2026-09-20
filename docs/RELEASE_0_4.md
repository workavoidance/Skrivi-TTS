# Reader 0.4 release work

Implemented: focus-preserving bottom-of-screen progress pill, light/dark styling,
explicit capture/OCR/startup/loading/generation/playback phases, global Escape only
while active, stale-event rejection and persistent error display. Native engine
progress events distinguish actual loading from synthesis and preserve the old
worker protocol for comparison tools. Two approved models in the normal reader;
legacy downloads, settings and shootout are retained. Optional PSM 3 automatic
column layout, English/Bokmal UI choice with Windows default, manual metadata-only
GitHub update check. No automatic network checks or app/model downloads.

Signing: scripts/sign-release.ps1 signs previously unsigned EXE/DLL/PYD/PS1 files,
preserves valid third-party signatures, timestamps new signatures and fails on
invalid signatures. New signed runtime profiles avoid changing existing unsigned
profiles. Final package hashes are generated after signing. The reusable workflow
can use the existing STT repository's Certum secrets without exporting their values.

Store: scripts/build-store.py requires the separately reserved TTS product identity.
User confirmed the listing is not reserved yet. --validation-only produces a clearly
UNASSOCIATED package solely to validate structure, not for upload/certification.
Store build uses bundled read-only models/runtime files, writable per-user settings,
Windows-managed startup and Store-managed updates. It has no microphone capability.
No Store submission or certificate-trust changes are performed automatically.

Validation so far: existing unit tests; live Qt widget render checks in light/dark;
pill does not steal foreground; stale/cancelled events cannot reopen it; error
survives worker completion; English/Bokmal switching; two-model list. Engine and
signed-package validation still required before claiming a signed release.

Local frozen checks now pass: GUI startup, cold/warm generation for both native
speech engines, real Escape registration, OCR modes 3/6, crop DPI mapping and
stale/cancelled result handling. See READER_0_4_LOCAL_CHECKS.json. These local
binaries are not the signed release; CI signatures and installer tests are separate.

After a successful signed release, publish and pin its signed runtime archive.
Later code-only updates must reuse those exact bytes. Rebuilding/re-signing changes
hashes and requires a new runtime profile; never reuse an installed profile ID for
new signed bytes.

Microsoft references: [Store package requirements](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements)
and [startup extension parameters](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap5-extension).
The Store signs the outer MSIX during submission. The validation artifact is not
associated with a reserved listing and is not a sideload installer.
