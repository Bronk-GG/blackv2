@echo off
setlocal enabledelayedexpansion

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

:: --- STEP 2: Find Python ---
echo [2/5] Locating Python interpreter...
set PYTHON_CMD=python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH. Please install Python.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i
echo Found Python: %PYTHON_EXE%
echo.

:: --- STEP 3: Ensure dependencies are installed ---
echo [3/5] Installing/verifying Python dependencies...
python -m pip install --quiet -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some pip installs may have failed. Continuing...
)

:: Ensure Playwright browsers are installed for the build environment
echo Installing playwright chromium for build environment (only needed once)...
python -m playwright install chromium
echo Done.
echo.

:: --- STEP 4: Locate PyInstaller executable ---
echo [4/5] Locating PyInstaller executable...

:: Try standard PATH first
where pyinstaller >nul 2>nul
if %ERRORLEVEL% EQU 0 set PYINSTALLER_EXE=pyinstaller

:: Dynamically resolve from current Python user site-packages if not found in PATH
if not defined PYINSTALLER_EXE (
    for /f "tokens=*" %%i in ('python -c "import os,site; s=site.getusersitepackages(); print(os.path.join(os.path.dirname(s),'Scripts','pyinstaller.exe'))"') do set PYINSTALLER_EXE=%%i
    if not exist "!PYINSTALLER_EXE!" set PYINSTALLER_EXE=
)

:: Install if still not found
if not defined PYINSTALLER_EXE (
    echo PyInstaller not found, installing via pip...
    python -m pip install pyinstaller
    for /f "tokens=*" %%i in ('python -c "import os,site; s=site.getusersitepackages(); print(os.path.join(os.path.dirname(s),'Scripts','pyinstaller.exe'))"') do set PYINSTALLER_EXE=%%i
    if not exist "!PYINSTALLER_EXE!" (
        echo [ERROR] Cannot locate pyinstaller.exe after installation.
        echo Run manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo Found: !PYINSTALLER_EXE!
echo.

:: --- STEP 5: Run Build ---
echo [5/5] Running PyInstaller with blackbird.spec...
echo.

:: Tell Playwright where to look for browsers at runtime inside the .exe
:: (The exe sets this itself via sys.frozen, but we also set it here so the spec resolves correctly)
for /f "tokens=*" %%i in ('python -c "import os,site; s=site.getusersitepackages(); print(os.path.join(os.path.dirname(s),'site-packages','playwright','driver'))"') do set PLAYWRIGHT_DRIVER_PATH=%%i
echo Playwright driver path: !PLAYWRIGHT_DRIVER_PATH!
echo.

"!PYINSTALLER_EXE!" blackbird.spec

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
