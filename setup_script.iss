
[Setup]
AppName=MIACT
AppVersion=1.0.0
DefaultDirName={autopf}\MIACT
DefaultGroupName=MIACT
OutputDir=..\installers
OutputBaseFilename=MIACT_v1.0.0_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\MIACT\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MIACT"; Filename: "{app}\MIACT.exe"
Name: "{commondesktop}\MIACT"; Filename: "{app}\MIACT.exe"

[Run]
Filename: "{app}\MIACT.exe"; Description: "Launch MIACT"; Flags: nowait postinstall skipifsilent
