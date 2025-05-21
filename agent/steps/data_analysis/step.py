import sys
import os

# Add the root directory to the path to make imports work
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from agent.steps.step_interface import PipelineStep, create_result

# Keep the original function for backward compatibility
def execute():
    """Logic for the data analysis step."""
    # Return a valid, complete response object
    return {
        "status": "success", 
        "message": "Data analysis completed", 
        "data": {"analysis": "summary"}
    }

# New class-based implementation using the PipelineStep interface
class Step(PipelineStep):
    """Data analysis step implementation using the PipelineStep interface."""
    
    def execute(self):
        """Execute the data analysis step."""
        # You could add more complex logic here
        return create_result(
            status="success",
            message="Data analysis completed",
            data={"analysis": "summary"}
        )
