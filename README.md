# Agent Pipeline Visualizer

A web application for visualizing multi-step agent workflows, with a Next.js TypeScript frontend and Python Flask backend.

## Project Structure

```
agent-pipeline-visualizer/
├── frontend/          # Next.js TypeScript frontend
├── backend/           # Flask Python backend
├── agent/             # Dummy agent implementation for developers to reference
├── run.sh             # Development script to manage both services
└── build_prod.sh      # Production build script
```

## Features

- **Frontend**: Next.js v14+ with TypeScript and Tailwind CSS (Port 3000)
- **Backend**: Flask REST API with CORS support (Port 4000)
- **WebSocket Support**: Real-time updates with no UI flickering during step execution
- **Agent Integration**: Reference implementation of a multi-step agent pipeline
- **Pipeline Visualization**: Interactive dashboard to monitor agent workflows
- **Build Scripts**:
  - Development script to run both servers with automatic port management
  - Production build script for deployment-ready builds

## Requirements

- Node.js and npm
- Python 3.8+
- Bash shell (for the build scripts)

## Setup

### Frontend

```bash
cd frontend
npm install
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

### Development

Use the development script to run both frontend and backend with WebSocket support:

```bash
./run.sh dev
```

This will:

- Kill any processes running on ports 3000 and 4000
- Start the Next.js frontend with WebSocket support on port 3000
- Start the Flask backend with WebSocket support on port 4000
- Enable real-time updates with no UI flickering during step execution

### Production Build

To build the application for production:

```bash
./build_prod.sh
```

This will:

- Build the Next.js application for production
- Prepare the Flask backend with Gunicorn for production
- Create startup scripts for both frontend and backend

### Running in Production

After building, you can run the production versions using:

```bash
# Start the frontend (in one terminal)
./start_frontend.sh

# Start the backend (in another terminal)
./start_backend.sh
```

## API Endpoints

### Basic Endpoints

- `GET /api/status` - Returns the status of the backend
- `GET /api/data` - Returns sample data

### Agent API Endpoints

- `POST /api/agent/register` - Register a new pipeline

### WebSocket Events

- `connect` - Client connection event
- `disconnect` - Client disconnection event
- `subscribe_pipeline` - Subscribe to updates for a specific pipeline
- `subscribe_all_pipelines` - Subscribe to updates for all pipelines
- `pipeline_updated` - Emitted when a pipeline is updated
- `step_updated` - Emitted when a step is updated
- `step_started` - Emitted when a step execution begins
- `pipelines_list_updated` - Emitted when the pipelines list changes
- `POST /api/agent/update` - Update a pipeline step status
- `GET /api/agent/status/<pipeline_id>` - Get the status of a specific pipeline
- `GET /api/agent/pipelines` - List all registered pipelines
- `POST /api/agent/execute` - Execute a specific step in a pipeline (for UI triggering)

## Frontend Pages

- `/` - Main page with connection status to the backend
- `/agent` - Agent pipeline visualization dashboard

## Development Notes

### Port Management

The application is configured to use specific ports:

- Frontend: Port 3000
- Backend: Port 4000

The build scripts automatically handle killing any existing processes on these ports before starting the services.

### Backend Features

- CORS support for API endpoints
- Request logging middleware
- Error handling for 404 and 500 errors

### Frontend Features

- TypeScript support
- Tailwind CSS for styling
- API utilities for backend communication

## Extending the Application

### Adding New API Endpoints

1. Edit `backend/app.py` to add new route handlers
2. Use the existing pattern:

```python
@app.route('/api/your-endpoint', methods=['GET'])
def your_endpoint():
    return jsonify({
        'data': 'Your response data'
    })
```

### Adding New Frontend Pages

1. Create new files in `frontend/src/app` directory
2. Follow the Next.js App Router conventions

## Agent Integration

The application includes a reference agent implementation that demonstrates how to integrate with the pipeline visualization system.

### Agent Directory Structure

```
agent/
├── agent.py           # Main agent implementation with multi-step pipeline
├── client.py          # CLI client to interact with the agent
├── requirements.txt   # Dependencies for the agent
└── README.md          # Detailed documentation on using the agent
```

### Running the Agent

1. Set up the agent environment:

```bash
./run.sh agent
```

2. Run the agent in step-by-step interactive mode:

```bash
./run.sh agent-run step
```

3. Run the agent in full pipeline mode:

```bash
./run.sh agent-run full
```

4. Run a specific step directly:

```bash
./run.sh agent-run step data_collection
```

5. Run everything at once (frontend, backend, and agent setup):

```bash
./run.sh full
```

### Integrating Your Own Agent

To integrate your own agent implementation:

1. Review the `agent.py` file to understand the communication pattern
2. Implement API calls to register your pipeline and update step statuses
3. Refer to `INTEGRATION_GUIDE.md` in the agent directory for detailed instructions
