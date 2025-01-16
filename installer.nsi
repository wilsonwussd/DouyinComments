; 安装程序初始定义常量
!define PRODUCT_NAME "抖音评论采集工具"
!define PRODUCT_VERSION "1.2.1"
!define PRODUCT_PUBLISHER "Wilson"
!define PRODUCT_WEB_SITE "https://github.com/wilson"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\抖音评论采集工具.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma
Unicode true

; MUI 现代界面定义
!include "MUI2.nsh"

; MUI 预定义常量
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; 欢迎页面
!insertmacro MUI_PAGE_WELCOME
; 许可协议页面
!insertmacro MUI_PAGE_LICENSE "README.md"
; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY
; 安装过程页面
!insertmacro MUI_PAGE_INSTFILES
; 安装完成页面
!define MUI_FINISHPAGE_RUN "$INSTDIR\抖音评论采集工具.exe"
!insertmacro MUI_PAGE_FINISH

; 卸载程序页面
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 安装界面包含的语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装程序版本号
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "Comments" "抖音评论采集工具安装程序"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "LegalCopyright" "Copyright (C) 2024"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "FileDescription" "抖音评论采集工具安装程序"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "ProductVersion" "${PRODUCT_VERSION}"

; 程序名称与输出文件
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "抖音评论采集工具_Setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\抖音评论采集工具"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite ifnewer
    
    ; 复制主程序文件
    File "release\抖音评论采集工具.exe"
    File "release\README.md"
    File "release\使用说明.txt"
    File "release\cookie.txt"
    File "release\cookie_json.txt"
    File "release\deepseek_api_key.txt"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\抖音评论采集工具"
    CreateShortCut "$SMPROGRAMS\抖音评论采集工具\抖音评论采集工具.lnk" "$INSTDIR\抖音评论采集工具.exe"
    CreateShortCut "$DESKTOP\抖音评论采集工具.lnk" "$INSTDIR\抖音评论采集工具.exe"
    
    ; 写入卸载信息到注册表
    WriteUninstaller "$INSTDIR\uninst.exe"
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\抖音评论采集工具.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\抖音评论采集工具.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

; 卸载部分
Section Uninstall
    ; 删除程序文件
    Delete "$INSTDIR\抖音评论采集工具.exe"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\使用说明.txt"
    Delete "$INSTDIR\cookie.txt"
    Delete "$INSTDIR\cookie_json.txt"
    Delete "$INSTDIR\deepseek_api_key.txt"
    Delete "$INSTDIR\uninst.exe"

    ; 删除快捷方式
    Delete "$SMPROGRAMS\抖音评论采集工具\抖音评论采集工具.lnk"
    Delete "$DESKTOP\抖音评论采集工具.lnk"
    RMDir "$SMPROGRAMS\抖音评论采集工具"

    ; 删除安装目录
    RMDir "$INSTDIR"

    ; 删除注册表项
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
    DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
    SetAutoClose true
SectionEnd

Function .onInit
    ; 检查是否已经安装
    ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
    StrCmp $R0 "" done
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "抖音评论采集工具已经安装。$\n$\n点击 [确定] 卸载先前的版本，或点击 [取消] 取消本次安装。" \
        IDOK uninst
    Abort
uninst:
    ExecWait '$R0 _?=$INSTDIR'
done:
FunctionEnd 