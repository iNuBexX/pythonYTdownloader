# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]
- UI: Added clickable "File exists" indicator next to the `Download Name` field. Indicator shows when the resolved output file already exists in the selected folder.
- UX: Clicking the indicator opens the OS file browser and selects the existing file (Windows Explorer supported; falls back to open folder on other OSes).
- UI: Indicator styling updated through iterations (triangle/bubble -> `⟁!` -> final clickable badge showing `File exists`).
- Dev: Added `dev_run.py` watcher that auto-restarts `app.py` on Python file changes to speed up development.
- Bugfix: Normalized and resolved absolute output path before revealing in Explorer to ensure correct selection.
- Misc: Updated `app.py` to recompute the output filename based on quality selection and to keep the indicator state in sync with folder/name/quality changes.

