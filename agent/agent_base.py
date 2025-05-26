import os
import json
import time
import importlib.util
from typing import Dict, List, Optional, Any
import requests
from loguru import logger

# Configure Loguru logger for the agent
# Ensure the log directory exists relative to this script's location
# (assuming this script is in the 'agent' directory)
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'log'))
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'agent.log')
logger.add(log_file_path, rotation="10 MB", retention="7 days", level="INFO", format="{time} {level} {message}")


class AgentBase:
    """Base class for AI Agent implementations"""
    
    def __init__(self, api_url: str = "http://localhost:4000"):
        self.api_url = api_url
        self.steps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steps")
        self.config = self._load_config()
        self.status = self._load_status()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            # Default configuration
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
                ]
            }
            
            # Save default config
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def _load_status(self) -> Dict[str, Dict[str, str]]:
        """Load agent status"""
        status_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json")
        
        if os.path.exists(status_path):
            with open(status_path, "r") as f:
                return json.load(f)
        else:
            return {}
    
    def _save_status(self) -> None:
        """Save agent status"""
        status_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json")
        
        with open(status_path, "w") as f:
            json.dump(self.status, f, indent=2)
    
    def _update_step_status(self, step_id: str, status: str) -> None:
        """Update the status of a step"""
        if step_id not in self.status:
            self.status[step_id] = {}
        
        self.status[step_id]["status"] = status
        self._save_status()
        
        # Notify the API of the status change
        try:
            requests.post(f"{self.api_url}/api/steps/{step_id}", json={"status": status})
        except Exception as e:
            logger.warning(f"Failed to notify API of status change: {e}")
    
    def _get_step_config(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific step"""
        for step in self.config.get("steps", []):
            if step["id"] == step_id:
                return step
        return None
    
    def _get_dependent_steps(self, step_id: str) -> List[str]:
        """Get the IDs of steps that this step depends on"""
        step_config = self._get_step_config(step_id)
        if step_config:
            return step_config.get("dependencies", [])
        return []
    
    def _get_step_path(self, step_id: str) -> str:
        """Get the path to a step's directory"""
        return os.path.join(self.steps_dir, step_id)
    
    def _ensure_step_directories(self, step_id: str) -> None:
        """Ensure that a step's input and output directories exist"""
        step_path = self._get_step_path(step_id)
        os.makedirs(os.path.join(step_path, "in"), exist_ok=True)
        os.makedirs(os.path.join(step_path, "out"), exist_ok=True)
    
    def _check_step_dependencies(self, step_id: str) -> bool:
        """Check if all dependencies for a step are completed"""
        dependencies = self._get_dependent_steps(step_id)
        
        for dep_id in dependencies:
            dep_status = self.status.get(dep_id, {}).get("status", "pending")
            if dep_status != "completed":
                return False
        
        return True
    
    def _wait_for_user_approval(self, step_id: str) -> bool:
        """Wait for user approval of a step's output"""
        approval_file = os.path.join(self._get_step_path(step_id), "out", ".approved")
        
        # Check if the approval file already exists (from a previous run)
        if os.path.exists(approval_file):
            os.remove(approval_file)
            return True
        
        logger.info(f"Waiting for user approval of step '{step_id}'...")
        logger.info(f"Please review the output files in '{os.path.join(self._get_step_path(step_id), 'out')}'")
        logger.info("Once you've reviewed the output, approve the step in the web interface or press Enter to continue.")
        
        # Mark step as waiting for input
        self._update_step_status(step_id, "waiting_input")
        
        logger.debug(f"_wait_for_user_approval for '{step_id}'. os.environ.get('CI') is '{os.environ.get('CI')}'")
        # Either wait for the approval file to be created or for user input
        # Only wait for stdin if not in a CI environment
        wait_for_stdin = os.environ.get("CI") != "true"
        logger.debug(f"wait_for_stdin is {wait_for_stdin}")

        while True:
            if os.path.exists(approval_file):
                os.remove(approval_file)
                return True
            
            # Check for user input (non-blocking) if allowed
            if wait_for_stdin:
                import select
                import sys
                
                # Check if there's input available (with a timeout)
                if select.select([sys.stdin], [], [], 1.0)[0]:
                    input()  # Consume the input
                    return True
            else:
                # If not waiting for stdin (e.g., in CI mode), just sleep briefly
                # to avoid busy-waiting, relying on the approval file.
                time.sleep(1)
    
    def _load_step_module(self, step_id: str) -> Any:
        """Load the Python module for a step"""
        step_file = os.path.join(self._get_step_path(step_id), f"{step_id}.py")
        
        if not os.path.exists(step_file):
            # Create a template module file
            with open(step_file, "w", encoding="utf-8") as f: # Added encoding
                # Corrected f-string for the template
                template_content = f"""from agent.step_base import StepBase
from loguru import logger

class {step_id.title().replace('_', '')}Step(StepBase):
    \\\"\\\"\\\"
    Implementation of the {step_id.replace('_', ' ').title()} step.
    \\\"\\\"\\\"
    
    def execute(self) -> bool:
        \\\"\\\"\\\"
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        \\\"\\\"\\\"
        # Implement your step logic here
        logger.info(f"Executing {step_id.replace('_', ' ').title()} step")
        
        # Example: Create a sample output file
        with open(self.get_output_path("result.txt"), "w", encoding=\\"utf-8\\") as f: # Added encoding
            f.write("This is a sample output from the {step_id.replace('_', ' ').title()} step.\\\\n")
            f.write("Edit this file to implement your own logic.\\\\n")
        
        return True
"""
                f.write(template_content)
        
        # Load the module
        spec = importlib.util.spec_from_file_location(f"agent.steps.{step_id}", step_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    def run_step(self, step_id: str) -> bool:
        """Run a specific step"""
        logger.info(f"Running step: {step_id}")
        
        # Ensure step directories exist
        self._ensure_step_directories(step_id)
        
        # Check if dependencies are satisfied
        if not self._check_step_dependencies(step_id):
            logger.warning(f"Dependencies not satisfied for step '{step_id}'")
            self._update_step_status(step_id, "waiting_dependency")
            return False
        
        # Update status to in_progress
        self._update_step_status(step_id, "in_progress")
        
        try:
            # Load the step module
            module = self._load_step_module(step_id)
            
            # Get the step class name (convert snake_case to CamelCase + 'Step')
            class_name = ''.join(word.title() for word in step_id.split('_')) + 'Step'
            
            # Get the step class
            step_class = getattr(module, class_name)
            
            # Create a step instance
            step = step_class(
                step_id=step_id,
                input_dir=os.path.join(self._get_step_path(step_id), "in"),
                output_dir=os.path.join(self._get_step_path(step_id), "out")
            )
            
            # Execute the step
            success = step.execute()
            
            if success:
                # Check if user approval is required
                step_config = self._get_step_config(step_id)
                if step_config and step_config.get("requiresUserInput", False):
                    approved = self._wait_for_user_approval(step_id)
                    if approved:
                        self._update_step_status(step_id, "completed")
                        return True
                    else:
                        self._update_step_status(step_id, "failed")
                        return False
                else:
                    # No user approval required
                    self._update_step_status(step_id, "completed")
                    return True
            else:
                self._update_step_status(step_id, "failed")
                return False
        
        except Exception as e:
            logger.error(f"Error running step '{step_id}': {e}")
            self._update_step_status(step_id, "failed")
            return False
    
    def run_all_steps(self) -> bool:
        """Run all steps in order"""
        all_success = True
        
        for step in self.config.get("steps", []):
            step_id = step["id"]
            success = self.run_step(step_id)
            if not success:
                all_success = False
        
        return all_success
    
    def get_available_steps(self) -> List[str]:
        """Get a list of steps that are available to run (dependencies satisfied)"""
        available_steps = []
        
        for step in self.config.get("steps", []):
            step_id = step["id"]
            if self._check_step_dependencies(step_id) and self.status.get(step_id, {}).get("status", "pending") != "completed":
                available_steps.append(step_id)
        
        return available_steps
