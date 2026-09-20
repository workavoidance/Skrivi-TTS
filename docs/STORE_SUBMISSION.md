# Skrivi Lytt: Microsoft Store submission

Use the **Skrivi-Lytt-0.4.3-windows-x64.msix** from the verified 0.4.3 GitHub release.
The public filename now uses Skrivi Lytt; internal SkriviTTS identifiers remain stable;
the product displayed to users is Skrivi Lytt.

## Reserved identity

- Package name: `Skrivi.SkriviLytt`
- Publisher: `CN=EF3D997F-87B2-4AD0-B65B-877EE1632E65`
- Publisher display name: `Skrivi`
- Package version: `1.4.8.0` (app version 0.4.3)
- Target: Windows 11 desktop, x64

The authoritative public values are in `store/identity.json`. Never reuse the
Skrivi Snakk identity. Do not upload the earlier UNASSOCIATED validation package.

## Upload

1. Open the **Skrivi Lytt** listing in Partner Center and create a submission.
2. Upload the associated MSIX in **Packages** and inspect the identity/version
   validation results. Use the MSIX for Store submission, not the EXE installer.
3. Complete the listing, screenshots, age ratings, privacy/support details and
   capability explanation. Review the certification notes below.
4. Submit when ready. Package validation is not Microsoft Store certification.

The outer MSIX is intended for Store signing; the enclosed application and native
components are already signed. The download is not a signed sideload installer.
Use the separately signed EXE for ordinary local testing. No certificate trust or
Windows security settings need to be changed for that installer.

## Suggested certification notes

Skrivi Lytt reads typed or selected text aloud and can recognize printed text in a
user-selected screen region. Speech synthesis and OCR run entirely on the device.
Bundled English and Norwegian Bokmal voices work without an account, network
connection or additional model downloads.

The runFullTrust capability is needed for the packaged desktop application:
global reading/cancellation shortcuts, Windows accessibility and clipboard text
selection, user-initiated region capture, and local speech/OCR worker processes.
The application does not record the microphone. It sends no selected text,
screenshots or audio to a server and contains no telemetry.

Open the application, paste text and choose Read aloud. Selected-text shortcut:
Ctrl+Alt+Space. Screen-region shortcut: Ctrl+Alt+Shift+Space. Escape cancels active
reading. The tray menu provides language controls and Quit. Closing the window
keeps the tray reader running. Startup at sign-in is optional and disabled by
default. The Store edition uses Windows startup settings and Store update controls.

## Validation boundary

The release pipeline validates the MSIX with Microsoft MakeAppx and tests the
signed desktop payload, speech engines and installer data preservation. Local
checks unpack with Microsoft MakeAppx, compare the payload hashes, start the GUI
and run offline OCR. This does not exercise Windows packaged deployment or Store
certification. Windows App Certification Kit is not installed on the build-review
machine; its certification suite has not been run. Test the Store-delivered build
before broad release, including tray startup, both hotkeys and both voices.

Microsoft references:
- [Package formats, identity and Store signing](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements)
- [Windows App Certification Kit](https://learn.microsoft.com/en-us/windows/uwp/debug-test-perf/windows-app-certification-kit)

## Automation

Run the `Skrivi Lytt Microsoft Store` bridge in the Skrivi-STT repository. It passes
that repository's existing four Microsoft secrets to Lytt's reusable workflow;
GitHub never reveals those values. Default runs only check Store access/status.
To submit an existing release, select submit and provide a tag such as v0.4.3.
The workflow verifies the MSIX checksum and embedded package identity, then
submits through Microsoft CLI 0.4.2. Certification remains Microsoft's decision.
A published submission is required; any existing draft/review stops submission.
After a failed upload, inspect Partner Center rather than deleting a draft blindly.
