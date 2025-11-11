#!/usr/bin/env pwsh
# MarlOS Windows PowerShell Installer
# Automatically installs MarlOS and sets up PATH if needed

param(
    [switch]$AutoPath = $false
)

$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================"  -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Text)
    Write-Host "[WARNING] $Text" -ForegroundColor Yellow
}

Write-Header "MarlOS Windows Installer"

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python is installed: $pythonVersion"
} catch {
    Write-Error "Python is not installed!"
    Write-Host ""
    Write-Host "Please install Python from https://python.org"
    Write-Host "Make sure to check 'Add Python to PATH' during installation!"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$versionCheck = python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 3.11 or higher is required!"
    Write-Host "Please update Python from https://python.org"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Success "Python version is compatible"
Write-Host ""

# Install marlos
Write-Header "Installing MarlOS"
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

try {
    pip install git+https://github.com/ayush-jadaun/MarlOS.git
    Write-Host ""
    Write-Success "MarlOS installed successfully!"
} catch {
    Write-Host ""
    Write-Error "Installation failed!"
    Write-Host $_.Exception.Message
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if marl command is accessible
Write-Host "Checking if 'marl' command is accessible..." -ForegroundColor Yellow
$marlExists = Get-Command marl -ErrorAction SilentlyContinue

if ($marlExists) {
    Write-Header "SUCCESS!"
    Write-Success "The 'marl' command is ready to use!"
    Write-Host ""
    Write-Host "Quick Start:" -ForegroundColor Cyan
    Write-Host "  marl              # Interactive menu"
    Write-Host "  marl --help       # Show all commands"
    Write-Host "  marl start        # Start MarlOS"
    Write-Host "  marl status       # Check status"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

# marl not found - need to add to PATH
Write-Header "PATH Setup Required"
Write-Warning "The 'marl' command was installed but is not in your PATH."
Write-Host ""

# Get Scripts directory
$scriptsDir = python -c "import sys; print(sys.prefix + '\\Scripts')"
Write-Host "Scripts directory: $scriptsDir" -ForegroundColor Cyan
Write-Host ""

if ($AutoPath) {
    $choice = "1"
} else {
    Write-Host "Choose an option:" -ForegroundColor Yellow
    Write-Host "  1. Add to PATH automatically (recommended)"
    Write-Host "  2. Show manual instructions"
    Write-Host "  3. Use 'python -m cli.main' instead"
    Write-Host ""
    $choice = Read-Host "Enter choice (1-3)"
}

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Adding $scriptsDir to your PATH..." -ForegroundColor Yellow
        Write-Host ""

        try {
            # Get current user PATH
            $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

            # Check if already in PATH
            if ($currentPath -split ';' | Where-Object { $_ -eq $scriptsDir }) {
                Write-Warning "Scripts directory is already in PATH"
                Write-Host "Try closing and reopening your terminal, then test: marl --help"
            } else {
                # Add to PATH
                $newPath = "$currentPath;$scriptsDir"
                [Environment]::SetEnvironmentVariable("Path", $newPath, "User")

                # Also update current session
                $env:Path += ";$scriptsDir"

                Write-Success "PATH updated successfully!"
                Write-Host ""
                Write-Host "IMPORTANT:" -ForegroundColor Yellow
                Write-Host "  - For this window: Try 'marl --help' now"
                Write-Host "  - For other windows: Close and reopen them, then test 'marl --help'"
                Write-Host ""

                # Test in current session
                $marlExistsNow = Get-Command marl -ErrorAction SilentlyContinue
                if ($marlExistsNow) {
                    Write-Success "Verified: 'marl' command is now accessible!"
                }
            }
        } catch {
            Write-Error "Failed to update PATH automatically"
            Write-Host $_.Exception.Message
            Write-Host ""
            Write-Host "Please add manually (see option 2)" -ForegroundColor Yellow
        }
    }

    "2" {
        Write-Host ""
        Write-Host "Manual PATH Setup Instructions:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Press Windows + R"
        Write-Host "2. Type: sysdm.cpl"
        Write-Host "3. Press Enter"
        Write-Host "4. Click 'Advanced' tab"
        Write-Host "5. Click 'Environment Variables'"
        Write-Host "6. Under 'User variables', select 'Path'"
        Write-Host "7. Click 'Edit' then 'New'"
        Write-Host "8. Add: $scriptsDir"
        Write-Host "9. Click OK on all windows"
        Write-Host "10. Close and reopen your terminal"
        Write-Host "11. Test: marl --help"
        Write-Host ""
    }

    "3" {
        Write-Host ""
        Write-Host "You can use MarlOS without PATH setup:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  python -m cli.main --help"
        Write-Host "  python -m cli.main status"
        Write-Host "  python -m cli.main start"
        Write-Host ""
        Write-Host "Or create a PowerShell alias:" -ForegroundColor Yellow
        Write-Host '  Set-Alias marl -Value "python -m cli.main"'
        Write-Host ""
    }

    default {
        Write-Warning "Invalid choice. Showing manual instructions..."
        & $MyInvocation.MyCommand.Path
    }
}

Write-Header "Installation Complete"
Write-Host "Full documentation:" -ForegroundColor Cyan
Write-Host "  https://github.com/ayush-jadaun/MarlOS"
Write-Host ""
Write-Host "PATH setup guide:" -ForegroundColor Cyan
Write-Host "  https://github.com/ayush-jadaun/MarlOS/blob/main/docs/PATH_SETUP_QUICK_REFERENCE.md"
Write-Host ""

Read-Host "Press Enter to exit"
