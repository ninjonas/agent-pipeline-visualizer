# Using the WebSocket Implementation

The agent-pipeline-visualizer now uses WebSockets for real-time updates instead of HTTP polling.

## How to Start

WebSockets are now enabled by default in the development mode. Simply run:

```bash
./run.sh dev
```

This will:

1. Install required dependencies
2. Start the Flask backend with WebSocket support
3. Start the Next.js frontend development server

## Features

- **Real-time updates**: Pipeline and step status updates appear instantly without polling
- **Reduced flickering**: No more page flickering during step execution
- **Lower network overhead**: WebSockets maintain a single connection instead of multiple HTTP requests
- **Better performance**: Smoother experience with large pipelines and multiple steps

## How It Works

1. **Backend**: The Flask server uses Flask-SocketIO to emit events when pipeline data changes
2. **Frontend**: React components subscribe to these events using socket.io-client
3. **Data Flow**: Changes in pipeline or step status are pushed to the client automatically

## Troubleshooting

If you experience any issues:

1. Check the console for WebSocket connection errors
2. Ensure both frontend and backend are running
3. Verify that port 4000 (backend) is accessible
4. Try refreshing the browser if connections are interrupted

## Key Files

- `backend/app.py` - Contains the WebSocket server implementation
- `frontend/src/lib/websocket.ts` - React hooks for WebSocket subscriptions
- `frontend/src/app/agent/websocket-page.tsx` - WebSocket-enabled agent page
- `frontend/src/app/agent/page.tsx` - Entry point that uses the WebSocket implementation
