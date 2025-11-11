@echo off
REM MarlOS Windows Installer
REM Automatically installs MarlOS and sets up PATH if needed

echo.
echo ========================================
echo   MarlOS Windows Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version
echo.

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11 or higher is required!
    echo Please update Python from https://python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python version is compatible
echo.

REM Install marlos
echo Installing MarlOS...
echo This may take a few minutes...
echo.
pip install git+https://github.com/ayush-jadaun/MarlOS.git

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed!
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] MarlOS installed successfully!
echo.

REM Check if marl command is accessible
where marl >nul 2>&1
if %errorlevel% equ 0 (
    echo ========================================
    echo   SUCCESS!
    echo ========================================
    echo.
    echo The 'marl' command is ready to use!
    echo.
    echo Quick Start:
    echo   marl              Interactive menu
    echo   marl --help       Show all commands
    echo   marl start        Start MarlOS
    echo.
    goto :end
)

REM marl not found - need to add to PATH
echo ========================================
echo   PATH Setup Required
echo ========================================
echo.
echo The 'marl' command was installed but is not in your PATH.
echo.

REM Get Scripts directory
for /f "delims=" %%i in ('python -c "import sys; print(sys.prefix + '\\Scripts')"') do set SCRIPTS_DIR=%%i

echo Scripts directory: %SCRIPTS_DIR%
echo.
echo Choose an option:
echo   1. Add to PATH automatically (recommended)
echo   2. Show manual instructions
echo   3. Use 'python -m cli.main' instead
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" goto :auto_path
if "%choice%"=="2" goto :manual_path
if "%choice%"=="3" goto :python_module
goto :manual_path

:auto_path
echo.
echo Adding %SCRIPTS_DIR% to your PATH...
echo.

REM Add to user PATH
setx PATH "%PATH%;%SCRIPTS_DIR%"

if %errorlevel% equ 0 (
    echo [OK] PATH updated successfully!
    echo.
    echo IMPORTANT: Close this window and open a new Command Prompt or PowerShell
    echo Then test: marl --help
    echo.
) else (
    echo [ERROR] Failed to update PATH automatically
    echo Please add manually (see instructions below^)
    echo.
    goto :manual_path
)
goto :end

:manual_path
echo.
echo Manual PATH Setup Instructions:
echo.
echo 1. Press Windows + R
echo 2. Type: sysdm.cpl
echo 3. Press Enter
echo 4. Click "Advanced" tab
echo 5. Click "Environment Variables"
echo 6. Under "User variables", select "Path"
echo 7. Click "Edit" then "New"
echo 8. Add: %SCRIPTS_DIR%
echo 9. Click OK on all windows
echo 10. Close and reopen your terminal
echo 11. Test: marl --help
echo.
goto :end

:python_module
echo.
echo You can use MarlOS without PATH setup:
echo.
echo   python -m cli.main --help
echo   python -m cli.main status
echo   python -m cli.main start
echo.
echo Or add a shortcut:
echo   doskey marl=python -m cli.main $*
echo.
goto :end

:end
echo ========================================
echo.
echo Full documentation:
echo   https://github.com/ayush-jadaun/MarlOS
echo.
echo PATH setup guide:
echo   https://github.com/ayush-jadaun/MarlOS/blob/main/docs/PATH_SETUP_QUICK_REFERENCE.md
echo.
pause
