# Shared Skrivi interface patterns

Implemented in development on 20 September 2026. These changes are not present
in the published Snakk 0.3.0 and Lytt 0.4.1 signed installers.

Both applications use an app-specific main window and separate Settings with
General, Shortcuts, Models, Privacy and About sections. Preferences save when
changed; failed saves restore the previous controls and explain the failure.
Downloads, file verification and other model operations remain explicit actions.

Normal launch opens the main window; launching again raises the existing window.
Closing a window leaves the application in the notification area. Quit exits.
Sign-in startup remains quiet. Snakk provides microphone/language/shortcut status
and a temporary dictation practice area; Lytt keeps text, voice and speed together.

Shortcuts can be changed and restored to defaults. Lytt's screen-region shortcut
is configurable and rejects conflicts with its selected-text shortcut. Both apps
offer an optional activity indicator with cancellation and persistent recovery
controls. Model management uses Download, Locate existing files and Verify files.
Lytt's model-folder command is under Advanced; normal reading omits engine timing.

About and tray menus offer manual update checks, help and feedback. Update checks
include numbered GitHub test releases and never offer an older version. Store
builds direct users to Store updates. Checks only run when requested.

Existing models, data directories, engine settings, saved audio and installation
identities are preserved. No dictation history or shared model deletion is added.
Snakk's practice text is discarded when its window closes.

Validation: Snakk has 215 passing tests plus bilingual rendered window checks;
Lytt has 25 unit tests and an offline GUI check covering navigation, failed-save
rollback, shortcut conflicts, indicator preference and translation. Packaged
Windows CI remains required before merge. A subsequent versioned signed release
and installed accessibility/audio checks are separate from this source update.
