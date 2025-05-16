# Agent Pipeline Visualizer

A web application that visualizes AI agent pipelines using a flexible agent interface system with a Flask API backend and a Next.js frontend.

## Quick Start

To start both the backend and frontend servers in development mode:

```bash
./run.sh dev
```

This will start:
- Flask backend on http://localhost:4000
- Next.js frontend on http://localhost:3000

If either the backend or frontend server crashes unexpectedly, the script will automatically detect this and shut down both servers to prevent orphaned processes.

## Project Structure

```
agent-pipeline-visualizer/
├── backend/                 # Flask backend
│   ├── app.py               # Main Flask application
│   ├── requirements.txt     # Python dependencies
│   └── app/                 # Application modules
│       ├── __init__.py      # Package initialization
│       ├── agent_interface.py # Base agent interface
│       ├── agent.py         # OpenAI agent implementation
│       ├── dummy_agent.py   # Dummy agent for testing
│       ├── custom_agent.py  # Example custom agent
│       └── agent_factory.py # Factory for creating agents
├── frontend/                # Next.js frontend
│   ├── package.json         # JavaScript dependencies
│   ├── public/              # Static files
│   ├── next.config.mjs      # Next.js configuration
│   └── src/                 # Source code
│       └── app/             # Next.js app directory
├── run.sh                   # Startup script
└── kill_servers.sh          # Shutdown script
```

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm 7 or higher

## Getting Started

### Agent Interface System

The application is built around a flexible agent interface system that allows developers to implement and use different AI agent backends. This is implemented using Python's abstract base classes and a factory pattern.

#### Available Agent Types

- **OpenAIAgent**: Uses the OpenAI API to provide responses
- **DummyAgent**: A simple agent that echoes back the input (for testing)
- **CustomAgent**: An example template for creating custom agent implementations

#### Creating Custom Agents

To create your own agent implementation:

1. Create a new Python file in the `backend/app/` directory
2. Implement the `AgentInterface` abstract class
3. Register your agent with the `AgentFactory`

Example:

```python
# my_agent.py
from app.agent_interface import AgentInterface
from app.agent_factory import AgentFactory
from typing import Dict, Any

class MyAgent(AgentInterface):
    def __init__(self, custom_param=None):
        self.custom_param = custom_param
        self.status = "idle"
        self.last_response = None
        self.error = None
        self.is_running = False
        self.status_thread = None
        
    def start(self) -> Dict[str, str]:
        # Implementation
        pass
        
    def stop(self) -> Dict[str, str]:
        # Implementation
        pass
        
    def get_status(self) -> Dict[str, Any]:
        # Implementation
        pass
        
    def query_agent(self, prompt: str) -> Dict[str, Any]:
        # Implementation
        pass

# Register with factory
AgentFactory.register_agent("my_agent", MyAgent)
```

#### API Endpoints for Agent Management

The backend exposes the following API endpoints for agent management:

- `GET /api/agent/types`: Get available agent types
- `POST /api/agent/create`: Create a new agent instance
- `POST /api/agent/start`: Start the current agent
- `POST /api/agent/stop`: Stop the current agent
- `GET /api/agent/status`: Get the current agent status
- `POST /api/agent/query`: Send a query to the agent

### Initial Setup

Run the setup script to install all dependencies for both the backend and frontend:

```bash
./run.sh setup
```

### Development Mode

To start both the backend and frontend servers in development mode:

```bash
./run.sh dev
```

This will start:
- Flask backend on http://localhost:4000
- Next.js frontend on http://localhost:3000

### Port Management

The application uses specific ports that need to be available:
- Backend: port 4000
- Frontend: port 3000

If you encounter any port conflicts, you can use the provided script to kill any processes using these ports:

```bash
./kill_servers.sh
```

This script will automatically detect and terminate any processes using ports 3000 and 4000.

### Production Build

To build the frontend for production:

```bash
./run.sh build
```

### Starting Production Servers

To start both servers in production mode:

```bash
./run.sh start
```

### Stopping Servers

To stop all running servers:

```bash
./run.sh stop
```

## API Endpoints

The Flask backend provides the following API endpoints:

- `GET /api/health` - Health check endpoint
- `GET /api/data` - Returns sample data
- `POST /api/echo` - Echoes back the posted data

## Features

- Flask backend with API endpoints
- Next.js frontend with TypeScript
- Tailwind CSS for styling
- CORS disabled for development
- API proxy configuration
- Build and run script

## Troubleshooting

### Port 4000 is already in use

If you see an error like "Port 4000 is already in use", you can:

1. Stop the process using that port:
   ```bash
   lsof -i:4000  # To find the process ID
   kill <PID>    # To kill the process
   ```

2. Or modify the `app.py` file to use a different port:
   ```python
   port = int(os.environ.get('PORT', 5001))  # Change to an available port
   ```
   
   Remember to also update the port in `next.config.mjs` and `apiService.ts` files.

### Next.js Configuration Issues

If you encounter ESM module issues with Next.js configuration:

1. Make sure your config file uses the correct export syntax:
   ```js
   // Use 'export default' instead of 'module.exports' in .mjs files
   export default nextConfig;
   ```

2. Check for duplicate configuration files (like both .mjs and .ts versions).

## License

MIT
