#!/usr/bin/env python3
"""
MarlOS Publish Script
Auto-bumps version, builds, and publishes to PyPI.

Usage:
    python scripts/publish.py patch     # 1.1.0 -> 1.1.1
    python scripts/publish.py minor     # 1.1.0 -> 1.2.0
    python scripts/publish.py major     # 1.1.0 -> 2.0.0
    python scripts/publish.py --dry-run # Build but don't upload
    python scripts/publish.py --test    # Upload to TestPyPI instead

Setup (one-time):
    1. Create PyPI account: https://pypi.org/account/register/
    2. Create API token: https://pypi.org/manage/account/token/
    3. Save token:
       - Option A: Set env var TWINE_PASSWORD=pypi-xxxxx
       - Option B: Create ~/.pypirc:
           [pypi]
           username = __token__
           password = pypi-xxxxx

    For TestPyPI (recommended first):
    1. Create account: https://test.pypi.org/account/register/
    2. Create token: https://test.pypi.org/manage/account/token/
    3. Set env var TEST_PYPI_TOKEN=pypi-xxxxx
"""

import os
import re
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Files that contain the version string
VERSION_FILES = [
    ("pyproject.toml", r'version = "(\d+\.\d+\.\d+)"', 'version = "{}"'),
    ("setup.py", r"version='(\d+\.\d+\.\d+)'", "version='{}'"),
    ("cli/main.py", r"version=\"(\d+\.\d+\.\d+)\"", 'version="{}"'),
    ("cli/marlOS.py", r"version=\"(\d+\.\d+\.\d+)\"", 'version="{}"'),
]


def get_current_version():
    """Read current version from pyproject.toml."""
    toml = (PROJECT_ROOT / "pyproject.toml").read_text()
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', toml)
    if not match:
        print("ERROR: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def bump_version(current: str, bump_type: str) -> str:
    """Bump version string."""
    major, minor, patch = map(int, current.split("."))
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        print(f"ERROR: Unknown bump type: {bump_type}")
        sys.exit(1)


def update_version_in_files(old_version: str, new_version: str):
    """Update version in all files."""
    for filename, pattern, template in VERSION_FILES:
        filepath = PROJECT_ROOT / filename
        if not filepath.exists():
            print(f"  SKIP {filename} (not found)")
            continue

        content = filepath.read_text(encoding="utf-8")
        new_content = re.sub(pattern, template.format(new_version), content)

        if content != new_content:
            filepath.write_text(new_content, encoding="utf-8")
            print(f"  OK   {filename}: {old_version} -> {new_version}")
        else:
            print(f"  SKIP {filename} (no match)")


def run(cmd, **kwargs):
    """Run a command, exit on failure."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), **kwargs)
    if result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        sys.exit(1)
    return result


def build():
    """Build sdist and wheel."""
    dist_dir = PROJECT_ROOT / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    run([sys.executable, "-m", "build"])

    # Verify build artifacts
    wheels = list(dist_dir.glob("*.whl"))
    tarballs = list(dist_dir.glob("*.tar.gz"))
    if not wheels or not tarballs:
        print("ERROR: Build produced no artifacts")
        sys.exit(1)

    for f in wheels + tarballs:
        size_kb = f.stat().st_size / 1024
        print(f"  Built: {f.name} ({size_kb:.0f} KB)")


def upload(test=False):
    """Upload to PyPI or TestPyPI."""
    cmd = [sys.executable, "-m", "twine", "upload"]

    if test:
        token = os.environ.get("TEST_PYPI_TOKEN")
        cmd += ["--repository-url", "https://test.pypi.org/legacy/"]
        if token:
            cmd += ["-u", "__token__", "-p", token]
        print("  Uploading to TestPyPI...")
    else:
        token = os.environ.get("TWINE_PASSWORD")
        if token:
            cmd += ["-u", "__token__", "-p", token]
        print("  Uploading to PyPI...")

    cmd.append("dist/*")
    run(cmd)


def git_tag(version: str):
    """Create and push a git tag."""
    tag = f"v{version}"
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"chore: bump version to {version}"])
    run(["git", "tag", "-a", tag, "-m", f"Release {version}"])
    print(f"  Tagged: {tag}")
    print(f"  Push with: git push origin ayush --tags")


def check_tools():
    """Verify required tools are installed."""
    missing = []
    for mod in ["build", "twine"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        sys.exit(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MarlOS Publish Script")
    parser.add_argument("bump", nargs="?", default="patch",
                        choices=["major", "minor", "patch"],
                        help="Version bump type (default: patch)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build but don't upload or tag")
    parser.add_argument("--test", action="store_true",
                        help="Upload to TestPyPI instead of PyPI")
    parser.add_argument("--no-tag", action="store_true",
                        help="Skip git tag")
    args = parser.parse_args()

    print("=" * 50)
    print("  MarlOS Publish Script")
    print("=" * 50)

    # Check tools
    print("\n[1/5] Checking tools...")
    check_tools()
    print("  OK")

    # Bump version
    current = get_current_version()
    new_version = bump_version(current, args.bump)
    print(f"\n[2/5] Bumping version: {current} -> {new_version}")
    update_version_in_files(current, new_version)

    # Run tests
    print(f"\n[3/5] Running tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test/", "--ignore=test/integration", "-x", "-q"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  TESTS FAILED:\n{result.stdout}\n{result.stderr}")
        print("  Fix tests before publishing.")
        sys.exit(1)
    # Extract pass count from last line
    last_line = result.stdout.strip().split("\n")[-1]
    print(f"  {last_line}")

    # Build
    print(f"\n[4/5] Building package...")
    build()

    if args.dry_run:
        print(f"\n[5/5] DRY RUN — skipping upload and tag")
        print(f"\n  Version bumped to {new_version}")
        print(f"  Artifacts in dist/")
        print(f"  Run without --dry-run to publish")
        return

    # Upload
    print(f"\n[5/5] Publishing...")
    upload(test=args.test)

    # Git tag
    if not args.no_tag:
        print(f"\n[+] Git tag...")
        git_tag(new_version)

    target = "TestPyPI" if args.test else "PyPI"
    print(f"\n{'=' * 50}")
    print(f"  Published MarlOS v{new_version} to {target}")
    print(f"{'=' * 50}")

    if args.test:
        print(f"\n  Install from TestPyPI:")
        print(f"  pip install -i https://test.pypi.org/simple/ marlos")
    else:
        print(f"\n  Install:")
        print(f"  pip install marlos=={new_version}")

    print(f"\n  Don't forget: git push origin ayush --tags")


if __name__ == "__main__":
    main()
