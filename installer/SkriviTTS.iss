#ifndef AppVersion
#define AppVersion "0.2.1"
#endif
#ifndef PackageDir
  #error PackageDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif

#if FileExists(PackageDir + "\app\native\VerifyPackage.exe")
#define NativePreflight
#endif

[Setup]
#ifdef SignedRelease
SignTool=certum
SignedUninstaller=yes
#endif
AppId={{E9E45873-7840-45F2-B17F-7C66496302C9}
AppName=Skrivi Lytt
AppVersion={#AppVersion}
AppPublisher=Skrivi
AppPublisherURL=https://skrivi.no/read-aloud/
AppSupportURL=https://github.com/workavoidance/Skrivi-TTS/issues
AppUpdatesURL=https://github.com/workavoidance/Skrivi-TTS/releases
DefaultDirName={localappdata}\SkriviTTS\versions\{#AppVersion}
UsePreviousAppDir=no
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=Skrivi-TTS-{#AppVersion}-windows-x64-setup
UninstallFilesDir={localappdata}\SkriviTTS\uninstall
UninstallDisplayIcon={app}\SkriviTTS.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
ChangesEnvironment=no
UsedUserAreasWarning=no
InfoBeforeFile=welcome.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "{#PackageDir}\package.json"; Flags: dontcopy
#ifdef NativePreflight
Source: "{#PackageDir}\app\native\VerifyPackage.exe"; Flags: dontcopy
#else
Source: "preflight.ps1"; Flags: dontcopy
#endif
Source: "{#PackageDir}\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PackageDir}\runtimes\*"; DestDir: "{localappdata}\SkriviTTS\runtimes"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs
Source: "{#PackageDir}\models\*"; DestDir: "{localappdata}\SkriviTTS\models"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Skrivi Lytt"; Filename: "{app}\SkriviTTS.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Skrivi Lytt"; Filename: "{app}\SkriviTTS.exe"; WorkingDir: "{app}"; Check: WantDesktopShortcut

[Run]
Filename: "{app}\SkriviTTS.exe"; Description: "{cm:LaunchProgram,Skrivi Lytt}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
english.PreflightFailed=An existing model or runtime differs from this package, or could not be checked. It has not been overwritten. See the setup log and verify your installation before trying again.
norwegian.PreflightFailed=En eksisterende modell eller motor er forskjellig fra denne pakken, eller kunne ikke kontrolleres. Den er ikke overskrevet. Se installasjonsloggen og kontroller installasjonen før du prøver igjen.
english.RegisterFailed=Voice registration failed. Setup did not finish. See the setup log.
norwegian.RegisterFailed=Registrering av stemmene mislyktes. Installasjonen ble ikke fullført. Se installasjonsloggen.
english.KeepData=Downloaded voices, runtimes, settings and saved audio are kept when you uninstall.
norwegian.KeepData=Nedlastede stemmer, motorer, innstillinger og lagret lyd beholdes når du avinstallerer.

[Code]
function WantDesktopShortcut: Boolean;
var
  Shell, Link: Variant;
  OldPath, Target, VersionRoot: String;
begin
  Result := WizardIsTaskSelected('desktopicon');
  OldPath := ExpandConstant('{userdesktop}\Skrivi TTS.lnk');
  if Result or not FileExists(OldPath) then Exit;
  try
    Shell := CreateOleObject('WScript.Shell');
    Link := Shell.CreateShortcut(OldPath);
    Target := ExpandFileName(Link.TargetPath);
    VersionRoot := ExpandConstant('{localappdata}\SkriviTTS\versions\');
    Result := (CompareText(Copy(Target, 1, Length(VersionRoot)), VersionRoot) = 0) and
      (CompareText(ExtractFileName(Target), 'SkriviTTS.exe') = 0);
  except
    Result := False;
  end;
end;

procedure RenameOwnedShortcut(OldPath, NewPath: String);
var
  Shell, Link: Variant;
  Target, VersionRoot: String;
begin
  if not FileExists(OldPath) then Exit;
  try
    Shell := CreateOleObject('WScript.Shell');
    Link := Shell.CreateShortcut(OldPath);
    Target := ExpandFileName(Link.TargetPath);
    VersionRoot := ExpandConstant('{localappdata}\SkriviTTS\versions\');
    if (CompareText(Copy(Target, 1, Length(VersionRoot)), VersionRoot) <> 0) or
      (CompareText(ExtractFileName(Target), 'SkriviTTS.exe') <> 0) then Exit;
    if not FileExists(NewPath) then begin
      if not FileCopy(OldPath, NewPath, True) then Exit;
      Link := Shell.CreateShortcut(NewPath);
      Link.TargetPath := ExpandConstant('{app}\SkriviTTS.exe');
      Link.WorkingDirectory := ExpandConstant('{app}');
      Link.IconLocation := ExpandConstant('{app}\SkriviTTS.exe') + ',0';
      Link.Save;
    end;
    DeleteFile(OldPath);
  except
    Log('Could not migrate an old Skrivi TTS shortcut; it was left in place.');
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  Arguments: String;
begin
  ExtractTemporaryFile('package.json');
#ifdef NativePreflight
  ExtractTemporaryFile('VerifyPackage.exe');
  Arguments := '"' + ExpandConstant('{tmp}\package.json') + '" "' +
    ExpandConstant('{localappdata}\SkriviTTS') + '"';
  if not ExecAndLogOutput(ExpandConstant('{tmp}\VerifyPackage.exe'),
    Arguments, '', SW_HIDE, ewWaitUntilTerminated, ResultCode, nil) or (ResultCode <> 0) then
    Result := CustomMessage('PreflightFailed')
  else
    Result := '';
#else
  ExtractTemporaryFile('preflight.ps1');
  Arguments := '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{tmp}\preflight.ps1') + '" -ManifestPath "' +
    ExpandConstant('{tmp}\package.json') + '" -LibraryRoot "' +
    ExpandConstant('{localappdata}\SkriviTTS') + '"';
  if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    Arguments, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
    Result := CustomMessage('PreflightFailed')
  else
    Result := '';
#endif
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  ExistingStartup: String;
begin
  if CurStep <> ssPostInstall then Exit;
  if not Exec(ExpandConstant('{app}\SkriviTTS.exe'), '--register-bundled',
    ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) or
    (ResultCode <> 0) then RaiseException(CustomMessage('RegisterFailed'));
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run',
    'SkriviTTS', ExistingStartup) then
    RegWriteStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run',
      'SkriviTTS', '"' + ExpandConstant('{app}\SkriviTTS.exe') + '" --tray');
  RenameOwnedShortcut(ExpandConstant('{userprograms}\Skrivi TTS.lnk'),
    ExpandConstant('{userprograms}\Skrivi Lytt.lnk'));
  RenameOwnedShortcut(ExpandConstant('{userdesktop}\Skrivi TTS.lnk'),
    ExpandConstant('{userdesktop}\Skrivi Lytt.lnk'));
end;

procedure InitializeWizard;
begin
  WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 +
    CustomMessage('KeepData');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ExistingStartup: String;
begin
  if CurUninstallStep <> usUninstall then Exit;
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run',
    'SkriviTTS', ExistingStartup) and
    (CompareText(ExistingStartup, '"' + ExpandConstant('{app}\SkriviTTS.exe') +
    '" --tray') = 0) then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'SkriviTTS');
end;
