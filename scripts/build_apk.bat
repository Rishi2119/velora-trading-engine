@echo off
REM ============================================================
REM Velora Flutter App - Android APK Build Script
REM ============================================================

echo ============================================================
echo         VELORA FLUTTER APP - BUILD ANDROID APK
echo ============================================================

cd /d "%~dp0velora_flutter"

REM Check Flutter installation
where flutter >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Flutter is not installed or not in PATH
    echo Please install Flutter: https://docs.flutter.dev/get-started/install
    pause
    exit /b 1
)

echo.
echo [0/4] Configuring Android SDK path...
call flutter config --android-sdk C:\android-sdk

echo.
echo [1/4] Cleaning previous builds...
call flutter clean

echo.
echo [2/4] Getting dependencies...
call flutter pub get

echo.
echo [3/4] Building APK (release mode)...
call flutter build apk --release

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo                    BUILD SUCCESSFUL!
    echo ============================================================
    echo.
    echo APK Location:
    echo   %~dp0velora_flutter\build\app\outputs\flutter-apk\app-release.apk
    echo.
    
    REM Copy to project root for easy access
    copy /Y "build\app\outputs\flutter-apk\app-release.apk" "%~dp0velora-release.apk" >nul 2>&1
    if exist "%~dp0velora-release.apk" (
        echo Also copied to: %~dp0velora-release.apk
    )
) else (
    echo.
    echo [ERROR] Build failed. Check the error messages above.
)

echo.
pause
