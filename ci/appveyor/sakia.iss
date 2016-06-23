#define MyAppName "Sakia"
#define MyAppPublisher "Sakia team"
#define MyAppURL "http://sakia-wallet.org"
#define MyAppExeName "sakia.exe"

#if !Defined(ROOT_PATH)
#define ROOT_PATH "."
#endif

#define MyAppSrc ROOT_PATH
#define MyAppExe ROOT_PATH + "\dist\sakia\" + MyAppExeName
#pragma message MyAppSrc

#if !FileExists(MyAppExe)
#error "Unable to find MyAppExe"
#endif

#define MyAppVerStr "0.20.2"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVerStr}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#ROOT_PATH}
OutputBaseFilename={#MyAppName}
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppSrc}\dist\sakia\*"; DestDir: "{app}\"; Flags: ignoreversion recursesubdirs
Source: "{#MyAppSrc}\sakia.ico"; DestDir: "{app}\"; Flags: ignoreversion recursesubdirs
Source: "{#MyAppSrc}\sakia.png"; DestDir: "{app}\"; Flags: ignoreversion recursesubdirs
Source: "{#MyAppSrc}\LICENSE"; DestDir: "{app}\"; Flags: ignoreversion recursesubdirs
Source: "{#MyAppSrc}\ci\appveyor\after_install.cmd"; DestDir: "{app}\"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; IconFilename: "{app}\sakia.ico"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; IconFilename: "{app}\sakia.ico"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\after_install.cmd"; Description: "Delete ALL existing data"; Flags: postinstall nowait skipifsilent unchecked

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{2F4DA7A9-B15B-06FC-474C-A470394CAEAA}
LicenseFile="{#MyAppSrc}\LICENSE"
