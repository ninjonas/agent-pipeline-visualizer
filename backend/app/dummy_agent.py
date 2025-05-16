import time
import threading
from typing import Dict, Any, Optional
from .agent_interface import AgentInterface

class DummyAgent(AgentInterface):
    """
    A simple dummy agent implementation that doesn't use any external API.
    This serves as an example for how to implement the AgentInterface.
    """
    
    def __init__(self, response_delay: float = 1.0):
        """
        Initialize the dummy agent.
        
        Args:
            response_delay (float): Simulated delay in seconds for responses
        """
        self.response_delay = response_delay
        self.status = "idle"
        self.last_response = None
        self.error = None
        self.is_running = False
        self.status_thread = None
    
    def start(self) -> Dict[str, str]:
        """Start the agent in the background"""
        if self.status_thread is None or not self.status_thread.is_alive():
            self.is_running = True
            self.status = "initializing"
            self.error = None
            self.status_thread = threading.Thread(target=self._run_agent)
            self.status_thread.daemon = True
            self.status_thread.start()
            return {"status": "Agent started", "current_status": self.status}
        return {"status": "Agent already running", "current_status": self.status}
    
    def stop(self) -> Dict[str, str]:
        """Stop the agent"""
        self.is_running = False
        if self.status_thread and self.status_thread.is_alive():
            self.status_thread.join(timeout=2.0)
        self.status = "stopped"
        return {"status": "Agent stopped"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent"""
        return {
            "status": self.status,
            "running": self.is_running,
            "last_response": self.last_response,
            "error": self.error
        }
    
    def query_agent(self, prompt: str) -> Dict[str, Any]:
        """
        Send a direct query to the agent.
        This dummy implementation just echoes the prompt back after a delay.
        
        Args:
            prompt (str): The user's prompt to process
            
        Returns:
            Dict[str, Any]: The response or error information
        """
        if not self.is_running:
            return {"error": "Agent is not running. Start the agent first."}
        
        try:
            self.status = "processing"
            
            # Simulate processing delay
            time.sleep(self.response_delay)
            
            # Simple response logic - just echo the prompt
            response = f"Dummy Agent received: {prompt}"
            self.last_response = response
            self.status = "idle"
            
            return {"response": response}
            
        except Exception as e:
            self.error = f"Unexpected error: {str(e)}"
            self.status = "error"
            return {"error": self.error}
    
    def _run_agent(self):
        """Background thread function to simulate agent initialization"""
        try:
            # Simulate initialization
            self.status = "testing connection"
            time.sleep(2.0)
            
            self.last_response = "Dummy agent initialization complete"
            self.status = "idle"
            
            # Main agent loop - just wait for explicit queries
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            self.error = f"Unexpected error: {str(e)}"
            self.status = "error"
            self.is_running = False
