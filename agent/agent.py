"""
Agent implementation that doesn't require external dependencies.
"""
import json
import os
import random
import sys
import time
import importlib
import importlib.util
import uuid
import logging
from typing import Dict, Any, Optional, Type, cast
from abc import ABC, abstractmethod

# Get paths for imports
agent_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(agent_dir)

# Add parent directory to path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import PipelineStep using importlib to avoid package import issues
step_interface_path = os.path.join(agent_dir, "steps", "step_interface.py")
spec = importlib.util.spec_from_file_location("step_interface", step_interface_path)
step_interface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step_interface)
PipelineStep = step_interface.PipelineStep
create_result = step_interface.create_result

# Determine log level from environment variable
log_level_name = os.environ.get("AGENT_LOG_LEVEL", "WARNING").upper()
log_level = getattr(logging, log_level_name, logging.WARNING)

# Check if we're in API mode (suppress most logging)
if os.environ.get("AGENT_API_MODE") == "1":
    log_level = logging.ERROR  # Only show errors in API mode

logger = logging.getLogger("agent")
handler = logging.StreamHandler(sys.stderr)  # Send logs to stderr
handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(log_level)

# Print debug info for module imports
if __name__ != "__main__":  # Only when imported, not when run directly
    logger.debug(f"Agent module loaded from: {__file__}")
    logger.debug(f"Python path: {sys.path}")

