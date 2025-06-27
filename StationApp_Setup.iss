; Inno Setup script for Station App
[Setup]
AppName=Station App
AppVersion=1.0
DefaultDirName={pf32}\ECDC_StationApp
DefaultGroupName=Station App
OutputDir=installer
OutputBaseFilename=ECDC_StationApp_Installer_0.2.3
PrivilegesRequired=admin
AllowNoIcons=yes
DisableDirPage=no
Uninstallable=yes
SetupIconFile=dist\\utils\\icon.ico

[Files]
Source: "dist\StationApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\utils\*"; DestDir: "{app}\utils"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{commondesktop}\Station App"; Filename: "{app}\StationApp.exe"; WorkingDir: "{app}"; IconFilename: "{app}\utils\icon.ico"

[Run]
; Check if FANUC\WinOLPC exists and run the bat file if not
Filename: "{cmd}"; \
  Parameters: "/C cd ""{app}\utils"" && fanuc_portable_setup.bat"; \
  Description: "Registering FANUC DLLs..."; \
  StatusMsg: "Registering FANUC DLLs..."; \
  Flags: shellexec waituntilterminated runasoriginaluser

; Create ODBC DSN for Station App with elevated privileges 
Filename: "{cmd}"; \
  Parameters: "/C cd ""{app}\utils"" && create_odbc_dsn.bat"; \
  Description: "Creating ODBC data source for Station App..."; \
  StatusMsg: "Creating ODBC data source for Station App..."; \
  Flags: shellexec waituntilterminated runasoriginaluser

[UninstallDelete]
Type: filesandordirs; Name: "{app}\fonts"
Type: filesandordirs; Name: "{app}\utils"
