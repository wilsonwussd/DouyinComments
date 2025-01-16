#define MyAppName "Douyin Comments"
#define MyAppNameCN "抖音评论采集工具"
#define MyAppVersion "1.2.1"
#define MyAppPublisher "Wilson"
#define MyAppURL "https://github.com/wilson"
#define MyAppExeName "DouyinComments.exe"

[Setup]
AppId={{8C0D6A9F-3355-4C64-8CA5-F2E5E4E8F8D1}
AppName={#MyAppNameCN}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppNameCN}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=DouyinComments_Setup_{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LanguageDetectionMethod=uilanguage
ShowLanguageDialog=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "release\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\readme.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "release\cookie.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "release\cookie_json.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "release\deepseek_api_key.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppNameCN}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppNameCN}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppNameCN}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppNameCN}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppNameCN, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1') then
  begin
    if MsgBox('检测到已安装旧版本，是否卸载？' + #13#10 + '点击"是"卸载旧版本并继续安装，点击"否"取消安装。', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      if RegQueryStringValue(HKEY_LOCAL_MACHINE, 
          'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1',
          'UninstallString', UninstallString) then
      begin
        UninstallString := RemoveQuotes(UninstallString);
        Exec(UninstallString, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      end;
    end
    else
      Result := False;
  end;
end; 