# Skrivi Lytt 0.4.2 — local acceptance build

Prepared for user testing before publication. The shared Skrivi interface adds
consistent settings, immediate preference saving, shortcut controls, model
maintenance, manual update checks and error recovery. Existing data and internal
installation identities remain unchanged.

The signed PC installer is `Skrivi-Lytt-0.4.2-windows-x64-setup.exe`.
The separate `Skrivi-Lytt-0.4.2-windows-x64.msix` is for Store submission.
Do not publish, change website links or submit to Microsoft until the user has
tested the installers and explicitly approved continuing.

Signed build passed: https://github.com/workavoidance/Skrivi-STT/actions/runs/35525294007
Built TTS source: `28ffc132e8d82aaa1fff36fc4380ba4cde60e892`.
25 unit tests, offline GUI checks, signed English/Bokmål engines and installation
checks passed. Reinstall and uninstall preserved all 4,291 existing data files.
The local installer signature and timestamp are valid. SHA-256:
`e08ab2edf79666acf2ae26bfdad53ffcedf89a96e654ff90e5603bbaab7412c9`.
Store identity remains `Skrivi.SkriviLytt`, package version `1.4.7.0`.
All 4,799 Store payload files match the signed release manifest.

Local files: `../output/test-builds/lytt-0.4.2/` and `../output/test-builds/lytt-store/`.
Shared acceptance checklist and verification records are in `../output/test-builds/`.
No GitHub release, website update, local installation or Store submission performed.
