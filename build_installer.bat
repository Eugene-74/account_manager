@echo off
setlocal

REM Builds the .exe (PyInstaller) then builds the installer (NSIS).
REM Prereq: NSIS installed and makensis.exe on PATH.

call build_exe.bat
if errorlevel 1 (
  echo build_exe failed
  exit /b 1
)

where makensis >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: makensis.exe not found on PATH.
  echo Install NSIS, then re-run this script.
  exit /b 1
)

pushd installer
makensis account_manager.nsi
popd
if errorlevel 1 (
  echo makensis failed
  exit /b 1
)

echo.
echo Installer generated: installer\AccountManagerSetup.exe
endlocal
