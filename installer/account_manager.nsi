; NSIS installer for AccountManager
; Requires NSIS (makensis.exe) installed.

!include "MUI2.nsh"

!define APP_NAME "AccountManager"
!define APP_PUBLISHER "Eugene-74"
!define APP_EXE "AccountManager.exe"
!define APP_VERSION "1.0.0"

; Paths are relative to this .nsi file (installer\...)
!define PROJECT_ROOT ".."
!define APP_ICON "..\resources\app.ico"

Name "${APP_NAME}"
OutFile "${APP_NAME}Setup.exe"

InstallDir "$PROGRAMFILES64\\${APP_NAME}"
InstallDirRegKey HKLM "Software\\${APP_PUBLISHER}\\${APP_NAME}" "InstallDir"

RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"

  ; Copy the full PyInstaller dist folder.
  File /r "..\dist\${APP_NAME}\*"

  ; Create a stable uninstaller filename in the install folder.
  WriteUninstaller "$INSTDIR\\uninstall.exe"

  ; Shortcuts
  CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}" "" "$INSTDIR\\resources\\app.ico"
  CreateShortcut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}" "" "$INSTDIR\\resources\\app.ico"

  ; Add/Remove Programs registration
  WriteRegStr HKLM "Software\\${APP_PUBLISHER}\\${APP_NAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$\"$INSTDIR\\uninstall.exe$\""
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayIcon" "$INSTDIR\\${APP_EXE}"

SectionEnd

Section "Uninstall"
  ; Remove shortcuts
  Delete "$DESKTOP\\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\\${APP_NAME}"

  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove registry
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
  DeleteRegKey HKLM "Software\\${APP_PUBLISHER}\\${APP_NAME}"
SectionEnd
