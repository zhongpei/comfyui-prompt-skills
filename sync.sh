#!/bin/bash
# Sync ComfyUI Prompt Skills Plugin Package to Remote Server
# 
# This script syncs ONLY the packaged deployment files:
# - install.sh (installer script)
# - *.whl (Python wheel package)
# - js/ (compiled Vue frontend)
# - skills/ (skill definitions)
# - data/ (style library)
#
# Usage: ./sync.sh
#
# Prerequisites:
#   cd custom_nodes/comfyui-prompt-skills && make dist
#
# After sync, SSH to remote and run:
#   cd /opt2/ComfyUI-test/custom_nodes/comfyui-prompt-skills
#   ./install.sh /opt2/ComfyUI-test

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="${SCRIPT_DIR}/custom_nodes/comfyui-prompt-skills"
REMOTE_USER="fofo"
REMOTE_HOST="192.168.2.60"
REMOTE_PATH="/opt2/ComfyUI-test/custom_nodes/comfyui-prompt-skills/"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}  ComfyUI Prompt Skills - Sync${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# Check if dist/deploy exists (run make dist first)
if [ ! -d "${PLUGIN_DIR}/dist/deploy" ]; then
    echo -e "${RED}Error: Distribution package not found.${NC}"
    echo "Run 'cd custom_nodes/comfyui-prompt-skills && make dist' first."
    exit 1
fi

echo -e "${YELLOW}Source: ${PLUGIN_DIR}/dist/deploy/${NC}"
echo -e "${YELLOW}Target: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}${NC}"
echo ""

# Sync only the packaged files
echo -e "${YELLOW}Syncing packaged files...${NC}"
rsync -avz --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    "${PLUGIN_DIR}/dist/deploy/" \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

echo ""
echo -e "${GREEN}✓ Sync completed successfully!${NC}"
echo ""
echo -e "Remote path: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. SSH to remote: ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo "  2. Run install:   cd ${REMOTE_PATH} && ./install.sh /opt2/ComfyUI-test"
echo "  3. Restart ComfyUI"
