; GDTT current-user Windows installer.
; Copyright (c) 2026 Akila DJ +. AI-assisted development: OpenAI Codex.

Unicode True
ManifestDPIAware True
RequestExecutionLevel user

!include "MUI2.nsh"

!ifndef APP_VERSION
  !error "APP_VERSION must be supplied by scripts/build_installer.ps1"
!endif
!ifndef APP_FILE_VERSION
  !error "APP_FILE_VERSION must be supplied by scripts/build_installer.ps1"
!endif
!ifndef BUNDLE_DIR
  !error "BUNDLE_DIR must be supplied by scripts/build_installer.ps1"
!endif
!ifndef OUTPUT_DIR
  !error "OUTPUT_DIR must be supplied by scripts/build_installer.ps1"
!endif
!ifndef OUTPUT_NAME
  !error "OUTPUT_NAME must be supplied by scripts/build_installer.ps1"
!endif

!define APP_NAME "GDTT"
!define APP_PUBLISHER "Gadash (Akila DJ)"
!define APP_EXE "GDTT.exe"
!define APP_REGISTRY_KEY "Software\Gadash (Akila DJ)\GDTT"
!define UNINSTALL_REGISTRY_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\GDTT"
!define APP_ICON "${__FILEDIR__}\..\src\data_transform_tool\resources\icons\data-transform-tool.ico"

Name "${APP_NAME}"
Caption "${APP_NAME} ${APP_VERSION} Setup"
OutFile "${OUTPUT_DIR}\${OUTPUT_NAME}"
InstallDir "$LOCALAPPDATA\Programs\GDTT"
InstallDirRegKey HKCU "${APP_REGISTRY_KEY}" "InstallLocation"
BrandingText "GDTT"
SetCompressor /SOLID lzma
CRCCheck force
Icon "${APP_ICON}"
UninstallIcon "${APP_ICON}"

VIProductVersion "${APP_FILE_VERSION}"
VIAddVersionKey /LANG=1033 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "FileDescription" "${APP_NAME} installer"
VIAddVersionKey /LANG=1033 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright (c) 2026 Akila DJ +"
VIAddVersionKey /LANG=1033 "Comments" "AI-assisted development: OpenAI Codex."

!define MUI_ABORTWARNING
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Start GDTT"
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "GDTT"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT HKCU
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${APP_REGISTRY_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "StartMenuFolder"

Var StartMenuFolder

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${__FILEDIR__}\..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "GDTT (required)" SecCore
  SectionIn RO
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${BUNDLE_DIR}\*.*"

  FileOpen $0 "$INSTDIR\.dtt-installation" w
  FileWrite $0 "GDTT ${APP_VERSION}$\r$\n"
  FileClose $0

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${APP_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"

  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegStr HKCU "${UNINSTALL_REGISTRY_KEY}" "QuietUninstallString" "$\"$INSTDIR\Uninstall.exe$\" /S"
  WriteRegDWORD HKCU "${UNINSTALL_REGISTRY_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_REGISTRY_KEY}" "NoRepair" 1
  SectionGetSize ${SecCore} $0
  WriteRegDWORD HKCU "${UNINSTALL_REGISTRY_KEY}" "EstimatedSize" $0

  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\GDTT.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Uninstall GDTT.lnk" "$INSTDIR\Uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section /o "Desktop shortcut" SecDesktop
  SetShellVarContext current
  CreateShortcut "$DESKTOP\GDTT.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

LangString DESC_SecCore ${LANG_ENGLISH} "Install GDTT — Data Transform Tool by Gadash (Akila DJ) and required runtime files."
LangString DESC_SecDesktop ${LANG_ENGLISH} "Add an optional shortcut to the current user's desktop."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} $(DESC_SecCore)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
  SetShellVarContext current
  ReadRegStr $StartMenuFolder HKCU "${APP_REGISTRY_KEY}" "StartMenuFolder"
  StrCmp $StartMenuFolder "" 0 +2
    StrCpy $StartMenuFolder "GDTT"

  Delete "$DESKTOP\GDTT.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\GDTT.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall GDTT.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  DeleteRegKey HKCU "${UNINSTALL_REGISTRY_KEY}"
  DeleteRegKey HKCU "${APP_REGISTRY_KEY}"

  IfFileExists "$INSTDIR\.dtt-installation" 0 unmarked_installation
  RMDir /r "$INSTDIR"
  Goto uninstall_complete

unmarked_installation:
  MessageBox MB_OK|MB_ICONEXCLAMATION|MB_DEFBUTTON1 \
    "The installation marker is missing, so application files were left in place for safety." /SD IDOK

uninstall_complete:
SectionEnd
