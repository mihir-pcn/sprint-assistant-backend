#!/bin/bash
# Render Build Script
# This file contains the build command that Render will use

set -e  # Exit on error

echo "=== Python Version Information ==="
echo "Current Python version:"
python --version || echo "python command not available"
python3 --version || echo "python3 command not available"

echo ""
echo "Available Python versions:"
ls /usr/bin/python* 2>/dev/null || echo "No Python binaries found in /usr/bin"

echo ""
echo "Checking for Python 3.12:"
if command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 found"
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    echo "⚠️  Using Python 3 (version: $PYTHON_VERSION)"
    PYTHON_CMD="python3"
else
    echo "❌ No suitable Python found"
    exit 1
fi

echo ""
echo "=== Installing Dependencies ==="
echo "Using Python command: $PYTHON_CMD"
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt

echo ""
echo "=== Verifying Installation ==="
$PYTHON_CMD -c "
import sys
print(f'Python version: {sys.version}')
print('Testing imports...')
try:
    import fastapi, uvicorn, langgraph, langchain_core, openai
    print('✅ All critical packages imported successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo "✅ Build completed successfully"
