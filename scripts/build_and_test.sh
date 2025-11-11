#!/bin/bash
# Quick Build and Test Script for Linux/Mac

set -e

echo ""
echo "========================================"
echo "  MarlOS - Build and Test"
echo "========================================"
echo ""

# Check if in correct directory
if [ ! -f "setup.py" ]; then
    echo "[ERROR] Run this script from the MarlOS root directory"
    exit 1
fi

echo "[1] Building package..."
echo ""

# Install build tools if needed
pip install --quiet build twine

# Clean old builds
rm -rf dist build *.egg-info

# Build package
python -m build

echo ""
echo "[SUCCESS] Package built!"
echo ""
echo "Built files:"
ls -1 dist/
echo ""

echo "========================================"
echo "  Testing Installation"
echo "========================================"
echo ""

# Test installation
echo "[2] Testing local install..."
pip uninstall -y marlos || true
pip install dist/marlos-1.0.4-py3-none-any.whl

echo ""
echo "[3] Verifying command..."
marl --version

echo ""
echo "========================================"
echo "  SUCCESS!"
echo "========================================"
echo ""
echo "Package built and tested successfully!"
echo ""
echo "Wheel file: dist/marlos-1.0.4-py3-none-any.whl"
echo ""
echo "Next steps:"
echo "  1. Test locally: marl --help"
echo "  2. Share wheel file with testers"
echo "  3. Or push to GitHub: git push origin main"
echo "  4. Testers install: pip install git+https://github.com/ayush-jadaun/MarlOS.git"
echo ""
