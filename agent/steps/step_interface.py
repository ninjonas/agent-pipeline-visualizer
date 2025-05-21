"""
Defines the interface that all pipeline steps must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class PipelineStep(ABC):
    """
    Abstract base class defining the interface for pipeline steps.
    All step implementations should inherit from this class.
    """
    
    def requires_acknowledgment(self) -> bool:
        """
        Determine if this step requires user acknowledgment before proceeding.
        By default, steps don't require acknowledgment.
        
        Returns:
            bool: True if user must acknowledge before proceeding, False otherwise
        """
        return False
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the step and return a standardized result.
        
        Returns:
            Dict with the following structure:
                {
                    "status": str,  # "success", "error", etc.
                    "message": str,  # Human-readable description
                    "data": Dict[str, Any]  # Step-specific result data
                }
        """
        pass

# Helper function to create a standard result dictionary
def create_result(status: str = "success", message: str = "", data: Dict[str, Any] = None, 
                 requires_acknowledgment: bool = False) -> Dict[str, Any]:
    """
    Create a standardized result dictionary for step execution.
    
    Args:
        status: The status of the step execution ("success", "error", etc.)
        message: A human-readable message describing the result
        data: Step-specific result data
        requires_acknowledgment: Whether this step result needs user acknowledgment
        
    Returns:
        A dictionary with the standard result format
    """
    result = {
        "status": status,
        "message": message,
        "data": data or {}
    }
    
    # Add acknowledgment flag if needed
    if requires_acknowledgment:
        result["requires_acknowledgment"] = True
    
    return result
