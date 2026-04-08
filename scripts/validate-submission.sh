#!/usr/bin/env bash
#
# validate-submission.sh — OpenEnv Submission Validator
#
# Checks that your HF Space is live, Docker image builds, and openenv validate passes.
#
# Run:
#   ./scripts/validate-submission.sh <ping_url> [repo_dir]
#
# Arguments:
#   ping_url   Your HuggingFace Space URL (e.g. https://your-space.hf.space)
#   repo_dir   Path to your repo (default: current directory)

set -uo pipefail

DOCKER_BUILD_TIMEOUT=600
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BOLD='\033[1m'
  NC='\033[0m'
else   
  RED=''
  GREEN=''
  YELLOW=''
  BOLD=''
  NC=''
fi

echo -e "${BOLD}Running OpenEnv Submission Validator${NC}"

if [ $# -lt 1 ]; then
  echo -e "${RED}Error: Not enough arguments.${NC}"
  echo "Usage: $0 <ping_url> [repo_dir]"
  exit 1
fi

PING_URL="$1"
REPO_DIR="${2:-.}"

cd "$REPO_DIR" || { echo -e "${RED}Failed to enter directory: $REPO_DIR${NC}"; exit 1; }

echo -e "\n${BOLD}[1/4] Pinging HF Space URL...${NC}"
echo "Checking URL: $PING_URL"

HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" "$PING_URL/health")
if [ "$HTTP_STATUS" -ne 200 ] && [ "$HTTP_STATUS" -ne 201 ]; then
  # Try base url if health doesn't exist
  HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" "$PING_URL")
  if [ "$HTTP_STATUS" -ne 200 ] && [ "$HTTP_STATUS" -ne 201 ] && [ "$HTTP_STATUS" -ne 405 ]; then
    echo -e "${RED}FAIL: Space is not returning HTTP 200. Got: $HTTP_STATUS${NC}"
    exit 1
  fi
fi
echo -e "${GREEN}PASS: HF Space is reachable.${NC}"

echo -e "\n${BOLD}[2/4] Validating openenv.yaml...${NC}"
# Depending on where openenv.yaml is (backend or root)
YAML_PATH="openenv.yaml"
if [ ! -f "$YAML_PATH" ]; then
    if [ -f "backend/openenv.yaml" ]; then
        YAML_PATH="backend/openenv.yaml"
    else
        echo -e "${RED}FAIL: Could not find openenv.yaml or backend/openenv.yaml${NC}"
        exit 1
    fi
fi

if command -v openenv &> /dev/null; then
    openenv validate "$YAML_PATH"
    if [ $? -ne 0 ]; then
        echo -e "${RED}FAIL: openenv.yaml validation failed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}PASS: openenv.yaml is valid.${NC}"
else
    echo -e "${YELLOW}WARN: openenv CLI not found. Skipping strict validation.${NC}"
fi

echo -e "\n${BOLD}[3/4] Testing Docker build...${NC}"
if command -v docker &> /dev/null; then
    # timeout avoids it hanging forever
    DOCKER_IMAGE="openenv-sub-$(date +%s)"
    timeout $DOCKER_BUILD_TIMEOUT docker build -t "$DOCKER_IMAGE" .
    if [ $? -ne 0 ]; then
        echo -e "${RED}FAIL: Docker build failed or timed out.${NC}"
        exit 1
    fi
    echo -e "${GREEN}PASS: Docker build succeeded.${NC}"
else
    echo -e "${YELLOW}WARN: Docker not found. Skipping build step.${NC}"
fi

echo -e "\n${BOLD}[4/4] Ensuring inference script runs...${NC}"
if [ ! -f "inference.py" ]; then
    echo -e "${RED}FAIL: inference.py not found in root directory.${NC}"
    exit 1
fi

echo "Running inference.py to ensure it produces scores..."
# Run a dry test. We set ENV_BASE_URL to the ping_url so it tests against the actual space.
export ENV_BASE_URL=$PING_URL
export MODEL_NAME="gpt-4o-mini" # default to a fast model

# Check if python is available
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

if $PYTHON_CMD inference.py > inference.log 2>&1; then
    echo -e "${GREEN}PASS: inference script executed.${NC}"
    
    # Simple check on output to ensure correct formatting
    if grep -q "\[START\]" inference.log && grep -q "\[END\]" inference.log; then
        echo -e "${GREEN}PASS: Script output follows expected stdout format.${NC}"
    else
        echo -e "${YELLOW}WARN: Could not verify [START] or [END] formats in inference log.${NC}"
    fi
else
    echo -e "${RED}FAIL: inference.py exited with error!${NC}"
    cat inference.log
    exit 1
fi

echo -e "\n${BOLD}${GREEN}Validation Complete. Setup looks good for submission!${NC}"
exit 0
