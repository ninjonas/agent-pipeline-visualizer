from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import logging
import time
import uuid
import json
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Configure CORS for API routes
socketio = SocketIO(app, cors_allowed_origins="*")  # Initialize SocketIO with CORS

# In-memory storage for pipeline data (would be a database in production)
pipelines = {}

# Request logging middleware
@app.before_request
def before_request():
    request.start_time = time.time()
    logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        logger.info(f"Response: {response.status_code} - took {elapsed:.2f}s")
    return response

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'online',
        'message': 'Flask API is running successfully'
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({
        'items': [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'},
            {'id': 3, 'name': 'Item 3'}
        ]
    })

# Agent API endpoints
@app.route('/api/agent/register', methods=['POST'])
def register_agent_pipeline():
    """Register a new agent pipeline and return a unique pipeline ID"""
    data = request.json
    agent_name = data.get('agent_name', 'unknown')
    total_steps = data.get('total_steps', 0)
    
    pipeline_id = str(uuid.uuid4())
    
    # Store initial pipeline data
    pipelines[pipeline_id] = {
        'id': pipeline_id,
        'agent_name': agent_name,
        'created_at': time.time(),
        'status': 'initialized',
        'total_steps': total_steps,
        'completed_steps': 0,
        'steps': {}
    }
    
    logger.info(f"New pipeline registered: {pipeline_id} by agent {agent_name}")
    
    # Emit WebSocket event for new pipeline registration
    socketio.emit('pipeline_registered', {
        'pipeline_id': pipeline_id,
        'pipeline_data': pipelines[pipeline_id]
    })
    
    # Also emit an updated pipelines list
    pipeline_list = []
    for pid, data in pipelines.items():
        pipeline_list.append({
            'id': pid,
            'agent_name': data.get('agent_name'),
            'status': data.get('status'),
            'created_at': data.get('created_at'),
            'completed_steps': data.get('completed_steps'),
            'total_steps': data.get('total_steps')
        })
    
    socketio.emit('pipelines_list_updated', {
        'pipelines': pipeline_list
    })
    
    return jsonify({
        'pipeline_id': pipeline_id,
        'status': 'registered'
    })

@app.route('/api/agent/update', methods=['POST'])
def update_agent_pipeline():
    """Update the status of a pipeline step"""
    data = request.json
    pipeline_id = data.get('pipeline_id')
    step = data.get('step')
    status = data.get('status')
    message = data.get('message', '')
    step_data = data.get('data')
    
    if not pipeline_id or not step or not status:
        return jsonify({
            'error': 'Missing required fields'
        }), 400
    
    if pipeline_id not in pipelines:
        return jsonify({
            'error': f'Pipeline ID {pipeline_id} not found'
        }), 404
    
    # Update pipeline step status
    pipeline = pipelines[pipeline_id]
    pipeline['steps'][step] = {
        'status': status,
        'message': message,
        'updated_at': time.time()
    }
    
    # Store step data if provided
    if step_data:
        pipeline['steps'][step]['data'] = step_data
    
    # Update pipeline status
    step_count = len(pipeline['steps'])
    completed_steps = sum(1 for s in pipeline['steps'].values() if s.get('status') == 'completed')
    pipeline['completed_steps'] = completed_steps
    
    # Update overall pipeline status
    if completed_steps == pipeline['total_steps']:
        pipeline['status'] = 'completed'
    elif any(s.get('status') == 'failed' for s in pipeline['steps'].values()):
        pipeline['status'] = 'failed'
    else:
        pipeline['status'] = 'in_progress'
    
    logger.info(f"Pipeline {pipeline_id} step '{step}' updated: {status}")
    
    # Emit WebSocket event with the updated step data
    socketio.emit('step_updated', {
        'pipeline_id': pipeline_id,
        'step': step,
        'step_data': pipeline['steps'][step],
        'pipeline_status': pipeline['status'],
        'completed_steps': completed_steps,
        'total_steps': pipeline['total_steps']
    })
    
    # Emit full pipeline update for subscribers
    socketio.emit('pipeline_updated', {
        'pipeline_id': pipeline_id,
        'pipeline_data': pipeline
    })
    
    return jsonify({
        'pipeline_id': pipeline_id,
        'step': step,
        'status': 'updated'
    })

@app.route('/api/agent/status/<pipeline_id>', methods=['GET'])
def get_agent_pipeline_status(pipeline_id):
    """Get the current status of a pipeline"""
    if pipeline_id not in pipelines:
        return jsonify({
            'error': f'Pipeline ID {pipeline_id} not found'
        }), 404
    
    return jsonify(pipelines[pipeline_id])

@app.route('/api/agent/pipelines', methods=['GET'])
def list_agent_pipelines():
    """List all registered pipelines"""
    pipeline_list = []
    
    for pipeline_id, data in pipelines.items():
        pipeline_list.append({
            'id': pipeline_id,
            'agent_name': data.get('agent_name'),
            'status': data.get('status'),
            'created_at': data.get('created_at'),
            'completed_steps': data.get('completed_steps'),
            'total_steps': data.get('total_steps')
        })
    
    return jsonify({
        'pipelines': pipeline_list
    })

