@echo off
REM ================================================================
REM  install_flutter.bat  —  Download and install Flutter SDK
REM  then adds it to your user PATH permanently.
REM
REM  Run ONCE as Administrator (or regular user — PATH is user-level).
REM  After running, close and reopen any terminals.
REM ================================================================
setlocal

SET FLUTTER_DIR=C:\flutter
SET FLUTTER_ZIP=%TEMP%\flutter_windows.zip
SET FLUTTER_URL=https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.29.1-stable.zip

echo.
echo ================================================
echo  VELORA - Flutter SDK Installer
echo ================================================
echo.

REM Already installed?
IF EXIST "%FLUTTER_DIR%\bin\flutter.bat" (
    echo [OK] Flutter already installed at %FLUTTER_DIR%
    goto :add_path
)

echo [1/3] Downloading Flutter stable (this may take a few minutes)...
powershell -Command "Invoke-WebRequest -Uri '%FLUTTER_URL%' -OutFile '%FLUTTER_ZIP%' -UseBasicParsing"
IF ERRORLEVEL 1 (
    echo [ERROR] Download failed. Check your internet connection.
    exit /b 1
)

echo [2/3] Extracting to %FLUTTER_DIR%...
powershell -Command "Expand-Archive -Path '%FLUTTER_ZIP%' -DestinationPath 'C:\' -Force"
IF ERRORLEVEL 1 (
    echo [ERROR] Extraction failed.
    exit /b 1
)

del /f /q "%FLUTTER_ZIP%" 2>nul

:add_path
echo [3/3] Adding Flutter to your user PATH...
powershell -Command "$p = [System.Environment]::GetEnvironmentVariable('PATH','User'); if ($p -notlike '*C:\flutter\bin*') { [System.Environment]::SetEnvironmentVariable('PATH', $p + ';C:\flutter\bin', 'User'); Write-Host 'PATH updated!' } else { Write-Host 'Flutter already in PATH.' }"

echo.
echo ================================================
echo  Flutter installed! Run these to verify:
echo    flutter --version
echo    flutter doctor
echo.
echo  IMPORTANT: Close and reopen your terminal/
echo  Command Prompt for PATH to take effect.
echo ================================================
echo.
pause
