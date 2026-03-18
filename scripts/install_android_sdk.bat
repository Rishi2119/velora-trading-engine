@echo off
setlocal

set SDK_ROOT=C:\android-sdk
set CMDLINE_TOOLS_DIR=%SDK_ROOT%\cmdline-tools
set JAVA_HOME=D:\Program Files\Android\Android Studio\jbr
set PATH=%JAVA_HOME%\bin;%PATH%

echo ============================================================
echo         VELORA - Android SDK Component Installer
echo ============================================================

if not exist "%SDK_ROOT%" mkdir "%SDK_ROOT%"

REM Step 1: Extraction
echo [1/4] Extracting command-line tools...
powershell -Command "Expand-Archive -Path $env:TEMP\cmdline-tools.zip -DestinationPath %SDK_ROOT%\temp -Force"

REM Step 2: Structure Fix (sdkmanager requirement)
echo [2/4] Configuring tool structure...
if not exist "%CMDLINE_TOOLS_DIR%\latest" mkdir "%CMDLINE_TOOLS_DIR%\latest"
xcopy /E /I /Y "%SDK_ROOT%\temp\cmdline-tools\*" "%CMDLINE_TOOLS_DIR%\latest\" >nul
rmdir /S /Q "%SDK_ROOT%\temp"

REM Step 3: Install Components
echo [3/4] Installing SDK components (Build Tools, Platforms)...
call "%CMDLINE_TOOLS_DIR%\latest\bin\sdkmanager.bat" --sdk_root=%SDK_ROOT% "platform-tools" "build-tools;34.0.0" "platforms;android-34"

REM Step 4: Accept Licenses
echo [4/4] Accepting Android Licenses...
echo y| call "%CMDLINE_TOOLS_DIR%\latest\bin\sdkmanager.bat" --sdk_root=%SDK_ROOT% --licenses

echo.
echo ============================================================
echo         Android SDK Setup Complete!
echo ============================================================
echo SDK Root: %SDK_ROOT%
echo.

endlocal
