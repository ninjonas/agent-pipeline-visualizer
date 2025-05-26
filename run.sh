#!/bin/bash

# Function to kill processes on specific ports
kill_port() {
  PORT=$1
  echo "Checking for process on port $PORT..."
  
  # For macOS (lsof)
  if command -v lsof &> /dev/null; then
    PID=$(lsof -i :$PORT -t 2>/dev/null)
    if [ -n "$PID" ]; then
      echo "Killing process $PID on port $PORT"
      kill -9 $PID 2>/dev/null || true
      sleep 1  # Give the OS time to release the port
      # Double-check port is actually free
      REMAINING=$(lsof -i :$PORT -t 2>/dev/null)
      if [ -n "$REMAINING" ]; then
        echo "Warning: Port $PORT still has active processes. Trying again..."
        kill -9 $REMAINING 2>/dev/null || true
      fi
    else
      echo "No process found running on port $PORT"
    fi
  # For Linux (netstat)
  elif command -v netstat &> /dev/null; then
    PID=$(netstat -nlp 2>/dev/null | grep ":$PORT" | awk '{print $7}' | cut -d'/' -f1)
    if [ -n "$PID" ]; then
      echo "Killing process $PID on port $PORT"
      kill -9 $PID 2>/dev/null || true
    else
      echo "No process found running on port $PORT"
    fi
  else
    echo "Neither lsof nor netstat found. Cannot check for processes on ports."
  fi
}

# Function to kill port processes if needed
kill_ports() {
  echo -e "${YELLOW}Ensuring ports 3000 and 4000 are available...${NC}"
  kill_port 3000
  kill_port 4000
  
  # Double-check ports are actually free
  sleep 1
  echo -e "${GREEN}Ports are now available for use.${NC}"
}

# Build script - Configure terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}   Agent Pipeline Visualizer Script     ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Directory Paths
FRONTEND_DIR="$(pwd)/frontend"
BACKEND_DIR="$(pwd)/backend"
AGENT_DIR="$(pwd)/agent"

# Function to run frontend
run_frontend() {
  local websocket_mode=${1:-"no"}
  
  echo -e "${YELLOW}Setting up Next.js frontend...${NC}"
  cd "$FRONTEND_DIR"
  
  # Install all dependencies
  echo -e "${YELLOW}Installing frontend dependencies...${NC}"
  npm install
  echo -e "${GREEN}Frontend dependencies installed${NC}"
  
  # Install socket.io-client if in websocket mode
  if [ "$websocket_mode" == "websocket" ]; then
    # Check if socket.io-client is already installed
    if ! grep -q '"socket.io-client"' package.json; then
      echo -e "${YELLOW}Installing socket.io-client...${NC}"
      npm install --silent socket.io-client
      echo -e "${GREEN}WebSocket client dependencies installed${NC}"
    else
      echo -e "${GREEN}socket.io-client already installed${NC}"
    fi
  fi
  
  echo -e "${YELLOW}Starting Next.js frontend...${NC}"
  # Use npx to ensure next is available
  npx next dev -p 3000 &
  FRONTEND_PID=$!
  echo -e "${GREEN}Frontend started at http://localhost:3000${NC}"
}

# Function to run backend
run_backend() {
  local websocket_mode=${1:-"no"}
  
  echo -e "${YELLOW}Setting up Flask backend...${NC}"
  cd "$BACKEND_DIR"
  
  # Check if virtual environment exists, if not create it
  if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment for backend...${NC}"
    python -m venv venv
  fi
  
  source venv/bin/activate
  
  # Install all dependencies
  echo -e "${YELLOW}Installing backend dependencies...${NC}"
  pip install -r requirements.txt
  echo -e "${GREEN}Backend dependencies installed${NC}"
  
  # Install WebSocket dependencies if in websocket mode
  if [ "$websocket_mode" == "websocket" ]; then
    echo -e "${YELLOW}Installing WebSocket dependencies...${NC}"
    pip install flask-socketio python-socketio python-engineio
    echo -e "${GREEN}WebSocket dependencies installed${NC}"
  fi
  
  echo -e "${YELLOW}Starting Flask backend...${NC}"
  # Use -u for unbuffered output to prevent issues with SIGINT handling
  PYTHONUNBUFFERED=1 exec python app.py &
  BACKEND_PID=$!
  
  if [ "$websocket_mode" == "websocket" ]; then
    echo -e "${GREEN}Backend started with WebSocket support at http://localhost:4000${NC}"
  else
    echo -e "${GREEN}Backend started at http://localhost:4000${NC}"
  fi
}

