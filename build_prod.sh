#!/bin/bash

# Production build & deployment script
# This script builds the Next.js app and sets up a proper production environment

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}   Production Build Script   ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Directory Paths
FRONTEND_DIR="$(pwd)/frontend"
BACKEND_DIR="$(pwd)/backend"

# Build frontend
echo -e "${YELLOW}Building Next.js frontend for production...${NC}"
cd "$FRONTEND_DIR"
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend build successful${NC}"
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi

# Create production ready backend
echo -e "${YELLOW}Preparing Flask backend for production...${NC}"
cd "$BACKEND_DIR"

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install or upgrade dependencies
pip install --upgrade -r requirements.txt

# Install gunicorn for production server
pip install gunicorn

# Add gunicorn to requirements.txt if not already there
if ! grep -q "gunicorn" requirements.txt; then
    echo "gunicorn" >> requirements.txt
fi

echo -e "${GREEN}✓ Backend preparation successful${NC}"

# Create startup scripts
echo -e "${YELLOW}Creating production startup scripts...${NC}"

# Create a startup script for the Next.js app
cat > "$(pwd)/../start_frontend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
npm run start
EOF
chmod +x "$(pwd)/../start_frontend.sh"

# Create a startup script for the Flask app with gunicorn
cat > "$(pwd)/../start_backend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
gunicorn --bind 0.0.0.0:4000 app:app
EOF
chmod +x "$(pwd)/../start_backend.sh"

echo -e "${GREEN}✓ Startup scripts created${NC}"

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}   BUILD COMPLETE   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "You can now run the production versions:"
echo -e "  ${YELLOW}./start_frontend.sh${NC} - Start the Next.js frontend"
echo -e "  ${YELLOW}./start_backend.sh${NC}  - Start the Flask backend with gunicorn"
echo -e ""
echo -e "For production deployment, consider using process managers like PM2 or supervisord"
