# Next reader update

Add **Check for updates** to Settings and the tray, contacting GitHub only when
clicked. No startup, background, scheduled or periodic checks. Show installed and
available versions; prefer the app-only download when runtime requirements match.
A check must not download models or start installation. Handle offline/rate-limit
errors; no telemetry or selected text may be transmitted.

The user explicitly said not to rebuild the working app solely for this feature.
It is scheduled for the next update, not claimed as part of 0.2.1. Current
**Project & updates** opens the releases page only when clicked.

Later: image/screen-area OCR input, broader selection/accessibility testing.

## Application settings matching Skrivi

User requested the same application controls as Skrivi STT:

- Interface language defaults to **Automatic (Windows display language)**.
  Manual **English** and **Norsk bokmaal** choices, matching Skrivi's current
  supported UI languages. Reuse the resolver/translation pattern in Skrivi
  src/whisper_dictate/i18n.py at reference commit 05ed960. Norwegian nb/nn/no
  Windows locales map to the supported Bokmaal interface; other locales fall
  back to English. UI translation should update immediately and be saved.
- Keep interface language independent of speech language, voice and model choice.
- **Start Skrivi TTS when I sign in** belongs in this Application section.
  This control already exists in 0.2.1, defaults off, and only controls SkriviTTS's
  own HKCU Run entry. Preserve the choice across app updates; never change the
  separate Skrivi dictation startup entry or turn startup on from this request.
- Put the user-triggered update check in the same section. No automatic requests.

These are follow-up controls; interface translation is not implemented in 0.2.1.
The installed reader stays on the verified build while this next release is prepared.
