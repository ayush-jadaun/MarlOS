@echo off
REM Quick Build and Test Script for Windows

echo.
echo ========================================
echo   MarlOS - Build and Test
echo ========================================
echo.

REM Check if in correct directory
if not exist "setup.py" (
    echo [ERROR] Run this script from the MarlOS root directory
    pause
    exit /b 1
)

echo [1] Building package...
echo.

REM Install build tools if needed
pip install --quiet build twine

REM Clean old builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.egg-info" rmdir /s /q *.egg-info

REM Build package
python -m build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Package built!
echo.
echo Built files:
dir /b dist
echo.

echo ========================================
echo   Testing Installation
echo ========================================
echo.

REM Test installation
echo [2] Testing local install...
pip uninstall -y marlos
pip install dist\marlos-1.0.5-py3-none-any.whl

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation test failed!
    pause
    exit /b 1
)

echo.
echo [3] Verifying command...
marl --version

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Command verification failed!
    echo The 'marl' command is not accessible
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Package built and tested successfully!
echo.
echo Wheel file: dist\marlos-1.0.5-py3-none-any.whl
echo.
echo Next steps:
echo   1. Test locally: marl --help
echo   2. Share wheel file with testers
echo   3. Or push to GitHub: git push origin main
echo   4. Testers install: pip install git+https://github.com/ayush-jadaun/MarlOS.git
echo.
pause