# Function to setup agent environment
setup_agent() {
  echo -e "${YELLOW}Setting up agent environment...${NC}"
  
  # Check if agent virtual environment exists
  if [ ! -d "$AGENT_DIR/venv" ]; then
    echo -e "${BLUE}Creating virtual environment for agent...${NC}"
    cd "$AGENT_DIR"
    python -m venv venv
  fi
  
  cd "$AGENT_DIR"
  source venv/bin/activate
  echo -e "${YELLOW}Installing agent dependencies...${NC}"
  pip install -r requirements.txt
  echo -e "${GREEN}Agent dependencies installed${NC}"
  deactivate
  
  echo -e "${GREEN}Agent environment ready.${NC}"
}

# Function to run agent
run_agent() {
  local mode=$1
  local step=$2
  local api_url="http://localhost:4000"
  
  setup_agent
  
  # Check if the backend is running
  if ! curl -s "$api_url/api/status" > /dev/null; then
    echo -e "${RED}Warning: Backend API is not accessible at $api_url${NC}"
    echo -e "${YELLOW}The agent will run in offline mode and won't connect to the visualizer.${NC}"
    echo -e "${BLUE}Consider running './run.sh dev' in another terminal first.${NC}"
    sleep 2
  else
    echo -e "${GREEN}Backend API is available. Agent will connect to the visualizer.${NC}"
  fi
  
  echo -e "${YELLOW}Running agent in $mode mode...${NC}"
  cd "$AGENT_DIR"
  source venv/bin/activate
  
  if [ "$mode" == "step" ] && [ -n "$step" ]; then
    python client.py --mode step --step "$step" --api-url "$api_url"
  elif [ "$mode" == "step" ]; then
    python client.py --mode step --api-url "$api_url"
  else
    python client.py --mode full --api-url "$api_url"
  fi
}

# Function to build frontend
build_frontend() {
  echo -e "${YELLOW}Building Next.js frontend...${NC}"
  cd "$FRONTEND_DIR"
  npm run build
  echo -e "${GREEN}Frontend build completed${NC}"
}

# Check for the command argument
if [ "$1" == "dev" ]; then
  # Development mode - run both servers with WebSocket support by default
  kill_ports
  run_frontend "websocket"
  run_backend "websocket"
  
  echo -e "${GREEN}Both servers are running with WebSocket support. Press Ctrl+C to stop both.${NC}"
  echo -e "${BLUE}Access the agent dashboard at http://localhost:3000/agent${NC}"
  echo -e "${GREEN}WebSocket enabled: No UI flickering during step execution${NC}"
  echo -e "${YELLOW}To run the agent demo in another terminal:${NC}"
  echo -e "  ${YELLOW}./run.sh agent-run step${NC}"
  
  # Trap to catch Ctrl+C and kill both processes
  trap 'echo -e "${YELLOW}Gracefully shutting down servers...${NC}"; kill -TERM $FRONTEND_PID $BACKEND_PID 2>/dev/null; sleep 1; if ps -p $BACKEND_PID > /dev/null; then kill -9 $BACKEND_PID 2>/dev/null; fi; if ps -p $FRONTEND_PID > /dev/null; then kill -9 $FRONTEND_PID 2>/dev/null; fi; echo -e "${RED}Servers stopped.${NC}"; exit 0' INT TERM
  # Wait for both processes to finish
  wait
  
elif [ "$1" == "build" ]; then
  # Build mode - build frontend
  build_frontend
  
elif [ "$1" == "agent" ]; then
  # Setup agent environment
  setup_agent
  
  echo -e "${BLUE}To run the agent in step-by-step mode:${NC}"
  echo -e "${YELLOW}./run.sh agent-run step${NC}"
  echo -e "${BLUE}To run the full agent pipeline:${NC}"
  echo -e "${YELLOW}./run.sh agent-run full${NC}"
  
elif [ "$1" == "agent-run" ]; then
  # Run agent with specified mode
  mode=${2:-"step"}  # Default to step mode if not specified
  step=$3
  
  # Check if the backend is running
  BACKEND_RUNNING=false
  if curl -s "http://localhost:4000/api/status" > /dev/null; then
    BACKEND_RUNNING=true
  fi
  
  # If the backend is not running and mode is 'step', start dev mode first
  if [ "$mode" == "step" ] && [ "$BACKEND_RUNNING" = false ]; then
    echo -e "${YELLOW}Backend not detected. Starting servers in dev mode first...${NC}"
    # Start the dev servers in the background
    $0 dev &
    DEV_PID=$!
    
    # Wait for servers to be ready
    echo -e "${YELLOW}Waiting for servers to start...${NC}"
    while ! curl -s "http://localhost:4000/api/status" > /dev/null; do
      sleep 1
    done
    echo -e "${GREEN}Servers are now running.${NC}"
    sleep 2  # Give a moment for everything to initialize
  elif [ "$BACKEND_RUNNING" = false ]; then
    # For non-step modes, just make sure the port is free
    kill_port 4000
  fi
  
  run_agent "$mode" "$step"
  
