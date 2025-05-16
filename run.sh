#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Project directories
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="${BASE_DIR}/backend"
FRONTEND_DIR="${BASE_DIR}/frontend"

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to kill processes using specific ports
kill_port_processes() {
  local port=$1
  echo -e "${YELLOW}Checking for processes using port ${port}...${NC}"
  
  if command_exists lsof; then
    # Find PIDs of processes using the specified port
    local pids=$(lsof -ti :${port} 2>/dev/null)
    if [ -n "$pids" ]; then
      echo -e "${YELLOW}Found processes using port ${port}. Killing them...${NC}"
      # Kill the processes
      echo "$pids" | xargs kill -9 2>/dev/null
      sleep 1
      echo -e "${GREEN}Port ${port} cleared.${NC}"
    else
      echo -e "${GREEN}No processes found using port ${port}.${NC}"
    fi
  else
    echo -e "${RED}lsof command not found. Unable to check for port usage.${NC}"
  fi
}

# Check for required dependencies
check_dependencies() {
  echo -e "${BLUE}Checking dependencies...${NC}"
  
  # Check for Python
  if ! command_exists python3; then
    echo -e "${RED}Python 3 is not installed. Please install it and try again.${NC}"
    exit 1
  fi
  
  # Check for Node.js
  if ! command_exists node; then
    echo -e "${RED}Node.js is not installed. Please install it and try again.${NC}"
    exit 1
  fi
  
  # Check for npm
  if ! command_exists npm; then
    echo -e "${RED}npm is not installed. Please install it and try again.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}All dependencies are installed!${NC}"
}

# Setup Python virtual environment and install dependencies
setup_backend() {
  echo -e "${BLUE}Setting up backend...${NC}"
  cd "$BACKEND_DIR" || exit 1
  
  # Create virtual environment if it doesn't exist
  if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
  fi
  
  # Activate virtual environment and install dependencies
  echo -e "${YELLOW}Installing backend dependencies...${NC}"
  source venv/bin/activate
  pip install -r requirements.txt
  
  cd ..
  echo -e "${GREEN}Backend setup complete!${NC}"
}

# Install npm dependencies for the frontend
setup_frontend() {
  echo -e "${BLUE}Setting up frontend...${NC}"
  cd "$FRONTEND_DIR" || exit 1
  
  echo -e "${YELLOW}Installing frontend dependencies...${NC}"
  npm install
  
  cd ..
  echo -e "${GREEN}Frontend setup complete!${NC}"
}

# Build the frontend
build_frontend() {
  echo -e "${BLUE}Building frontend...${NC}"
  cd "$FRONTEND_DIR" || exit 1
  
  npm run build
  
  cd ..
  echo -e "${GREEN}Frontend build complete!${NC}"
}

# Start the backend server
start_backend() {
  echo -e "${BLUE}Starting backend server...${NC}"
  
  # Kill any processes using our port
  kill_port_processes 4000
  
  cd "$BACKEND_DIR" || exit 1
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Run in background and save PID
  python3 app.py &
  echo $! > ./backend.pid
  
  cd ..
  echo -e "${GREEN}Backend server started on http://localhost:4000${NC}"
}

# Start the frontend server
start_frontend() {
  echo -e "${BLUE}Starting frontend server...${NC}"
  
  # Kill any processes using our port
  kill_port_processes 3000
  
  cd "$FRONTEND_DIR" || exit 1
  
  # Run in background and save PID
  npm run start &
  echo $! > ./frontend.pid
  
  cd ..
  echo -e "${GREEN}Frontend server started on http://localhost:3000${NC}"
}

# Start both servers in development mode
start_dev() {
  echo -e "${BLUE}Starting development servers...${NC}"
  
  # Kill any processes using our ports
  kill_port_processes 4000
  kill_port_processes 3000
  
  cd "$BACKEND_DIR" || exit 1
  
  # Activate virtual environment and start Flask in dev mode
  source venv/bin/activate
  echo -e "${YELLOW}Starting Flask development server...${NC}"
  python3 app.py &
  BACKEND_PID=$!
  echo $BACKEND_PID > ./backend.pid
  
  cd ..
  
  cd "$FRONTEND_DIR" || exit 1
  echo -e "${YELLOW}Starting Next.js development server...${NC}"
  npm run dev &
  FRONTEND_PID=$!
  echo $FRONTEND_PID > ./frontend.pid
  
  cd ..
  
  echo -e "${GREEN}Development servers started:${NC}"
  echo -e "${GREEN}Backend: http://localhost:4000${NC}"
  echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
  echo -e "${YELLOW}Press Ctrl+C to stop both servers.${NC}"
  
  # Wait for user to press Ctrl+C and then cleanup
  trap cleanup INT
  
  # Monitor both processes and kill the other if one dies
  while true; do
    if ! ps -p "$BACKEND_PID" > /dev/null; then
      echo -e "${RED}Backend server crashed or stopped unexpectedly. Stopping all servers.${NC}"
      # Kill frontend process
      if ps -p "$FRONTEND_PID" > /dev/null; then
        kill "$FRONTEND_PID"
      fi
      # Clean up pid files
      [ -f "$BACKEND_DIR/backend.pid" ] && rm "$BACKEND_DIR/backend.pid"
      [ -f "$FRONTEND_DIR/frontend.pid" ] && rm "$FRONTEND_DIR/frontend.pid"
      echo -e "${RED}All servers have been stopped due to backend failure.${NC}"
      return 1
    fi
    
    if ! ps -p "$FRONTEND_PID" > /dev/null; then
      echo -e "${RED}Frontend server crashed or stopped unexpectedly. Stopping all servers.${NC}"
      # Kill backend process
      if ps -p "$BACKEND_PID" > /dev/null; then
        kill "$BACKEND_PID"
      fi
      # Clean up pid files
      [ -f "$BACKEND_DIR/backend.pid" ] && rm "$BACKEND_DIR/backend.pid"
      [ -f "$FRONTEND_DIR/frontend.pid" ] && rm "$FRONTEND_DIR/frontend.pid"
      echo -e "${RED}All servers have been stopped due to frontend failure.${NC}"
      return 1
    fi
    
    # Check every 2 seconds
    sleep 2
  done
}

