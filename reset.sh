#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}   Agent Pipeline Reset Script     ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Directory Paths
AGENT_DIR="$(pwd)/agent"
STEPS_DIR="$AGENT_DIR/steps"
STATUS_FILE="$AGENT_DIR/status.json"

# Check if we're in the correct directory
if [ ! -d "$AGENT_DIR" ]; then
    echo -e "${RED}Error: agent directory not found.${NC}"
    echo -e "${YELLOW}Please run this script from the root of the agent-pipeline-visualizer project.${NC}"
    exit 1
fi

# Function to confirm with the user
confirm() {
    read -p "This will delete all output files and reset the pipeline. Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled by user.${NC}"
        exit 0
    fi
}

# Ask for confirmation
confirm

# Reset the status file
echo -e "${YELLOW}Resetting agent status...${NC}"
echo "{}" > "$STATUS_FILE"
echo -e "${GREEN}Agent status reset.${NC}"

# List all step directories
echo -e "${YELLOW}Cleaning up step output directories...${NC}"
STEP_DIRS=(
    "data_analysis"
    "evaluation_generation"
    "create_contribution_goal"
    "create_development_item"
    "update_contribution_goal"
    "update_development_item"
    "timely_feedback"
    "coaching"
)

# Clean up step output directories
for step in "${STEP_DIRS[@]}"; do
    STEP_OUT_DIR="$STEPS_DIR/$step/out"
    
    if [ -d "$STEP_OUT_DIR" ]; then
        echo -e "Cleaning $step output directory..."
        # Remove all files but keep the directory
        rm -f "$STEP_OUT_DIR"/*
        
        # Also ensure the input directory exists
        mkdir -p "$STEPS_DIR/$step/in"
    else
        echo -e "${YELLOW}Warning: Output directory for $step not found. Creating it...${NC}"
        mkdir -p "$STEP_OUT_DIR"
        mkdir -p "$STEPS_DIR/$step/in"
    fi
done

echo -e "${GREEN}All step output directories have been cleaned.${NC}"

# Reset the backend status if the API is running
echo -e "${YELLOW}Attempting to reset status via API...${NC}"
if command -v curl &> /dev/null; then
    API_URL="http://localhost:4000"
    STATUS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/status" 2>/dev/null)
    
    if [ "$STATUS_RESPONSE" == "200" ]; then
        echo -e "${YELLOW}API is available. Sending reset request...${NC}"
        RESET_RESPONSE=$(curl -s -X POST "$API_URL/api/reset" 2>/dev/null)
        echo -e "${GREEN}API reset request sent.${NC}"
    else
        echo -e "${YELLOW}API not available. If the backend is running, you may need to restart it.${NC}"
    fi
else
    echo -e "${YELLOW}curl not found. Skipping API reset.${NC}"
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}Pipeline reset complete!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}You can now start the agent pipeline from the beginning.${NC}"
echo -e "${YELLOW}To run the agent in step-by-step mode:${NC}"
echo -e "  ${YELLOW}./run.sh agent-run step${NC}"
