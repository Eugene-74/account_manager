@echo off
setlocal

echo.
echo ================================================
echo AccountManager Release Script
echo ================================================
echo.

REM --- Step 1/4: Build EXE ---
echo Step 1/4: Building EXE...
call build_exe.bat
if errorlevel 1 (
  echo ERROR: build_exe failed
  pause
  exit /b 1
)

set "EXE_PATH="
if exist "dist\AccountManager.exe" (
  set "EXE_PATH=dist\AccountManager.exe"
) else if exist "dist\AccountManager\AccountManager.exe" (
  set "EXE_PATH=dist\AccountManager\AccountManager.exe"
)

if "%EXE_PATH%"=="" (
  echo ERROR: EXE not found in dist\
  echo Expected dist\AccountManager.exe or dist\AccountManager\AccountManager.exe
  pause
  exit /b 1
)

REM --- Step 2/4: Build installer (NSIS) ---
echo.
echo Step 2/4: Building installer...
where makensis >nul 2>&1
if errorlevel 1 (
  echo ERROR: makensis.exe not found on PATH.
  echo Install NSIS, then re-run this script.
  pause
  exit /b 1
)

pushd installer
makensis account_manager.nsi
set "NSIS_ERR=%errorlevel%"
popd
if not "%NSIS_ERR%"=="0" (
  echo ERROR: makensis failed
  pause
  exit /b 1
)

set "INSTALLER_PATH=installer\AccountManagerSetup.exe"
if not exist "%INSTALLER_PATH%" (
  echo ERROR: Installer not found: %INSTALLER_PATH%
  pause
  exit /b 1
)

REM --- Step 3/4: Read version (from NSIS config) ---
echo.
echo Step 3/4: Reading version...
set "RAW_VERSION="
for /f "tokens=3" %%a in ('findstr /B /C:"!define APP_VERSION" installer\account_manager.nsi') do set "RAW_VERSION=%%a"
set "RAW_VERSION=%RAW_VERSION:"=%"
set "RAW_VERSION=%RAW_VERSION: =%"

if "%RAW_VERSION%"=="" (
  echo ERROR: Could not read version from installer\account_manager.nsi
  echo Expected a line like: !define APP_VERSION "1.0.0"
  pause
  exit /b 1
)

set "VERSION=v%RAW_VERSION%"
echo Creating release for version %VERSION%...

REM --- Step 4/4: Create Git tag + GitHub release ---
echo.
echo Step 4/4: Creating GitHub Release...

where gh >nul 2>&1
if errorlevel 1 (
  echo ERROR: gh CLI not found on PATH.
  echo Install GitHub CLI: https://cli.github.com/
  pause
  exit /b 1
)

REM Check if tag exists and delete it
git tag -l %VERSION% | findstr /C:"%VERSION%" >nul 2>&1
if %errorlevel% equ 0 (
    echo Tag %VERSION% already exists, deleting...
    git tag -d %VERSION% >nul 2>&1
    git push origin :refs/tags/%VERSION% >nul 2>&1
)

REM Create git tag
git tag -a %VERSION% -m "Release %VERSION%"
if errorlevel 1 (
  echo ERROR: Failed to create git tag %VERSION%
  pause
  exit /b 1
)

git push origin %VERSION%
if errorlevel 1 (
  echo ERROR: Failed to push tag %VERSION% to origin
  pause
  exit /b 1
)

REM Create GitHub release using gh CLI
gh release create %VERSION% ^
    "%EXE_PATH%" ^
    "%INSTALLER_PATH%" ^
    --title "%VERSION%" ^
    --notes "Release %VERSION%"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create GitHub release
    pause
    exit /b 1
)

echo.
echo ================================================
echo GitHub Release %VERSION% created successfully!
echo Assets:
echo - %EXE_PATH%
echo - %INSTALLER_PATH%
echo ================================================

endlocal
