# Build Windows EXE + Installer

## Prerequisites

- Windows
- Python venv in `accountManagerEnv\\env` (already in this repo)
- NSIS installed (so `makensis.exe` is available on PATH)

## Build the EXE

Run:

- `build_exe.bat`

Output:

- `dist\\AccountManager\\AccountManager.exe`

## Build the installer (includes uninstall.exe)

Run:

- `build_installer.bat`

Output:

- `installer\\AccountManagerSetup.exe`

Notes:

- The installer installs into `Program Files\\AccountManager`.
- It creates Start Menu + Desktop shortcuts.
- It writes an uninstaller at `{install}\\uninstall.exe` and registers it in Windows “Apps & features”.
