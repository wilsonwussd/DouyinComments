@echo off
chcp 65001 >nul

echo [INFO] Checking Inno Setup installation...
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%INNO_PATH%" (
    echo [ERROR] Inno Setup not found
    echo Please download and install Inno Setup 6 from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
)

echo [INFO] Checking release folder...
if not exist "release\DouyinComments.exe" (
    echo [ERROR] Executable not found in release folder
    echo Please run build_exe.bat first
    pause
    exit /b 1
)

echo [INFO] Creating installer...
"%INNO_PATH%" /Q "setup.iss"

echo [INFO] Checking installer...
if exist "DouyinComments_Setup_1.2.1.exe" (
    echo [SUCCESS] Installer created successfully:
    echo DouyinComments_Setup_1.2.1.exe
) else (
    echo [ERROR] Failed to create installer
)

pause 