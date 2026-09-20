# Signed reader 0.4

0.4.1 integrates the Skrivi Lytt name and reserved Store identity. All release checks passed.

Published as a test release after explicit user approval:
https://github.com/workavoidance/Skrivi-TTS/releases/tag/v0.4.1.
Built source 410df3850ec32176bc6578d9e0dd12f900d0925a; successful workflow run
https://github.com/workavoidance/Skrivi-STT/actions/runs/35517692394.

Focus-preserving bottom-screen light/dark pill, real worker progress, active Escape,
two-model reader, optional OCR columns, interface-language controls and manual
update checks are implemented. Existing native model quality/defaults are retained.

The workflow verified 370 payload signatures, both speech engines, first install,
reinstall, conflicting-file preservation, uninstall, 4,291 retained data files and
the signed uninstaller. Installer signature/timestamp and both signed speech engines
also passed locally. Microsoft-unpacked Store payload: all 4,795 hashes match;
GUI startup and signed OCR column recognition passed. These checks do not replace
user listening or installed Store certification testing.

Evidence: READER_0_4_LOCAL_CHECKS.json, RELEASE_0_4_1_INSTALL_CHECKS.json,
RELEASE_0_4_1_ENGINE_CHECKS.json, RELEASE_0_4_1_STORE_CHECKS.json,
OCR_FROZEN_CHECKS.json and release assets
SIGNATURES.json / INSTALLER-SIGNATURES.json / SHA256SUMS.txt.

The installer uses the signed native/VerifyPackage.cs helper to validate existing
model/runtime checksums before copying files. It never overwrites conflicting files.
Valid upstream executable signatures are retained; unsigned components receive
Certum SHA-256 signatures with RFC3161 timestamps. The generated uninstaller is
signed through Inno Setup's signing hook.

SIGNED_RUNTIME_ARCHIVE.json pins the published runtime archive and frozen source
inputs. prepare-release.py and stage-release.py verify and reuse the exact bytes;
sign-release.ps1 preserves their valid signatures. An intentional frozen dependency
change needs a new runtime profile and pin. Code-only releases can reuse the current
profiles; model downloads and user data do not belong to application versions.

The reserved Skrivi.SkriviLytt identity is recorded in store/identity.json.
The associated 0.4.1 package (1.4.6.0) passed MakeAppx validation, payload hash checks,
GUI startup, offline OCR and both voices cold/warm. All 4,280 runtime files match
the immutable 0.4.0 pin. Windows App Certification Kit and Store-deployed testing
have not run. See STORE_SUBMISSION.md. Previous 0.4.0 package 1.4.3.0
is UNASSOCIATED and NOT FOR UPLOAD. The Store signs the outer package on submission; no
certificate trust changes or submission were performed here.

Local structure validation used Microsoft-signed MakeAppx from official NuGet
Microsoft.Windows.SDK.BuildTools 10.0.26100.9169. Archive SHA-256:
6000c971fc9155052a8359779b30b6682c39e091664d83b3852c4702ab6d238e.
Use Microsoft MakeAppx to unpack MSIX files: raw ZIP extraction retains URI-encoded
filenames such as %21v, unlike Windows package deployment.

References: [Store package requirements](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements),
[startup extension parameters](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-uap5-extension),
[Inno signing](https://jrsoftware.org/ishelp/topic_setup_signtool.htm).