class PipelineAgent:
    """
    A dummy agent that demonstrates a multi-step data processing workflow.
    This agent simulates the processing steps without external dependencies.
    """
    
    def __init__(self, api_url: str = "http://localhost:4000"):
        """
        Initialize the agent with configuration.
        
        Args:
            api_url: URL of the backend API
        """
        self.api_url = api_url
        self.pipeline_id = None
        
        # Load steps from configuration file
        config_path = os.path.join(os.path.dirname(__file__), "steps_config.json")
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            self.steps = config.get("steps", [])
            # Load acknowledgment feature config
            self.steps_requiring_acknowledgment = config.get("steps_requiring_acknowledgment", {})
        
        self.step_status = {step: "pending" for step in self.steps}
        self.current_step = None
        self.results = {}
        self.pending_acknowledgment = None
    
    def register_pipeline(self) -> str:
        """Register a new pipeline (simulated)"""
        # We're being called with an existing pipeline ID
        if hasattr(sys, "pipeline_id"):
            self.pipeline_id = getattr(sys, "pipeline_id")
            logger.info("Using existing pipeline ID: %s", self.pipeline_id)
        else:
            # Generate a pipeline ID
            self.pipeline_id = str(uuid.uuid4())
            logger.info("Pipeline registered with ID: %s", self.pipeline_id)
        
        return self.pipeline_id
    
    def update_step_status(self, step_name: str, status: str, message: str = "", data: Any = None) -> bool:
        """Update the status of a step (simulated)"""
        if not self.pipeline_id:
            logger.error("No pipeline ID. Register pipeline first.")
            return False
        
        # Update local state only
        self.step_status[step_name] = status
        if data:
            if "results" not in self.results:
                self.results["results"] = {}
            self.results["results"][step_name] = data
        
        logger.info("Step '%s' updated: %s", step_name, status)
        return True
    
    def execute_step(self, step_name: str) -> Dict[str, Any]:
        """Execute a specific pipeline step"""
        if step_name not in self.steps:
            return {"status": "error", "message": f"Unknown step: {step_name}"}
        
        if self.step_status[step_name] == "completed":
            return {"status": "skipped", "message": f"Step '{step_name}' already completed"}
        
        # Check if there's a pending acknowledgment
        if self.pending_acknowledgment:
            return {
                "status": "waiting_for_acknowledgment",
                "message": f"Waiting for user acknowledgment for step '{self.pending_acknowledgment}'",
                "requires_acknowledgment": True,
                "pending_step": self.pending_acknowledgment
            }
        
        self.current_step = step_name
        self.update_step_status(step_name, "running", f"Starting {step_name}...")
        
        # Simulate processing time
        processing_time = random.uniform(1.5, 4.0)
        time.sleep(processing_time)
        
        # Try to use actual step implementations if available, otherwise simulate
        step_result = self._process_step(step_name)
        
        # Check if step requires acknowledgment
        requires_acknowledgment = (
            step_name in self.steps_requiring_acknowledgment and
            self.steps_requiring_acknowledgment.get(step_name, False)
        )
        
        if requires_acknowledgment:
            # Set pending acknowledgment and update status
            self.pending_acknowledgment = step_name
            self.update_step_status(
                step_name, 
                "waiting_for_acknowledgment", 
                f"Completed {step_name} in {processing_time:.2f}s, waiting for user acknowledgment",
                step_result["data"]
            )
            # Add acknowledgment flag to the result
            step_result["requires_acknowledgment"] = True
        elif step_result["status"] == "success":
            # Normal successful completion without acknowledgment required
            self.update_step_status(
                step_name, 
                "completed", 
                f"Completed {step_name} in {processing_time:.2f}s",
                step_result["data"]
            )
        else:
            # Failed step
            self.update_step_status(
                step_name, 
                "failed", 
                step_result["message"]
            )
            
        self.current_step = None
        return step_result
    
    def _process_step(self, step_name: str) -> Dict[str, Any]:
        """Perform the actual processing for a step by dynamically loading its module."""
        try:
            # Use a relative import path based on the current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            step_dir = os.path.join(current_dir, "steps", step_name)
            # Add step directory to path temporarily
            sys.path.insert(0, step_dir)
            
            # First try the direct import approach
            try:
                step_module_path = "step"
                logger.info("Attempting to import module: %s from %s", step_module_path, step_dir)
                
                # Use importlib to load the module directly from file
                step_file_path = os.path.join(step_dir, "step.py")
                if os.path.exists(step_file_path):
                    spec = importlib.util.spec_from_file_location(step_module_path, step_file_path)
                    step_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(step_module)
                else:
                    # Fall back to standard import
                    step_module = importlib.import_module(step_module_path)
            except ImportError as e:
                # If that fails, try as a package
                step_module_path = f"agent.steps.{step_name}.step"
                logger.info("First approach failed (%s), trying: %s", e, step_module_path)
                step_module = importlib.import_module(step_module_path)
            finally:
                # Clean up sys.path no matter what
                if step_dir in sys.path:
                    sys.path.remove(step_dir)
            
            # Try to create a PipelineStep instance if the module has a Step class
            if hasattr(step_module, "Step"):
                try:
                    # Instantiate the Step class and call its execute method
                    step_instance = step_module.Step()
                    
                    # Check if the instance implements the interface by checking for the execute method
                    if hasattr(step_instance, 'execute') and callable(step_instance.execute):
                        step_execute_result = step_instance.execute()
                        # Ensure data field exists
                        if not step_execute_result.get("data"):
                            step_execute_result["data"] = {}
                        logger.debug("Step %s result from Step instance: %s", step_name, json.dumps(step_execute_result))
                        return step_execute_result
                    else:
                        logger.warning("Step %s has a Step class but it doesn't implement expected interface", step_name)
                except Exception as ex:
                    logger.error("Error instantiating Step class: %s", ex)
            
            # Fall back to the old function-based approach
            if hasattr(step_module, "execute"):
                step_result = step_module.execute()
                # Ensure the result is properly formatted
                if not isinstance(step_result, dict):
                    logger.warning("Step %s returned non-dict result. Converting to standard format.", step_name)
                    return {
                        "status": "success",
                        "message": f"Execution of {step_name} completed",
                        "data": {"raw_result": str(step_result)}
                    }
                
                # Ensure required fields exist
                if "status" not in step_result:
                    step_result["status"] = "success"
                if "message" not in step_result:
                    step_result["message"] = f"Execution of {step_name} completed"
                if "data" not in step_result:
                    step_result["data"] = {}
                    
                # Log the result for debugging
                logger.debug("Step %s result: %s", step_name, json.dumps(step_result))
                return step_result
            else:
                logger.warning("Step module %s has no execute() function or Step class. Using simulation.", step_module_path)
                # Fallback to simulated execution
                return self._simulate_step_execution(step_name)
        except Exception as e:
            logger.error("Error executing step module: %s", e)
            # Fallback to simulated execution on error
            return self._simulate_step_execution(step_name)
    
    def _simulate_step_execution(self, step_name: str) -> Dict[str, Any]:
        """Generate a simulated result for a step execution"""
        processing_time = random.uniform(0.5, 1.0)
        
        # Generate a fake successful result
        data = {
            "timestamp": time.time(),
            "metrics": {
                "accuracy": round(random.uniform(0.75, 0.98), 2),
                "duration": processing_time
            }
        }
        
        return {
            "status": "success",
            "message": f"Simulated execution of {step_name} completed",
            "data": data
        }
    
    def execute_pipeline(self) -> Dict[str, Any]:
        """Execute the entire pipeline sequentially"""
        if not self.pipeline_id:
            self.register_pipeline()
        
        results = {
            "pipeline_id": self.pipeline_id,
            "status": "in_progress",
            "steps": {}
        }
        
        for step_name in self.steps:
            step_result = self.execute_step(step_name)
            results["steps"][step_name] = step_result
            
            # Stop pipeline execution if a step fails
            if step_result["status"] == "error":
                break
        
        # Determine overall pipeline status
        if all(self.step_status[step_name] == "completed" for step_name in self.steps):
            results["status"] = "completed"
        elif any(self.step_status[step_name] == "failed" for step_name in self.steps):
            results["status"] = "failed"
        else:
            results["status"] = "partial"
        
        return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get the current status of the pipeline"""
        return {
            "pipeline_id": self.pipeline_id,
            "steps": self.step_status,
            "current_step": self.current_step,
            "results": self.results
        }
    
    def acknowledge_step(self, step_name: str) -> Dict[str, Any]:
        """
        Acknowledge a step that was waiting for user confirmation.
        
        Args:
            step_name: The name of the step to acknowledge
            
        Returns:
            Dict with status of the acknowledgment
        """
        if not self.pending_acknowledgment:
            return {
                "status": "error",
                "message": "No step is waiting for acknowledgment"
            }
            
        if self.pending_acknowledgment != step_name:
            return {
                "status": "error",
                "message": f"Step {step_name} is not waiting for acknowledgment. {self.pending_acknowledgment} is."
            }
            
        # Mark the step as completed
        self.update_step_status(
            step_name,
            "completed",
            f"Step {step_name} acknowledged by user"
        )
        
        # Clear the pending acknowledgment
        self.pending_acknowledgment = None
        
        return {
            "status": "success",
            "message": f"Step {step_name} acknowledged",
            "step": step_name
        }


if __name__ == "__main__":
    # Example usage
    agent = PipelineAgent()
    pipeline_id = agent.register_pipeline()
    
    # Option 1: Execute entire pipeline
    # results = agent.execute_pipeline()
    # print(json.dumps(results, indent=2))
    
    # Option 2: Execute steps individually
    for step in agent.steps:
        result = agent.execute_step(step)
        print(f"Step '{step}' execution: {result['status']}")
        
        # Get current pipeline status
        status = agent.get_pipeline_status()
        print(f"Current pipeline status: {json.dumps(status, indent=2)}")
