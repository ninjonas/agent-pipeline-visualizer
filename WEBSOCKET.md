# WebSocket Support for Agent Pipeline Visualizer

This guide explains how the WebSocket implementation eliminates UI flickering.

## Running with WebSockets

WebSockets are now enabled by default when using the development mode:

```bash
./run.sh dev
```

This command will:

1. Install required WebSocket dependencies for both backend and frontend
2. Start the Flask backend with WebSocket support
3. Start the Next.js frontend with socket.io-client

## Benefits of WebSockets

- **Real-time updates**: Pipeline and step status changes appear instantly
- **No flickering**: Eliminates the UI flickering during step execution
- **Reduced network traffic**: Single persistent connection instead of polling
- **Better performance**: Less resource usage on both client and server

## Implementation Details

The WebSocket implementation includes:

- **Backend**: Flask-SocketIO emits real-time events when pipeline data changes
- **Frontend**: React hooks for subscribing to WebSocket events
- **Communication**: Bidirectional real-time updates between client and server

## Troubleshooting

If you experience any issues:

1. Check browser console for WebSocket errors
2. Ensure both backend and frontend are running
3. Verify port 4000 is accessible

## Running Agent Steps

With the WebSocket server running, you can execute agent steps as usual:

```bash
./run.sh agent-run step
```

The UI will update in real-time without flickering when steps are executed.
