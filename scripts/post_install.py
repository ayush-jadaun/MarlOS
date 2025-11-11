#!/usr/bin/env python3
"""
Post-installation script for MarlOS
Checks if the marl command is accessible and provides setup instructions
"""

import os
import sys
import platform
from pathlib import Path
import subprocess
import shutil


def get_scripts_dir():
    """Get the Python Scripts directory"""
    if platform.system() == "Windows":
        scripts_dir = Path(sys.prefix) / "Scripts"
    else:
        scripts_dir = Path(sys.prefix) / "bin"
    return scripts_dir


def is_in_path(directory):
    """Check if a directory is in PATH"""
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    return str(directory) in path_dirs


def check_marl_command():
    """Check if marl command is accessible"""
    return shutil.which("marl") is not None


def print_banner():
    """Print installation banner"""
    print("\n" + "="*70)
    print("  MarlOS Installation Complete!")
    print("="*70 + "\n")


def print_success():
    """Print success message"""
    print("✅ SUCCESS! The 'marl' command is ready to use.\n")
    print("Quick Start:")
    print("  marl              # Interactive menu")
    print("  marl --help       # Show all commands")
    print("  marl start        # Start MarlOS")
    print("  marl status       # Check status")
    print("\n" + "="*70 + "\n")


def print_path_warning(scripts_dir):
    """Print PATH setup warning"""
    system = platform.system()

    print("⚠️  WARNING: 'marl' command not found in PATH!\n")
    print(f"The marl.exe script was installed to:")
    print(f"  {scripts_dir}\n")
    print("But this directory is not in your system PATH.\n")

    if system == "Windows":
        print("🔧 FIX IT NOW:\n")
        print("Option 1 - Add to PATH (Recommended):")
        print(f'  1. Press Windows + R, type "sysdm.cpl", press Enter')
        print(f'  2. Advanced → Environment Variables')
        print(f'  3. Under "User variables", select "Path" → Edit → New')
        print(f'  4. Add: {scripts_dir}')
        print(f'  5. OK → Restart PowerShell/CMD\n')

        print("Option 2 - PowerShell Command (Run as Admin):")
        print(f'  [Environment]::SetEnvironmentVariable("Path", $env:Path + ";{scripts_dir}", "User")\n')

        print("Option 3 - Use Full Path:")
        print(f'  {scripts_dir / "marl.exe"} --help\n')

        print("Option 4 - Use Python Module:")
        print(f'  python -m cli.main --help\n')

    elif system == "Darwin":  # macOS
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            rc_file = "~/.zshrc"
        else:
            rc_file = "~/.bash_profile"

        print("🔧 FIX IT NOW:\n")
        print(f"Add this line to {rc_file}:")
        print(f'  export PATH="{scripts_dir}:$PATH"\n')
        print("Then reload:")
        print(f'  source {rc_file}\n')

    else:  # Linux
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            rc_file = "~/.zshrc"
        elif "fish" in shell:
            rc_file = "~/.config/fish/config.fish"
        else:
            rc_file = "~/.bashrc"

        print("🔧 FIX IT NOW:\n")
        print(f"Add this line to {rc_file}:")
        print(f'  export PATH="{scripts_dir}:$PATH"\n')
        print("Then reload:")
        print(f'  source {rc_file}\n')

    print("📖 Full Guide: https://github.com/ayush-jadaun/MarlOS/blob/main/docs/PATH_SETUP_QUICK_REFERENCE.md")
    print("\n" + "="*70 + "\n")


def print_pipx_recommendation():
    """Recommend pipx for easier installation"""
    print("💡 TIP: Avoid PATH issues in the future!")
    print("\nUse pipx (it handles PATH automatically):")
    print("  pip install pipx")
    print("  pipx ensurepath")
    print("  pipx install marlos")
    print()


def main():
    """Main post-install check"""
    print_banner()

    scripts_dir = get_scripts_dir()

    # Check if marl command is accessible
    if check_marl_command():
        print_success()
    else:
        # Check if Scripts directory is in PATH
        if is_in_path(scripts_dir):
            print("⚠️  Strange: Scripts directory is in PATH but 'marl' not found.")
            print("   Try closing and reopening your terminal.\n")
        else:
            print_path_warning(scripts_dir)
            print_pipx_recommendation()


if __name__ == "__main__":
    main()
