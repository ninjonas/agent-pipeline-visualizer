import os
import json
import time
import importlib.util
from typing import Dict, List, Optional, Any
import requests
from loguru import logger
import sys

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
        logger.debug(f"Attempting to save status: {self.status} to {status_path}") # Log what's being saved
        try:
            with open(status_path, "w") as f:
                json.dump(self.status, f, indent=2)
            logger.debug(f"Successfully saved status to {status_path}")
        except Exception as e:
            logger.error(f"Failed to save status.json: {e}. Current status in memory: {self.status}")

    def _update_step_status(self, step_id: str, status: str) -> None:
        """Update the status of a step"""
        if step_id not in self.status:
            self.status[step_id] = {}
        
        if self.status[step_id].get("status") == status:
            logger.debug(f"[StatusUpdate] Step '{step_id}' is already '{status}'. No change to self.status, no save, no API POST.")
            return

        logger.info(f"[StatusUpdate] Changing status of step '{step_id}' from '{self.status[step_id].get('status')}' to '{status}'.")
        self.status[step_id]["status"] = status
        self._save_status() # Saves self.status to status.json
        
        try:
            response = requests.post(f"{self.api_url}/api/steps/{step_id}", json={"status": status}, timeout=10) # Increased timeout
            response.raise_for_status()
            logger.info(f"[StatusUpdate] Successfully notified API for step '{step_id}' new status '{status}'.") # Original log line was similar
        except requests.exceptions.RequestException as e:
            logger.warning(f"[StatusUpdate] Failed to notify API for step '{step_id}' status '{status}': {e}")

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
        if not dependencies:
            logger.debug(f"[DepCheck] Step '{step_id}' has no dependencies. Check passes.")
            return True
        
        logger.debug(f"[DepCheck] Checking dependencies for step '{step_id}'. Dependencies: {dependencies}. Current self.status snapshot: {json.dumps(self.status)}")
        all_deps_completed = True
        for dep_id in dependencies:
            dep_status_data = self.status.get(dep_id, {}) # self.status should be up-to-date due to run_pipeline's _load_status()
            dep_actual_status = dep_status_data.get("status", "pending")
            logger.info(f"[DepCheck] For '{step_id}', evaluating dependency '{dep_id}': its status is '{dep_actual_status}'. Required: 'completed'.")
            if dep_actual_status != "completed":
                logger.warning(f"[DepCheck] Dependency FAILED: '{dep_id}' for step '{step_id}' is '{dep_actual_status}' (not 'completed').")
                all_deps_completed = False
                break # No need to check further if one dependency fails
            else:
                logger.debug(f"[DepCheck] Dependency MET: '{dep_id}' for step '{step_id}' is 'completed'.")
        
        if all_deps_completed:
            logger.info(f"[DepCheck] All dependencies for '{step_id}' are 'completed'. Dependency check PASSED.")
        else:
            logger.warning(f"[DepCheck] Not all dependencies for '{step_id}' are 'completed'. Dependency check FAILED.")
        return all_deps_completed
    
    def _wait_for_user_approval(self, step_id: str) -> bool:
        """Wait for user approval of a step's output. Returns True if approved, False otherwise (currently always True or loops)."""
        approval_file = os.path.join(self._get_step_path(step_id), "out", ".approved")
        
        # Check if the approval file already exists (e.g., created by web UI before this function was called or during a brief pause)
        if os.path.exists(approval_file):
            logger.info(f"Approval file found for '{step_id}' at start of wait. Consuming it.")
            try:
                os.remove(approval_file)
            except OSError as e:
                logger.warning(f"Could not remove pre-existing approval file {approval_file} (might be race condition): {e}")
            # Assuming removal success or file gone, consider it approved.
            return True

        logger.info(f"Waiting for user approval of step '{step_id}'...")
        logger.info(f"Please review the output files in '{os.path.join(self._get_step_path(step_id), 'out')}'")
        logger.info("Once you've reviewed the output, approve the step in the web interface or press Enter in this terminal (if applicable).")
        
        # Set status to waiting_input. If it's already waiting_input, this will be a no-op if we check current status.
        # However, we want to ensure the notification fires if this is the first time entering wait for this execution.
        self._update_step_status(step_id, "waiting_input")
        
        can_check_stdin = os.environ.get("CI") != "true"
        is_tty = sys.stdin.isatty()
        if can_check_stdin and not is_tty:
            logger.info("Stdin is not a TTY; stdin approval will be disabled for this step.")
            can_check_stdin = False # Disable if not a TTY even if not CI

        last_stdin_error_log_time = 0
        stdin_error_log_interval = 60 # Log stdin errors at most once per minute

        while True:
            if os.path.exists(approval_file):
                logger.info(f"Approval file found for '{step_id}'. Consuming it.")
                try:
                    os.remove(approval_file)
                except OSError as e:
                    logger.warning(f"Error removing approval file {approval_file} (possibly already removed): {e}")
                return True # Approved
            
            if can_check_stdin:
                import select # Keep select import here, specific to this block
                try:
                    # Check if stdin is readable with a timeout
                    if not sys.stdin.closed and select.select([sys.stdin], [], [], 0.5)[0]: # 0.5s timeout
                        logger.debug(f"Stdin became readable for step '{step_id}'. Reading for approval.")
                        sys.stdin.readline() # Consume the Enter press
                        logger.info(f"Enter pressed in terminal for step '{step_id}', considering as approval.")
                        return True # Approved via stdin
                except EOFError:
                    if time.time() - last_stdin_error_log_time > stdin_error_log_interval:
                        logger.warning(f"EOF on stdin for step '{step_id}'. Disabling further stdin checks for this step.")
                        last_stdin_error_log_time = time.time()
                    can_check_stdin = False 
                except (ValueError, OSError) as e: # ValueError if stdin is closed, OSError for other issues
                    if time.time() - last_stdin_error_log_time > stdin_error_log_interval:
                        logger.warning(f"Error checking stdin for step '{step_id}': {e}. Disabling further stdin checks.")
                        last_stdin_error_log_time = time.time()
                    can_check_stdin = False
                except Exception as e: # Catch-all for unexpected select/input issues
                    if time.time() - last_stdin_error_log_time > stdin_error_log_interval:
                        logger.error(f"Unexpected error during stdin check for step '{step_id}': {e}", exc_info=True)
                        last_stdin_error_log_time = time.time()
                    can_check_stdin = False # Disable stdin checks to be safe
            
            time.sleep(0.5) # Poll every 0.5 seconds
    
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
        """Run a specific step. Returns True if successful (including approval), False otherwise."""
        logger.info(f"Initiating run for step: {step_id}")
        
        self._ensure_step_directories(step_id)
        
        current_status = self.status.get(step_id, {}).get("status", "pending")
        if current_status == "completed":
            logger.info(f"Step '{step_id}' is already marked as completed. Skipping run logic.")
            return True
        if current_status == "failed":
            logger.warning(f"Step '{step_id}' is marked as failed. Not running.")
            return False

        if not self._check_step_dependencies(step_id):
            logger.warning(f"Dependencies not satisfied for step '{step_id}'. Setting to 'waiting_dependency'.")
            self._update_step_status(step_id, "waiting_dependency")
            return False # Cannot run
        
        self._update_step_status(step_id, "in_progress")
        
        try:
            module = self._load_step_module(step_id)
            class_name = ''.join(word.title() for word in step_id.split('_')) + 'Step'
            step_class = getattr(module, class_name)
            step_instance = step_class(
                step_id=step_id,
                input_dir=os.path.join(self._get_step_path(step_id), "in"),
                output_dir=os.path.join(self._get_step_path(step_id), "out")
            )
            
            logger.info(f"Executing core logic for step '{step_id}'...")
            if not step_instance.execute(): # Step's own logic failed
                logger.error(f"Core logic execution for step '{step_id}' returned False.")
                self._update_step_status(step_id, "failed")
                return False

            # Step execution was successful, now handle user input if required
            step_config = self._get_step_config(step_id)
            if step_config and step_config.get("requiresUserInput"):
                logger.info(f"Step '{step_id}' requires user input. Waiting for approval...")
                
                # _wait_for_user_approval will block until approved (returns True) 
                # or if it were to implement a denial/timeout (returns False - currently doesn't)
                # It also handles setting status to 'waiting_input'.
                approved = self._wait_for_user_approval(step_id)
                
                if approved:
                    logger.info(f"Step '{step_id}' was approved by user.")
                    self._update_step_status(step_id, "completed") # CRITICAL: Mark completed AFTER approval
                    return True # Successfully executed and approved
                else:
                    # This path is for future if _wait_for_user_approval can return False (e.g. explicit denial)
                    logger.error(f"Step '{step_id}' was not approved or approval process failed.")
                    self._update_step_status(step_id, "failed") 
                    return False # Failed due to approval stage
            else:
                # No user input required, and execution was successful
                logger.info(f"Step '{step_id}' completed successfully (no user input was required).")
                self._update_step_status(step_id, "completed")
                return True # Successfully executed

        except Exception as e:
            logger.error(f"Unhandled exception during run_step for '{step_id}': {e}", exc_info=True)
            self._update_step_status(step_id, "failed")
            return False

    def run_pipeline(self) -> None:
        """Run the full agent pipeline sequentially."""
        logger.info("[Pipeline] Starting agent pipeline run...")
        
        all_steps_config = self.config.get("steps", [])
        if not all_steps_config:
            logger.warning("[Pipeline] No steps defined in the configuration. Pipeline cannot run.")
            return

        for step_config in all_steps_config:
            step_id = step_config["id"]
            logger.info(f"[Pipeline] Considering step: '{step_id}' in pipeline loop.")

            # Load fresh status from file at the start of EACH step's processing in the pipeline
            self.status = self._load_status()
            current_step_status_from_file = self.status.get(step_id, {}).get("status", "pending")
            logger.info(f"[Pipeline] Status of '{step_id}' (read from status.json via _load_status) before run_step call: '{current_step_status_from_file}'.")

            if current_step_status_from_file == "completed":
                logger.info(f"[Pipeline] Step '{step_id}' is already 'completed' (per status.json). Skipping.")
                continue

            if current_step_status_from_file == "failed":
                logger.warning(f"[Pipeline] Step '{step_id}' is 'failed' (per status.json). Skipping. Manual intervention may be required.")
                continue
            
            # If a step is waiting_input (e.g. from a previous interrupted run), run_step should handle it by calling _wait_for_user_approval.
            # _check_step_dependencies within run_step will ensure its direct dependencies are met before proceeding.

            logger.info(f"[Pipeline] About to call run_step for '{step_id}'. This call should block if '{step_id}' requires input and is not yet approved.")
            step_run_success = self.run_step(step_id) # This call is expected to be blocking until the step is resolved (completed/failed)
            logger.info(f"[Pipeline] run_step for '{step_id}' has returned, with result: {step_run_success}. Pipeline loop continues for '{step_id}'.")

            # Immediately after run_step returns, load the definitive status from the file again
            self.status = self._load_status()
            status_on_file_after_run_step = self.status.get(step_id, {}).get("status", "pending")
            logger.info(f"[Pipeline] Status of '{step_id}' (read from status.json) AFTER run_step returned: '{status_on_file_after_run_step}'.")

            if not step_run_success:
                logger.error(f"[Pipeline] HALTING. run_step for '{step_id}' returned False. Final status from file: '{status_on_file_after_run_step}'.")
                return # Stop the entire pipeline
            
            # If run_step returned True, the step should now be 'completed'. Verify this.
            if status_on_file_after_run_step != "completed":
                logger.error(f"[Pipeline] LOGIC ERROR or race condition! run_step for '{step_id}' returned True, but its status in status.json is '{status_on_file_after_run_step}' (expected 'completed'). HALTING.")
                return

            logger.info(f"[Pipeline] Step '{step_id}' successfully processed (run_step returned True and status is 'completed'). Moving to next step.")

        logger.info("[Pipeline] Agent pipeline has processed all defined steps.")
