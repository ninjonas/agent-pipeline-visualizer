import time
import threading
from typing import Dict, Any, Optional, List
from .agent_interface import AgentInterface

class CustomAgent(AgentInterface):
    """
    An example of a more complex custom agent implementation.
    This demonstrates how developers can implement their own agents
    with custom behavior and integrations.
    """
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 tools: Optional[List[Dict[str, Any]]] = None,
                 system_prompt: str = "You are a helpful assistant."):
        """
        Initialize the custom agent with various configuration options.
        
        Args:
            model_path (Optional[str]): Path to local model or model identifier
            temperature (float): Sampling temperature for generation
            max_tokens (int): Maximum tokens to generate
            tools (Optional[List[Dict[str, Any]]]): Tools configuration for the agent
            system_prompt (str): The system prompt to use
        """
        self.model_path = model_path or "default_model"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.system_prompt = system_prompt
        
        # State tracking
        self.status = "idle"
        self.last_response = None
        self.error = None
        self.is_running = False
        self.status_thread = None
        
        # History tracking
        self.conversation_history = []
        
    def start(self) -> Dict[str, str]:
        """Start the agent in the background"""
        if self.status_thread is None or not self.status_thread.is_alive():
            self.is_running = True
            self.status = "initializing"
            self.error = None
            self.status_thread = threading.Thread(target=self._run_agent)
            self.status_thread.daemon = True
            self.status_thread.start()
            return {"status": "Custom Agent started", "current_status": self.status}
        return {"status": "Custom Agent already running", "current_status": self.status}
    
    def stop(self) -> Dict[str, str]:
        """Stop the agent"""
        self.is_running = False
        if self.status_thread and self.status_thread.is_alive():
            self.status_thread.join(timeout=2.0)
        self.status = "stopped"
        return {"status": "Custom Agent stopped"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent"""
        return {
            "status": self.status,
            "running": self.is_running,
            "last_response": self.last_response,
            "error": self.error,
            "model": self.model_path,
            "conversation_length": len(self.conversation_history),
            "tools_enabled": len(self.tools) > 0
        }
    
    def query_agent(self, prompt: str) -> Dict[str, Any]:
        """
        Send a query to the custom agent.
        
        Args:
            prompt (str): The user's prompt to process
            
        Returns:
            Dict[str, Any]: The response or error information
        """
        if not self.is_running:
            return {"error": "Agent is not running. Start the agent first."}
        
        try:
            self.status = "processing"
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            
            # In a real implementation, you would call your custom LLM here
            # For now, we'll simulate a response
            time.sleep(1.0)  # Simulate processing time
            
            response = f"This is a simulated response from {self.model_path} for: {prompt}"
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            self.last_response = response
            self.status = "idle"
            
            return {
                "response": response,
                "model_used": self.model_path,
                "tokens_used": len(prompt.split()) * 2  # Crude estimation
            }
            
        except Exception as e:
            self.error = f"Custom Agent Error: {str(e)}"
            self.status = "error"
            return {"error": self.error}
    
    def _run_agent(self):
        """Background thread function for the agent"""
        try:
            # Simulate loading a model
            self.status = "loading model"
            time.sleep(2.0)
            
            # Simulate model ready
            self.last_response = f"Custom model {self.model_path} loaded successfully"
            self.status = "idle"
            
            # Main agent loop
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            self.error = f"Custom Agent Error: {str(e)}"
            self.status = "error"
            self.is_running = False