# Stop all running servers
stop_servers() {
  echo -e "${BLUE}Stopping servers...${NC}"
  
  # Stop backend if running
  if [ -f "$BACKEND_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
    if ps -p "$BACKEND_PID" > /dev/null; then
      echo -e "${YELLOW}Stopping backend server (PID: $BACKEND_PID)...${NC}"
      kill -9 "$BACKEND_PID" 2>/dev/null
      rm "$BACKEND_DIR/backend.pid"
    else
      echo -e "${YELLOW}Backend server process not found, cleaning up pid file.${NC}"
      rm "$BACKEND_DIR/backend.pid"
    fi
  fi
  
  # Stop frontend if running
  if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
    if ps -p "$FRONTEND_PID" > /dev/null; then
      echo -e "${YELLOW}Stopping frontend server (PID: $FRONTEND_PID)...${NC}"
      kill -9 "$FRONTEND_PID" 2>/dev/null
      rm "$FRONTEND_DIR/frontend.pid"
    else
      echo -e "${YELLOW}Frontend server process not found, cleaning up pid file.${NC}"
      rm "$FRONTEND_DIR/frontend.pid"
    fi
  fi
  
  # Also kill any processes on our ports to be sure
  kill_port_processes 4000
  kill_port_processes 3000
  
  echo -e "${GREEN}All servers have been stopped.${NC}"
}

# Cleanup function to stop servers when script is interrupted
cleanup() {
  echo -e "\n${BLUE}Catching interrupt signal. Cleaning up...${NC}"
  stop_servers
  
  # Also kill any remaining processes on our ports
  kill_port_processes 4000
  kill_port_processes 3000
  
  exit 0
}

# Function to handle server crashes
handle_crash() {
  echo -e "\n${RED}A server has crashed. Cleaning up...${NC}"
  stop_servers
  exit 1
}

# Display help
show_help() {
  echo -e "${BLUE}Flask + Next.js Web Application Build/Run Script${NC}"
  echo -e "Usage: $0 [command]"
  echo -e ""
  echo -e "Commands:"
  echo -e "  setup       Setup both backend and frontend"
  echo -e "  build       Build the frontend for production"
  echo -e "  start       Start both servers in production mode"
  echo -e "  dev         Start both servers in development mode"
  echo -e "  stop        Stop all running servers"
  echo -e "  check_ports Check and clear ports 3000 and 4000 if they are in use"
  echo -e "  help        Show this help message"
}

# Main execution based on argument
case "$1" in
  setup)
    check_dependencies
    setup_backend
    setup_frontend
    ;;
  build)
    build_frontend
    ;;
  start)
    start_backend
    start_frontend
    echo -e "${YELLOW}Press Ctrl+C to stop both servers.${NC}"
    trap cleanup INT
    
    # Get PIDs from files
    BACKEND_PID=""
    FRONTEND_PID=""
    [ -f "$BACKEND_DIR/backend.pid" ] && BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
    [ -f "$FRONTEND_DIR/frontend.pid" ] && FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
    
    # Monitor both processes in production mode too
    while true; do
      if [ -n "$BACKEND_PID" ] && ! ps -p "$BACKEND_PID" > /dev/null; then
        echo -e "${RED}Backend server crashed or stopped unexpectedly. Stopping all servers.${NC}"
        # Stop remaining servers
        stop_servers
        exit 1
      fi
      
      if [ -n "$FRONTEND_PID" ] && ! ps -p "$FRONTEND_PID" > /dev/null; then
        echo -e "${RED}Frontend server crashed or stopped unexpectedly. Stopping all servers.${NC}"
        # Stop remaining servers
        stop_servers
        exit 1
      fi
      
      # Check every 2 seconds
      sleep 2
    done
    ;;
  dev)
    start_dev
    ;;
  stop)
    stop_servers
    ;;
  check_ports)
    echo -e "${BLUE}Checking port availability...${NC}"
    kill_port_processes 4000
    kill_port_processes 3000
    echo -e "${GREEN}Ports checked and cleared if necessary.${NC}"
    ;;
  help|*)
    show_help
    ;;
esac
