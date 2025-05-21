"""
Agent implementation that doesn't require external dependencies.
"""
import json
import os
import random
import sys
import time
import importlib
import uuid
from typing import Dict, List, Any, Optional

# Ensure 'agent' is in the module search path
agent_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(agent_dir)

# Clean up path to remove any duplicates
for path_entry in [agent_dir, parent_dir]:
    while path_entry in sys.path:
        sys.path.remove(path_entry)
        
# Add paths in the correct order
sys.path.insert(0, parent_dir)  # Add parent directory first
sys.path.insert(0, agent_dir)   # Add agent directory with highest priority

# Setup logging with environment variable control
import logging

# Determine log level from environment variable
log_level_name = os.environ.get('AGENT_LOG_LEVEL', 'WARNING').upper()
log_level = getattr(logging, log_level_name, logging.WARNING)

# Check if we're in API mode (suppress most logging)
if os.environ.get('AGENT_API_MODE') == '1':
    log_level = logging.ERROR  # Only show errors in API mode

logger = logging.getLogger("agent")
handler = logging.StreamHandler(sys.stderr)  # Send logs to stderr
handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
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
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            self.steps = config.get("steps", [])
        
        self.step_status = {step: "pending" for step in self.steps}
        self.current_step = None
        self.results = {}
    
    def register_pipeline(self) -> str:
        """Register a new pipeline (simulated)"""
        # We're being called with an existing pipeline ID
        if hasattr(sys, 'pipeline_id'):
            self.pipeline_id = getattr(sys, 'pipeline_id')
            logger.info(f"Using existing pipeline ID: {self.pipeline_id}")
        else:
            # Generate a pipeline ID
            self.pipeline_id = str(uuid.uuid4())
            logger.info(f"Pipeline registered with ID: {self.pipeline_id}")
        
        return self.pipeline_id
    
    def update_step_status(self, step: str, status: str, message: str = "", data: Any = None) -> bool:
        """Update the status of a step (simulated)"""
        if not self.pipeline_id:
            logger.error("No pipeline ID. Register pipeline first.")
            return False
        
        # Update local state only
        self.step_status[step] = status
        if data:
            if "results" not in self.results:
                self.results["results"] = {}
            self.results["results"][step] = data
        
        logger.info(f"Step '{step}' updated: {status}")
        return True
    
    def execute_step(self, step: str) -> Dict[str, Any]:
        """Execute a specific pipeline step"""
        if step not in self.steps:
            return {"status": "error", "message": f"Unknown step: {step}"}
        
        if self.step_status[step] == "completed":
            return {"status": "skipped", "message": f"Step '{step}' already completed"}
        
        self.current_step = step
        self.update_step_status(step, "running", f"Starting {step}...")
        
        # Simulate processing time
        processing_time = random.uniform(1.5, 4.0)
        time.sleep(processing_time)
        
        # Try to use actual step implementations if available, otherwise simulate
        result = self._process_step(step)
        
        # Update step status based on result
        if result["status"] == "success":
            self.update_step_status(
                step, 
                "completed", 
                f"Completed {step} in {processing_time:.2f}s",
                result["data"]
            )
        else:
            self.update_step_status(
                step, 
                "failed", 
                result["message"]
            )
            
        self.current_step = None
        return result
    
    def _process_step(self, step: str) -> Dict[str, Any]:
        """Perform the actual processing for a step by dynamically loading its module."""
        try:
            # Use a relative import path based on the current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            step_dir = os.path.join(current_dir, "steps", step)
            # Add step directory to path temporarily
            sys.path.insert(0, step_dir)
            
            # First try the direct import approach
            try:
                step_module_path = f"step"
                logger.info(f"Attempting to import module: {step_module_path} from {step_dir}")
                step_module = importlib.import_module(step_module_path)
            except ImportError as e:
                # If that fails, try as a package
                step_module_path = f"agent.steps.{step}.step"
                logger.info(f"First approach failed ({e}), trying: {step_module_path}")
                step_module = importlib.import_module(step_module_path)
            finally:
                # Clean up sys.path no matter what
                if step_dir in sys.path:
                    sys.path.remove(step_dir)
                
            if hasattr(step_module, "execute"):
                result = step_module.execute()
                # Ensure the result is properly formatted
                if not isinstance(result, dict):
                    logger.warning(f"Step {step} returned non-dict result. Converting to standard format.")
                    return {
                        "status": "success",
                        "message": f"Execution of {step} completed",
                        "data": {"raw_result": str(result)}
                    }
                
                # Ensure required fields exist
                if "status" not in result:
                    result["status"] = "success"
                if "message" not in result:
                    result["message"] = f"Execution of {step} completed"
                if "data" not in result:
                    result["data"] = {}
                    
                # Log the result for debugging
                logger.debug(f"Step {step} result: {json.dumps(result)}")
                return result
            else:
                logger.warning(f"Step module {step_module_path} has no execute() function. Using simulation.")
                # Fallback to simulated execution
                return self._simulate_step_execution(step)
        except Exception as e:
            logger.error(f"Error executing step module: {e}")
            # Fallback to simulated execution on error
            return self._simulate_step_execution(step)
    
    def _simulate_step_execution(self, step: str) -> Dict[str, Any]:
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
            "message": f"Simulated execution of {step} completed",
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
        
        for step in self.steps:
            step_result = self.execute_step(step)
            results["steps"][step] = step_result
            
            # Stop pipeline execution if a step fails
            if step_result["status"] == "error":
                break
        
        # Determine overall pipeline status
        if all(self.step_status[step] == "completed" for step in self.steps):
            results["status"] = "completed"
        elif any(self.step_status[step] == "failed" for step in self.steps):
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
