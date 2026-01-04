# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]
- UI: Added clickable "File exists" indicator next to the `Download Name` field. Indicator shows when the resolved output file already exists in the selected folder.
- UX: Clicking the indicator opens the OS file browser and selects the existing file (Windows Explorer supported; falls back to open folder on other OSes).
- UI: Indicator styling updated through iterations (triangle/bubble -> `⟁!` -> final clickable badge showing `File exists`).
- Dev: Added `dev_run.py` watcher that auto-restarts `app.py` on Python file changes to speed up development.
- Bugfix: Normalized and resolved absolute output path before revealing in Explorer to ensure correct selection.
- Misc: Updated `app.py` to recompute the output filename based on quality selection and to keep the indicator state in sync with folder/name/quality changes.

- Bugfix: Fixed Explorer reveal behavior — clicking the `File exists` badge now opens Windows Explorer and selects the actual existing output file (previously opened Documents).

## Planned / TODO
- Add batch downloads and playlist support with queue management and concurrency controls.
- Provide overwrite/skip/auto-increment file-exists strategies in settings.
- Improve trim UI: visual timeline, presets, and frame-accurate seeking.
- Add format presets (mobile, desktop, HQ, podcast) and bitrate controls.
- Persist download queue and resumable state across app restarts.
- Add unit tests for `utils/` and set up CI to run tests and linting.
- Create platform installers and improve PyInstaller spec files.
- Add optional anonymous analytics and crash-reporting (opt-in only).
- Add a preferences dialog to manage FFmpeg path, output patterns, and defaults.
- Implement automatic updates check and notify users of new releases.
- Add keyboard shortcuts and accessibility improvements.
- Provide localization support (i18n) for multiple languages.