@app.route('/api/agent/execute', methods=['POST'])
def execute_agent_step():
    """Execute a specific step in an agent pipeline using the agent's client.py"""
    data = request.json
    pipeline_id = data.get('pipeline_id')
    step = data.get('step')

    if not pipeline_id or not step:
        return jsonify({
            'error': 'Missing required fields'
        }), 400

    if pipeline_id not in pipelines:
        return jsonify({
            'error': f'Pipeline ID {pipeline_id} not found'
        }), 404

    # Mark the step as running
    pipelines[pipeline_id]['steps'][step] = {
        'status': 'running',
        'message': f'Started executing {step}',
        'updated_at': time.time()
    }
    
    # Emit WebSocket event for step execution start
    socketio.emit('step_started', {
        'pipeline_id': pipeline_id,
        'step': step,
        'step_data': pipelines[pipeline_id]['steps'][step]
    })

    try:
        # Use subprocess to execute the agent's client.py with the step
        agent_dir = os.path.join(os.path.dirname(__file__), '../agent')
        client_file = os.path.join(agent_dir, 'client.py')

        if not os.path.exists(client_file):
            raise FileNotFoundError("Agent client.py not found")

        # Execute the client.py with the step and pipeline ID
        import subprocess
        import sys
        
        # Print debugging information about the Python environment
        logger.info(f"Using Python executable: {sys.executable}")
        logger.info(f"Working directory: {agent_dir}")
        
        # Get the parent directory for PYTHONPATH
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set a special environment variable to indicate we're running from the API
        # This helps the agent know to format output appropriately
        env_vars = dict(os.environ, 
                    PYTHONPATH=parent_dir, 
                    AGENT_API_MODE="1",
                    PYTHONUNBUFFERED="1")  # Disable Python output buffering
        
        try:
            # Create a unique output file for this run
            import tempfile
            temp_output_file = tempfile.NamedTemporaryFile(delete=False, mode='w+')
            temp_output_path = temp_output_file.name
            temp_output_file.close()
            
            try:
                # Run the agent with output redirected to our file
                with open(temp_output_path, 'w') as output_file:
                    process = subprocess.run(
                        [sys.executable, client_file, '--mode', 'step', '--step', step, '--pipeline-id', pipeline_id],
                        cwd=agent_dir,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env_vars
                    )
                
                # Read the clean output from file
                with open(temp_output_path, 'r') as input_file:
                    clean_stdout = input_file.read()
                
                # Create a result object with our clean stdout
                result = type('CompletedProcess', (), {
                    'returncode': process.returncode,
                    'stdout': clean_stdout,
                    'stderr': process.stderr
                })
                
                # Log details about the execution
                logger.info(f"Agent subprocess completed with return code: {result.returncode}")
                logger.info(f"Agent stdout length: {len(result.stdout)} bytes")
                logger.debug(f"Agent stdout: '{result.stdout}'")
                
                if result.stderr:
                    logger.warning(f"Agent stderr: '{result.stderr}'")
            finally:
                # Clean up temp file
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
        except Exception as e:
            logger.error(f"Error executing subprocess: {e}")
            raise

        if result.returncode != 0:
            logger.error(f"Agent execution failed with return code: {result.returncode}")
            logger.error(f"Agent stderr: {result.stderr}")
            raise RuntimeError(f"Agent execution failed: {result.stderr}")

        # Parse the output as JSON - handle potential JSON parsing errors
        try:
            # First try direct parsing of the output
            try:
                stdout_content = result.stdout.strip()
                logger.info(f"Raw stdout content length: {len(stdout_content)} bytes")
                logger.debug(f"Raw stdout content: '{stdout_content}'")
                
                if not stdout_content:
                    raise ValueError("Empty output from agent")
                
                # Try to parse the output directly first
                step_result = json.loads(stdout_content)
                logger.info("Successfully parsed direct JSON output")
                
            except json.JSONDecodeError as direct_error:
                # If direct parsing fails, try to extract a JSON object from mixed output
                logger.warning(f"Direct JSON parsing failed: {direct_error}")
                logger.info(f"Attempting to extract JSON from mixed output: '{stdout_content[:100]}...'")
                
                import re
                
                # Clean up output - try to find first { and last }
                first_brace = stdout_content.find('{')
                last_brace = stdout_content.rfind('}')
                
                if first_brace >= 0 and last_brace > first_brace:
                    # Try to extract what looks like a complete JSON object
                    potential_json = stdout_content[first_brace:last_brace+1]
                    try:
                        step_result = json.loads(potential_json)
                        logger.info("Successfully extracted clean JSON from output")
                    except json.JSONDecodeError:
                        # If that still fails, continue with regex approach
                        pass
                
                # Only continue with regex if we haven't found a valid result yet
                if 'step_result' not in locals():
                    # Look for patterns that might be complete JSON objects
                    json_patterns = [
                        r'(\{.*\})',  # Any object {...}
                        r'(\{[^{]*"status"[^}]*\})',  # Object containing "status"
                        r'(\{[^{]*"message"[^}]*\})'  # Object containing "message"
                    ]
                    
                    for pattern in json_patterns:
                        json_matches = re.findall(pattern, stdout_content, re.DOTALL)
                        if json_matches:
                            logger.info(f"Found {len(json_matches)} potential JSON matches with pattern {pattern}")
                            
                            # Try each potential JSON match until one parses correctly
                            for json_candidate in json_matches:
                                try:
                                    candidate_result = json.loads(json_candidate)
                                    # Check if this is a valid step result with required fields
                                    if "status" in candidate_result:
                                        step_result = candidate_result
                                        logger.info("Found valid JSON object in output")
                                        break
                                except json.JSONDecodeError:
                                    continue
                            
                            # If we found a valid result, break out of the pattern loop
                            if 'step_result' in locals():
                                break
                
                # If we still don't have a valid result
                if 'step_result' not in locals():
                    # Try manual approach: Get the entire content, log it, and build our own response
                    logger.error(f"Could not parse any valid JSON from agent output. Raw content: '{stdout_content}'")
                    
                    # Build a fallback response with the raw output
                    step_result = {
                        "status": "failed",
                        "message": "Could not parse JSON output from agent",
                        "data": {"raw_output": stdout_content}
                    }
            
            # Update the step status
            pipelines[pipeline_id]['steps'][step] = {
                'status': step_result.get('status', 'failed'),
                'message': step_result.get('message', 'No message provided'),
                'updated_at': time.time(),
                'data': step_result.get('data', {})
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw output: {result.stdout}")
            
            # Update with error status
            pipelines[pipeline_id]['steps'][step] = {
                'status': 'failed',
                'message': f"Failed to parse agent output: {e}",
                'updated_at': time.time(),
                'data': {'raw_output': result.stdout}
            }

    except Exception as e:
        logger.exception(f"Error during agent step execution: {e}")
        
        # Store more detailed error information
        error_message = str(e)
        error_type = type(e).__name__
        
        pipelines[pipeline_id]['steps'][step] = {
            'status': 'failed',
            'message': f"{error_type}: {error_message}",
            'updated_at': time.time(),
            'data': {
                'error_type': error_type,
                'error_details': error_message
            }
        }

    # Update overall pipeline status
    update_pipeline_status(pipeline_id)

    return jsonify({
        'pipeline_id': pipeline_id,
        'step': step,
        'result': pipelines[pipeline_id]['steps'][step]
    })

@app.route('/api/steps', methods=['GET'])
def list_steps():
    """List all available steps from steps_config.json"""
    config_path = os.path.join(os.path.dirname(__file__), '../agent/steps_config.json')

    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
            steps = config.get('steps', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading steps_config.json: {e}")
        return jsonify({
            'error': 'Failed to load steps configuration',
            'details': str(e)
        }), 500

    return jsonify({
        'steps': steps
    })

def update_pipeline_status(pipeline_id):
    """Update the overall status of a pipeline based on its steps"""
    if pipeline_id not in pipelines:
        return
    
    pipeline = pipelines[pipeline_id]
    steps = pipeline.get('steps', {})
    
    # Count completed steps
    completed_steps = sum(1 for s in steps.values() if s.get('status') == 'completed')
    pipeline['completed_steps'] = completed_steps
    
    # Update overall status
    if completed_steps == pipeline['total_steps']:
        pipeline['status'] = 'completed'
    elif any(s.get('status') == 'failed' for s in steps.values()):
        pipeline['status'] = 'failed'
    else:
        pipeline['status'] = 'in_progress'
    
    # Emit WebSocket event with updated pipeline data
    socketio.emit('pipeline_updated', {
        'pipeline_id': pipeline_id,
        'pipeline_data': pipeline
    })
       
# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error', 'message': str(error)}), 500

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_pipeline')
def handle_subscribe_pipeline(data):
    pipeline_id = data.get('pipeline_id')
    logger.info(f"Client {request.sid} subscribed to pipeline {pipeline_id}")
    
    if pipeline_id in pipelines:
        # Immediately send current pipeline data to the client
        emit('pipeline_updated', {
            'pipeline_id': pipeline_id,
            'pipeline_data': pipelines[pipeline_id]
        })

@socketio.on('subscribe_all_pipelines')
def handle_subscribe_all_pipelines():
    logger.info(f"Client {request.sid} subscribed to all pipelines")
    
    # Immediately send current pipelines list to the client
    pipeline_list = []
    for pipeline_id, data in pipelines.items():
        pipeline_list.append({
            'id': pipeline_id,
            'agent_name': data.get('agent_name'),
            'status': data.get('status'),
            'created_at': data.get('created_at'),
            'completed_steps': data.get('completed_steps'),
            'total_steps': data.get('total_steps')
        })
    
    emit('pipelines_list_updated', {
        'pipelines': pipeline_list
    })

if __name__ == '__main__':
    import signal
    import sys
    
    # Setup signal handling for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received termination signal. Shutting down gracefully...")
        # Clean up any resources if needed
        sys.exit(0)
        
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    port = int(os.environ.get('PORT', 4000))
    logger.info(f"Starting Flask-SocketIO server on port {port}")
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
