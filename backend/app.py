from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.agent_factory import AgentFactory
from app.agent_manager import agent_manager

app = Flask(__name__)

# Enable CORS for all routes (will be used in development)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Flask API is running'})

@app.route('/api/echo', methods=['POST'])
def echo():
    # Echo back the request data
    data = request.get_json()
    return jsonify({
        'received': data,
        'message': 'Data received successfully'
    })

# Multi-Agent management endpoints
@app.route('/api/agents', methods=['GET'])
def list_agents():
    """Get a list of all available agents"""
    agents = agent_manager.list_agents()
    return jsonify({"agents": agents})

@app.route('/api/agent/types', methods=['GET'])
def get_agent_types():
    """Get all available agent types from the factory"""
    agent_types = list(AgentFactory._registry.keys())
    return jsonify({"agent_types": agent_types})

@app.route('/api/agent/create', methods=['POST'])
def create_agent():
    """Create a new agent of the specified type with optional config"""
    data = request.get_json()
    if not data or 'agent_type' not in data:
        return jsonify({'error': 'No agent type provided'}), 400
    
    agent_type = data['agent_type']
    config = data.get('config', {})
    name = data.get('name')
    
    result = agent_manager.create_agent(agent_type, config, name)
    return jsonify(result)

@app.route('/api/agent/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an existing agent"""
    result = agent_manager.delete_agent(agent_id)
    return jsonify(result)

@app.route('/api/agent/<agent_id>/start', methods=['POST'])
def start_agent(agent_id):
    """Start a specific agent"""
    result = agent_manager.start_agent(agent_id)
    return jsonify(result)

@app.route('/api/agent/<agent_id>/stop', methods=['POST'])
def stop_agent(agent_id):
    """Stop a specific agent"""
    result = agent_manager.stop_agent(agent_id)
    return jsonify(result)

@app.route('/api/agent/<agent_id>/status', methods=['GET'])
def get_agent_status(agent_id):
    """Get the status of a specific agent"""
    result = agent_manager.get_status(agent_id)
    return jsonify(result)

@app.route('/api/agent/<agent_id>/query', methods=['POST'])
def query_agent(agent_id):
    """Send a query to a specific agent"""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400
    
    result = agent_manager.query_agent(agent_id, data['prompt'])
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))  # Using port 4000
    app.run(host='0.0.0.0', port=port, debug=True)
