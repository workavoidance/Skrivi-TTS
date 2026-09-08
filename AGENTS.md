# Continue this application

Read PROJECT_STATUS.md, README.md and docs/ARCHITECTURE.md first. Reuse the existing
adapters and recorded experiments. This is separate from Skrivi speech-to-text.

Models, settings, voices, presets and audio are user data. Never delete, reset or
redownload them during an app update. No weights, user audio or local settings go
into Git. Preserve native synthesis defaults and synchronous full-WAV playback.

Add engine-specific controls only when implemented, range-validated and recorded
in each result. Do not advertise GPU inference until actual execution is verified.
No selected-text logging, telemetry, cloud synthesis or hidden model downloads.

Update PROJECT_STATUS.md with durable paths, versions, test evidence, limitations
and next steps. Commit substantive changes. Release packages must be built from a
recorded commit and must pass model-preservation and engine checks appropriate to
the change. Do not rewrite the app or restart broad research without a concrete need.
