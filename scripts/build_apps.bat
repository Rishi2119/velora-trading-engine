@echo off
REM ============================================================
REM  Velora Trading System — Build Script
REM  Builds the Flutter Web and Mobile APK Applications
REM ============================================================
title Velora App Builder

echo.
echo  ╔══════════════════════════════════════╗
echo  ║     VELORA BUILDER — FLUTTER V2.0    ║
echo  ╚══════════════════════════════════════╝
echo.
echo  [1/3] Navigating to Flutter directory...
cd /d "%~dp0velora_flutter"

echo  Fetching Dependencies...
call flutter pub get

echo.
echo  [2/3] Building Flutter Web Output...
call flutter build web --release
if %errorlevel% neq 0 (
    echo  [ERROR] Web build failed. Ensure flutter is installed and available in PATH.
) else (
    echo  [SUCCESS] Web output generated at velora_flutter\build\web
)

echo.
echo  [3/3] Building Flutter Android APK...
call flutter build apk --release
if %errorlevel% neq 0 (
    echo  [ERROR] APK build failed. Check your Android SDK setup.
) else (
    echo  [SUCCESS] APK generated at velora_flutter\build\app\outputs\flutter-apk\app-release.apk
)

echo.
echo  ============================================================
echo  Build Process Complete.
echo  Run "start_api.bat" to boot the unified FastAPI backend.
echo  Run "cd velora_flutter && flutter run -d chrome" to test locally.
echo  ============================================================
echo.

pause
