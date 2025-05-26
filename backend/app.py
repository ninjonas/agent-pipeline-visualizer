from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
import shutil
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent'))
CONFIG_FILE = os.path.join(AGENT_DIR, 'config.json')
STEPS_DIR = os.path.join(AGENT_DIR, 'steps')

# Ensure agent directory structure exists
def ensure_directories():
    """Ensure all required directories exist"""
    if not os.path.exists(AGENT_DIR):
        os.makedirs(AGENT_DIR)
    
    if not os.path.exists(STEPS_DIR):
        os.makedirs(STEPS_DIR)
    
    # Create step directories if they don't exist
    step_dirs = [
        'data_analysis', 'evaluation_generation', 'create_contribution_goal', 
        'create_development_item', 'update_contribution_goal', 'update_development_item',
        'timely_feedback', 'coaching'
    ]
    
    for step in step_dirs:
        step_path = os.path.join(STEPS_DIR, step)
        if not os.path.exists(step_path):
            os.makedirs(step_path)
        
        in_dir = os.path.join(step_path, 'in')
        out_dir = os.path.join(step_path, 'out')
        
        if not os.path.exists(in_dir):
            os.makedirs(in_dir)
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

# Load agent configuration
def load_config():
    """Load agent configuration from file or create default"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    # Default configuration if file doesn't exist
    default_config = {
        "steps": [
            {
                "id": "data_analysis",
                "name": "Data Analysis",
                "description": "Analyze performance data to identify trends and areas for improvement.",
                "requiresUserInput": True,
                "dependencies": [],
                "group": "performance_evaluation"
            },
            {
                "id": "evaluation_generation",
                "name": "Evaluation Generation",
                "description": "Generate performance evaluations based on the analysis of data and feedback.",
                "requiresUserInput": True,
                "dependencies": ["data_analysis"],
                "group": "performance_evaluation"
            },
            {
                "id": "create_contribution_goal",
                "name": "Create Contribution Goal",
                "description": "Create specific, measurable contribution goals for team members based on performance data.",
                "requiresUserInput": True,
                "dependencies": ["evaluation_generation"],
                "group": "performance_evaluation"
            },
            {
                "id": "create_development_item",
                "name": "Create Development Item",
                "description": "Create development items to help team members improve their skills and performance.",
                "requiresUserInput": True,
                "dependencies": ["evaluation_generation"],
                "group": "performance_evaluation"
            },
            {
                "id": "update_contribution_goal",
                "name": "Update Contribution Goal",
                "description": "Update contribution goals based on the progress made by team members.",
                "requiresUserInput": True,
                "dependencies": ["create_contribution_goal"],
                "group": "monthly_checkins"
            },
            {
                "id": "update_development_item",
                "name": "Update Development Item",
                "description": "Update development items based on the progress made by team members.",
                "requiresUserInput": True,
                "dependencies": ["create_development_item"],
                "group": "monthly_checkins"
            },
            {
                "id": "timely_feedback",
                "name": "Timely Feedback",
                "description": "Provide timely feedback to team members based on their performance and progress.",
                "requiresUserInput": True,
                "dependencies": ["update_contribution_goal", "update_development_item"],
                "group": "monthly_checkins"
            },
            {
                "id": "coaching",
                "name": "Coaching",
                "description": "Provide coaching and support to team members to help them achieve their goals and improve their performance.",
                "requiresUserInput": True,
                "dependencies": ["timely_feedback"],
                "group": "monthly_checkins"
            }
        ],
        "status": {}
    }
    
    # Save default config
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    return default_config

# Save agent configuration
def save_config(config):
    """Save agent configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Get step status
def get_step_status():
    """Get current status of all steps"""
    config = load_config()
    status_file = os.path.join(AGENT_DIR, 'status.json')
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
        except Exception as e:
            print(f"Error loading status: {e}")
            status = {}
    else:
        status = {}
    
    steps = []
    
    # Combine step configuration with status
    for step in config['steps']:
        step_id = step['id']
        step_status = status.get(step_id, {})
        
        steps.append({
            "id": step_id,
            "name": step["name"],
            "description": step["description"],
            "status": step_status.get("status", "pending"),
            "requiresUserInput": step["requiresUserInput"],
            "dependencies": step["dependencies"],
            "group": step.get("group", ""),
            "message": step_status.get("message") # Added this line
        })
    
    return steps

# Get files for a step
def get_step_files(step_id):
    """Get list of files in the step's output directory"""
    out_dir = os.path.join(STEPS_DIR, step_id, 'out')
    
    if not os.path.exists(out_dir):
        return []
    
    files = []
    for file in os.listdir(out_dir):
        file_path = os.path.join(out_dir, file)
        if os.path.isfile(file_path):
            files.append(file_path)
    
    return files

