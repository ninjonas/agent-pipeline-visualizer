from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AgentInterface(ABC):
    """
    Interface for AI Agents that can be implemented with different LLM backends.
    This interface defines the standard methods that all agent implementations should provide.
    """
    
    @abstractmethod
    def start(self) -> Dict[str, str]:
        """
        Start the agent in the background.
        
        Returns:
            Dict[str, str]: Status information about the agent startup
        """
        pass
    
    @abstractmethod
    def stop(self) -> Dict[str, str]:
        """
        Stop the agent.
        
        Returns:
            Dict[str, str]: Status information about the agent shutdown
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dict[str, Any]: Status information including current state, 
                           last response, and any errors
        """
        pass
    
    @abstractmethod
    def query_agent(self, prompt: str) -> Dict[str, Any]:
        """
        Send a direct query to the agent.
        
        Args:
            prompt (str): The user's prompt to process
            
        Returns:
            Dict[str, Any]: The response or error information
        """
        pass
