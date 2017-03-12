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

#define MyAppVerStr "0.30.12"

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
Source: "{#MyAppSrc}\ci\appveyor\vcredist_x86.exe"; DestDir: "{tmp}\"; Flags: ignoreversion deleteafterinstall
Source: "{#MyAppSrc}\ci\appveyor\vcredist_x64.exe"; DestDir: "{tmp}\"; Flags: ignoreversion deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; IconFilename: "{app}\sakia.ico"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; IconFilename: "{app}\sakia.ico"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
#define VCmsg "Installing Microsoft Visual C++ Redistributable...."

[Run]
Filename: "{tmp}\vcredist_x86.exe"; StatusMsg: "{#VCmsg}"; Check: not IsWin64 and not VCinstalled
Filename: "{tmp}\vcredist_x64.exe"; StatusMsg: "{#VCmsg}"; Check: IsWin64 and not VCinstalled
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\after_install.cmd"; Description: "Delete ALL existing data"; Flags: postinstall nowait skipifsilent unchecked

[Code]
function VCinstalled: Boolean;
 // By Michael Weiner <mailto:spam@cogit.net>
 // Function for Inno Setup Compiler
 // 13 November 2015
 // Returns True if Microsoft Visual C++ Redistributable is installed, otherwise False.
 // The programmer may set the year of redistributable to find; see below.
 var
  names: TArrayOfString;
  i: Integer;
  dName, key, year: String;
 begin
  // Year of redistributable to find; leave null to find installation for any year.
  year := '';
  Result := False;
  key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall';
  // Get an array of all of the uninstall subkey names.
  if RegGetSubkeyNames(HKEY_LOCAL_MACHINE, key, names) then
   // Uninstall subkey names were found.
   begin
    i := 0
    while ((i < GetArrayLength(names)) and (Result = False)) do
     // The loop will end as soon as one instance of a Visual C++ redistributable is found.
     begin
      // For each uninstall subkey, look for a DisplayName value.
      // If not found, then the subkey name will be used instead.
      if not RegQueryStringValue(HKEY_LOCAL_MACHINE, key + '\' + names[i], 'DisplayName', dName) then
       dName := names[i];
      // See if the value contains both of the strings below.
      Result := (Pos(Trim('Visual C++ ' + year),dName) * Pos('Redistributable',dName) <> 0)
      i := i + 1;
     end;
   end;
 end;

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{2F4DA7A9-B15B-06FC-474C-A470394CAEAA}
LicenseFile="{#MyAppSrc}\LICENSE"
