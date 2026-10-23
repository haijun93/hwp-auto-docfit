#define AppName "한글편집 후처리 (HWP_AutoDocFit)"
#define AppVersion GetEnv("DOCFIT_VERSION")
#define AppExe "HWP_AutoDocFit.exe"

[Setup]
AppId={{A7D3B5B8-824B-4F97-A33D-C208F6E895F4}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=HWP_AutoDocFit
DefaultDirName={localappdata}\Programs\HWP_AutoDocFit
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=HWP_AutoDocFit_v{#AppVersion}_Setup
SetupIconFile=..\resources\app_icon.ico
UninstallDisplayIcon={app}\{#AppExe}
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
CloseApplications=yes
RestartApplications=no
AppMutex=Global\HWP_AutoDocFit_SingleInstance_Mutex,Local\HWP_AutoDocFit_SingleInstance_Mutex
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
Uninstallable=yes

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕 화면 바로 가기 만들기"; GroupDescription: "추가 바로 가기:"; Flags: unchecked

[Files]
Source: "..\dist\HWP_AutoDocFit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "한글편집 후처리 실행"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.hwp\shell\HwpAutoDocFit"; Flags: dontcreatekey uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.hwpx\shell\HwpAutoDocFit"; Flags: dontcreatekey uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\HwpAutoDocFit"; Flags: dontcreatekey uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shell\HwpAutoDocFit"; Flags: dontcreatekey uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shell\HwpAutoDocFit"; Flags: dontcreatekey uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shell\HwpAutoDocFit"; Flags: dontcreatekey uninsdeletekey
