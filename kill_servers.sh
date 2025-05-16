#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Killing processes on ports 3000 and 4000...${NC}"

# Kill processes on port 3000 (frontend)
echo -e "${YELLOW}Checking for processes on port 3000...${NC}"
PIDS_3000=$(lsof -ti :3000 2>/dev/null)
if [ -n "$PIDS_3000" ]; then
  echo -e "${YELLOW}Found processes on port 3000. Killing them...${NC}"
  echo "$PIDS_3000" | xargs kill -9 2>/dev/null
  echo -e "${GREEN}Port 3000 cleared.${NC}"
else
  echo -e "${GREEN}No processes found on port 3000.${NC}"
fi

# Kill processes on port 4000 (backend)
echo -e "${YELLOW}Checking for processes on port 4000...${NC}"
PIDS_4000=$(lsof -ti :4000 2>/dev/null)
if [ -n "$PIDS_4000" ]; then
  echo -e "${YELLOW}Found processes on port 4000. Killing them...${NC}"
  echo "$PIDS_4000" | xargs kill -9 2>/dev/null
  echo -e "${GREEN}Port 4000 cleared.${NC}"
else
  echo -e "${GREEN}No processes found on port 4000.${NC}"
fi

echo -e "${GREEN}Done. Ports 3000 and 4000 should now be available.${NC}"
