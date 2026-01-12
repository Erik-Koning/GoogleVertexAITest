#!/bin/bash
# Download pip packages locally for transfer to air-gapped cloud workstation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUNDLE_DIR="$PROJECT_ROOT/pip_bundle"
BUNDLE_ZIP="$PROJECT_ROOT/pip_bundle.zip"

echo "=== Bundling pip packages for cloud workstation ==="

# Clean previous bundle
rm -rf "$BUNDLE_DIR"
rm -f "$BUNDLE_ZIP"
mkdir -p "$BUNDLE_DIR"

# Download all packages (wheels preferred)
echo "Downloading packages..."
pip download -r "$PROJECT_ROOT/requirements.txt" -d "$BUNDLE_DIR" \
    --platform manylinux2014_x86_64 \
    --python-version 311 \
    --only-binary=:all: \
    2>/dev/null || true

# Fallback: download source packages for anything that failed
echo "Downloading any remaining source packages..."
pip download -r "$PROJECT_ROOT/requirements.txt" -d "$BUNDLE_DIR" \
    --no-binary=:none: 2>/dev/null || true

# Count packages
PACKAGE_COUNT=$(ls -1 "$BUNDLE_DIR" | wc -l | tr -d ' ')
echo "Downloaded $PACKAGE_COUNT packages"

# Create zip
echo "Creating zip bundle..."
cd "$PROJECT_ROOT"
zip -r "$BUNDLE_ZIP" pip_bundle/

# Cleanup directory (keep just the zip)
rm -rf "$BUNDLE_DIR"

ZIP_SIZE=$(du -h "$BUNDLE_ZIP" | cut -f1)
echo ""
echo "=== Bundle created ==="
echo "File: $BUNDLE_ZIP"
echo "Size: $ZIP_SIZE"
echo ""
echo "Transfer to workstation and run:"
echo "  unzip pip_bundle.zip"
echo "  pip install --no-index --find-links=pip_bundle -r requirements.txt"
