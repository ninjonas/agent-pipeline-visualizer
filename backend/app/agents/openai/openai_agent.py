import time
import threading
import httpx
import json
from typing import Dict, Any, Optional
from ...agent_interface import AgentInterface

class OpenAIAgent(AgentInterface):
    """
    OpenAI-specific implementation of the AgentInterface.
    Uses the OpenAI API to provide LLM capabilities.
    """
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        # Use environment variables by default
        # API key should be set in .env file or environment variables as OPENAI_API_KEY
        import os
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
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
        """Send a direct query to the agent"""
        if not self.is_running:
            return {"error": "Agent is not running. Start the agent first."}
            
        try:
            self.status = "processing"
            
            # Use httpx to make a direct API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = httpx.post(
                f"{self.api_base}/chat/completions", 
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                self.last_response = result["choices"][0]["message"]["content"]
                self.status = "idle"
                return {"response": self.last_response}
            else:
                self.error = f"API Error: {response.status_code} - {response.text}"
                self.status = "error"
                return {"error": self.error}
                
        except httpx.HTTPError as e:
            self.error = f"HTTP Error: {str(e)}"
            self.status = "error"
            return {"error": self.error}
        except Exception as e:
            self.error = f"Unexpected error: {str(e)}"
            self.status = "error"
            return {"error": self.error}
    
    def _run_agent(self):
        """Background thread function that simulates agent initialization"""
        try:
            # Simulate connection test
            self.status = "testing connection"
            
            # Simple connection test
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = httpx.get(
                    f"{self.api_base}/models", 
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.last_response = "OpenAI connection established"
                else:
                    self.error = f"Connection test failed: {response.status_code}"
                    self.status = "error"
                    self.is_running = False
                    return
                    
            except Exception as e:
                self.error = f"Connection test error: {str(e)}"
                self.status = "error"
                self.is_running = False
                return
            
            # If we get here, we're good to go
            self.status = "idle"
            
            # Main agent loop - just keep thread alive until stopped
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            self.error = f"Agent error: {str(e)}"
            self.status = "error"
            self.is_running = False
