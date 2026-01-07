#!/bin/bash
# Install Script for ComfyUI Prompt Skills Plugin
# This script installs the pre-built plugin to a ComfyUI instance
#
# Usage: ./install.sh [comfyui_path]
#   comfyui_path: Path to ComfyUI installation (default: /opt2/ComfyUI)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_NAME="comfyui-prompt-skills"
DEFAULT_COMFYUI_PATH="/opt2/ComfyUI"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
COMFYUI_PATH="${1:-$DEFAULT_COMFYUI_PATH}"
TARGET_DIR="${COMFYUI_PATH}/custom_nodes/${PLUGIN_NAME}"

echo -e "${YELLOW}Installing ComfyUI Prompt Skills Plugin...${NC}"
echo "  Source: ${SCRIPT_DIR}"
echo "  Target: ${TARGET_DIR}"
echo ""

# Check if ComfyUI exists
if [ ! -d "${COMFYUI_PATH}" ]; then
    echo -e "${RED}Error: ComfyUI not found at ${COMFYUI_PATH}${NC}"
    echo "Usage: ./install.sh [comfyui_path]"
    exit 1
fi

# Create target directory
mkdir -p "${TARGET_DIR}"

# Check for wheel package (in current dir or dist/ subdirectory)
WHEEL_FILE=$(ls "${SCRIPT_DIR}"/*.whl 2>/dev/null | head -n1 || echo "")
if [ -z "${WHEEL_FILE}" ]; then
    WHEEL_FILE=$(ls "${SCRIPT_DIR}"/dist/*.whl 2>/dev/null | head -n1 || echo "")
fi
if [ -z "${WHEEL_FILE}" ]; then
    echo -e "${RED}Error: No wheel package found${NC}"
    echo "Run 'make package' first to build the wheel."
    exit 1
fi

# 1. Install Python package via pip
echo -e "${YELLOW}[1/4] Installing Python package...${NC}"
echo "  Wheel: ${WHEEL_FILE}"
echo "  Python: $(which python3)"
python3 -m pip install --force-reinstall "${WHEEL_FILE}"
echo -e "${GREEN}  ✓ Python package installed${NC}"

# 2. Copy JavaScript files (frontend)
echo -e "${YELLOW}[2/4] Installing JavaScript frontend...${NC}"
if [ -d "${SCRIPT_DIR}/js" ] && [ -n "$(ls -A "${SCRIPT_DIR}/js" 2>/dev/null)" ]; then
    mkdir -p "${TARGET_DIR}/js"
    cp -r "${SCRIPT_DIR}/js/"* "${TARGET_DIR}/js/"
    echo -e "${GREEN}  ✓ JavaScript files copied${NC}"
else
    echo -e "${YELLOW}  ⚠ No JavaScript files found${NC}"
fi

# 3. Copy skills directory
echo -e "${YELLOW}[3/4] Installing skills...${NC}"
if [ -d "${SCRIPT_DIR}/skills" ]; then
    mkdir -p "${TARGET_DIR}/skills"
    cp -r "${SCRIPT_DIR}/skills/"* "${TARGET_DIR}/skills/"
    echo -e "${GREEN}  ✓ Skills installed${NC}"
else
    echo -e "${YELLOW}  ⚠ No skills directory found${NC}"
fi

# 4. Copy data directory
echo -e "${YELLOW}[4/4] Installing data files...${NC}"
if [ -d "${SCRIPT_DIR}/data" ]; then
    mkdir -p "${TARGET_DIR}/data"
    cp -r "${SCRIPT_DIR}/data/"* "${TARGET_DIR}/data/"
    echo -e "${GREEN}  ✓ Data files installed${NC}"
else
    echo -e "${YELLOW}  ⚠ No data directory found${NC}"
fi

# Create __init__.py entry point that imports from installed package
echo -e "${YELLOW}Creating entry point...${NC}"
cat > "${TARGET_DIR}/__init__.py" << 'EOF'
"""
ComfyUI Prompt Skills Plugin - Entry Point

This file loads the plugin from the installed pip package.
"""
try:
    from comfyui_prompt_skills import (
        NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS,
        WEB_DIRECTORY,
    )
except ImportError as e:
    import logging
    logging.warning(f"Failed to import comfyui_prompt_skills: {e}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
    WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
EOF
echo -e "${GREEN}  ✓ Entry point created${NC}"

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Plugin installed to: ${TARGET_DIR}"
echo "Restart ComfyUI to load the plugin."
