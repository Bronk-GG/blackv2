@echo off
setlocal enabledelayedexpansion

:: Always run from the directory this .bat lives in
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
echo Script directory: %SCRIPT_DIR%

echo =========================================
echo  Building Blackbird OSINT Executable...
echo =========================================
echo.

:: --- STEP 1: Cleanup ---
echo [1/5] Cleaning up old build artifacts...
if exist "build" (
    rd /s /q "build"
    if !ERRORLEVEL! NEQ 0 echo [WARNING] Could not remove 'build' directory.
)
if exist "dist" (
    rd /s /q "dist"
    if !ERRORLEVEL! NEQ 0 echo [WARNING] Could not remove 'dist' directory.
)
if exist "blackbird.exe" del /f /q "blackbird.exe"
echo Done.
echo.

:: --- STEP 2: Auto-detect Python interpreter ---
echo [2/5] Locating Python interpreter...
set PYTHON=

:: Try common options in order of preference
for %%P in (python py "py -3.13" "py -3.12" "py -3.14" "py -3.11") do (
    if not defined PYTHON (
        %%P --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 set PYTHON=%%P
    )
)

if not defined PYTHON (
    echo [ERROR] No Python installation found in PATH.
    echo         Please install Python from https://python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('!PYTHON! -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i
for /f "tokens=*" %%v in ('!PYTHON! -c "import sys; print(sys.version.split()[0])"') do set PYTHON_VER=%%v
echo Found Python !PYTHON_VER!: %PYTHON_EXE%
echo.

:: --- STEP 3: Install dependencies ---
echo [3/5] Installing/verifying Python dependencies...

:: Install everything except aiohttp first
!PYTHON! -m pip install --quiet -r requirements.txt --ignore-requires-python

:: aiohttp may fail to compile C extensions if MSVC is missing.
:: Try pre-built binary wheel first, then fall back to pure-python mode.
!PYTHON! -m pip install --quiet "aiohttp>=3.9" --only-binary :all: 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] aiohttp binary wheel not found, trying source install...
    !PYTHON! -m pip install --quiet "aiohttp>=3.9"
)

:: Install playwright
!PYTHON! -m pip install --quiet "playwright>=1.50.0"
echo Installing Playwright Chromium browser (only needed once)...
!PYTHON! -m playwright install chromium
echo Done.
echo.

:: --- STEP 4: Install PyInstaller ---
echo [4/5] Installing PyInstaller...
!PYTHON! -m pip install --quiet pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)
echo PyInstaller ready.
echo.

:: --- STEP 5: Run Build ---
echo [5/5] Running PyInstaller with blackbird.spec...
echo.

:: Resolve Playwright driver path for the spec
for /f "tokens=*" %%i in ('!PYTHON! -c "import os, playwright; print(os.path.join(os.path.dirname(playwright.__file__), 'driver'))"') do set PLAYWRIGHT_DRIVER_PATH=%%i
echo Playwright driver path: !PLAYWRIGHT_DRIVER_PATH!
echo.

:: Guard: make sure blackbird.spec is present before running
if not exist "%SCRIPT_DIR%blackbird.spec" (
    echo [ERROR] blackbird.spec not found in: %SCRIPT_DIR%
    echo         Make sure you are running build.bat from the blackbird project folder.
    pause
    exit /b 1
)

!PYTHON! -m PyInstaller "%SCRIPT_DIR%blackbird.spec"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =========================================
    echo  Build Successful!
    echo  Output: dist\blackbird.exe
    echo.
    echo  NOTE: On first run, if Chromium has not
    echo  been downloaded yet, Blackbird will auto-
    echo  install it to %%LOCALAPPDATA%%\ms-playwright
    echo  ^(this happens once silently in background^)
    echo =========================================
) else (
    echo.
    echo =========================================
    echo  Build Failed!
    echo  Check the output above for errors.
    echo =========================================
)

echo.
pause
exit /b %ERRORLEVEL%