elif [ "$1" == "full" ]; then
  # Run everything - frontend, backend, and agent
  kill_ports
  run_frontend
  run_backend
  
  echo -e "${GREEN}Servers are running. Setting up agent...${NC}"
  setup_agent
  
  echo -e "${BLUE}==================================${NC}"
  echo -e "${GREEN}All components are ready!${NC}"
  echo -e "${BLUE}==================================${NC}"
  echo -e "Frontend: ${GREEN}http://localhost:3000${NC}"
  echo -e "Backend API: ${GREEN}http://localhost:4000${NC}"
  echo -e "Agent Dashboard: ${GREEN}http://localhost:3000/agent${NC}"
  echo -e "${BLUE}==================================${NC}"
  echo -e "${YELLOW}To run the agent:${NC}"
  echo -e "  ${YELLOW}./run.sh agent-run step${NC} (in a new terminal)"
  
  # Trap to catch Ctrl+C and kill both processes
  trap 'echo -e "${YELLOW}Gracefully shutting down servers...${NC}"; kill -TERM $FRONTEND_PID $BACKEND_PID 2>/dev/null; sleep 1; if ps -p $BACKEND_PID > /dev/null; then kill -9 $BACKEND_PID 2>/dev/null; fi; if ps -p $FRONTEND_PID > /dev/null; then kill -9 $FRONTEND_PID 2>/dev/null; fi; echo -e "${RED}Servers stopped.${NC}"; exit 0' INT TERM
  # Wait for both processes to finish
  wait
  
elif [ "$1" == "kill" ]; then
  # Just kill processes on ports 3000 and 4000
  echo -e "${BLUE}=========================================${NC}"
  echo -e "${YELLOW}Killing processes on ports 3000 and 4000...${NC}"
  echo -e "${BLUE}=========================================${NC}"
  kill_ports
  echo -e "${GREEN}Done!${NC}"

elif [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  # Show help information
  echo -e "${BLUE}=========================================${NC}"
  echo -e "${GREEN}       Agent Pipeline Visualizer        ${NC}"
  echo -e "${BLUE}=========================================${NC}"
  echo -e "${YELLOW}Available commands:${NC}\n"
  
  echo -e "${GREEN}Server Management:${NC}"
  echo -e "  ${YELLOW}./run.sh dev${NC}         - Run frontend and backend in development mode with WebSocket support"
  echo -e "  ${YELLOW}./run.sh full${NC}        - Run frontend, backend and setup agent"
  echo -e "  ${YELLOW}./run.sh build${NC}       - Build the frontend for production"
  echo -e "  ${YELLOW}./run.sh kill${NC}        - Kill any processes running on ports 3000 and 4000"
  
  echo -e "\n${GREEN}Agent Commands:${NC}"
  echo -e "  ${YELLOW}./run.sh agent${NC}       - Setup the agent environment"
  echo -e "  ${YELLOW}./run.sh agent-run${NC}   - Run agent in interactive step-by-step mode"
  echo -e "  ${YELLOW}./run.sh agent-run full${NC} - Run the complete agent pipeline"
  echo -e "  ${YELLOW}./run.sh agent-run step data_collection${NC} - Run a specific agent step"
  echo -e "  ${YELLOW}./reset.sh${NC}           - Reset all agent steps and clear outputs"
  
  echo -e "\n${GREEN}Example Workflow:${NC}"
  echo -e "  1. Start the servers:    ${YELLOW}./run.sh dev${NC}"
  echo -e "  2. Open in browser:      ${BLUE}http://localhost:3000/agent${NC}"
  echo -e "  3. In a new terminal:    ${YELLOW}./run.sh agent-run step${NC}"
  
  echo -e "\n${BLUE}For more details, see the README.md and agent/README.md files${NC}"
else
  # Show usage if no valid argument is provided
  echo -e "${RED}Unknown command: $1${NC}"
  echo -e "Run ${YELLOW}./run.sh help${NC} for usage information"
  exit 1
fi