# API routes
@app.route('/api/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return jsonify({"status": "ok"})

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update agent configuration"""
    if request.method == 'GET':
        return jsonify(load_config())
    elif request.method == 'POST':
        new_config = request.json
        save_config(new_config)

        # Update status.json with requiresUserInput from new_config
        status_file = os.path.join(AGENT_DIR, 'status.json')
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
        else:
            status_data = {}

        for step_config in new_config.get('steps', []):
            step_id = step_config.get('id')
            if step_id:
                if step_id not in status_data:
                    status_data[step_id] = {}
                status_data[step_id]['requiresUserInput'] = step_config.get('requiresUserInput', False)
        
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
        return jsonify({"status": "success"})

@app.route('/api/steps', methods=['GET'])
def api_steps():
    """Get all steps with their status"""
    steps = get_step_status()
    return jsonify({"steps": steps})

@app.route('/api/steps/<step_id>', methods=['GET'])
def api_step(step_id):
    """Get a specific step with its status"""
    steps = get_step_status()
    step = next((s for s in steps if s['id'] == step_id), None)
    
    if step:
        return jsonify(step)
    else:
        return jsonify({"error": "Step not found"}), 404

@app.route('/api/steps/<step_id>/files', methods=['GET'])
def api_step_files(step_id):
    """Get files for a specific step"""
    files = get_step_files(step_id)
    return jsonify({"files": files})

@app.route('/api/steps/<step_id>/approve', methods=['POST'])
def api_approve_step(step_id):
    """Approve a step that's waiting for user input"""
    status_file = os.path.join(AGENT_DIR, 'status.json')
    
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            status = json.load(f)
    else:
        status = {}
    
    # Update the step status if it's waiting for user input
    if step_id in status and status[step_id].get('status') == 'waiting_input':
        status[step_id]['status'] = 'completed'
        
        # Write the approval status to a special file that the agent will check
        approval_file = os.path.join(STEPS_DIR, step_id, 'out', '.approved')
        with open(approval_file, 'w') as f:
            f.write('approved')
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "Step not in waiting_input state"}), 400

@app.route('/api/steps/<step_id>/run', methods=['POST'])
def api_run_step(step_id):
    """Run a specific step"""
    try:
        # Ensure the parent directory of 'agent' is in sys.path
        # to allow imports like 'from agent.agent_base import AgentBase'
        import sys
        # AGENT_DIR is defined as os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent'))
        # We need its parent in sys.path for 'import agent.agent_base'
        # or AGENT_DIR itself if we are doing 'from agent_base import AgentBase'
        # Let's add the parent of AGENT_DIR to sys.path to be safe for package imports.
        agent_parent_dir = os.path.abspath(os.path.join(AGENT_DIR, '..'))
        if agent_parent_dir not in sys.path:
            sys.path.insert(0, agent_parent_dir) # Insert at the beginning for priority

        from agent.agent_base import AgentBase # Try importing as part of the 'agent' package

        current_steps_status = get_step_status()
        step = next((s for s in current_steps_status if s['id'] == step_id), None)
        
        if not step:
            return jsonify({"status": "error", "error": f"Step {step_id} not found", "steps": current_steps_status}), 404
        
        for dep_id in step['dependencies']:
            dep_step = next((s for s in current_steps_status if s['id'] == dep_id), None)
            if not dep_step or dep_step['status'] != 'completed':
                return jsonify({
                    "status": "error", 
                    "error": f"Step {step_id} has unsatisfied dependencies: {dep_id} is not completed",
                    "steps": current_steps_status
                }), 400
        
        agent = AgentBase()
        agent.run_step(step_id)
        
        updated_steps_status = get_step_status()
        final_step_state = next((s for s in updated_steps_status if s['id'] == step_id), None)

        if final_step_state and final_step_state['status'] not in ['failed', 'pending', 'waiting_dependency']:
            return jsonify({"status": "success", "message": f"Step {step_id} processed.", "steps": updated_steps_status})
        else:
            detailed_error = ""
            if final_step_state and final_step_state.get('message'):
                detailed_error = f" - Details: {final_step_state['message']}"
            
            current_status_str = final_step_state['status'] if final_step_state and final_step_state.get('status') else 'unknown'
            error_message = f"Step {step_id} may have failed or is in an unexpected state: {current_status_str}{detailed_error}"
            return jsonify({"status": "error", "error": error_message, "steps": updated_steps_status}), 500

    except ImportError as e:
        print(f"ImportError in api_run_step for {step_id}: {e}")
        print(f"Current sys.path: {sys.path}")
        print(f"AGENT_DIR: {AGENT_DIR}")
        current_steps_status_on_error = get_step_status() if 'current_steps_status' in locals() else []
        return jsonify({"status": "error", "error": f"Server configuration error (ImportError): {str(e)}", "steps": current_steps_status_on_error}), 500
    except Exception as e:
        print(f"Error running step {step_id}: {e}")
        current_steps_status_on_error = get_step_status() if 'current_steps_status' in locals() else []
        return jsonify({"status": "error", "error": str(e), "steps": current_steps_status_on_error}), 500

@app.route('/api/files', methods=['GET', 'POST'])
def api_files():
    """Get or update file content"""
    if request.method == 'GET':
        file_path = request.args.get('path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            return jsonify({"content": content})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        data = request.json
        file_path = data.get('path')
        content = data.get('content')
        
        if not file_path:
            return jsonify({"error": "No file path provided"}), 400
        
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset the agent pipeline by clearing status and output files"""
    try:
        # Reset status
        status_file = os.path.join(AGENT_DIR, 'status.json')
        with open(status_file, 'w') as f:
            json.dump({}, f)
        
        # Clear output files for all steps
        step_dirs = [
            'data_analysis', 'evaluation_generation', 'create_contribution_goal', 
            'create_development_item', 'update_contribution_goal', 'update_development_item',
            'timely_feedback', 'coaching'
        ]
        
        for step in step_dirs:
            step_out_dir = os.path.join(STEPS_DIR, step, 'out')
            if os.path.exists(step_out_dir):
                for item in os.listdir(step_out_dir):
                    item_path = os.path.join(step_out_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
        
        return jsonify({"status": "success", "message": "Pipeline reset successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Start the server
if __name__ == '__main__':
    # Ensure directories exist
    ensure_directories()
    
    # Create default config if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        load_config()
    
    app.run(host='0.0.0.0', port=4000, debug=True)
