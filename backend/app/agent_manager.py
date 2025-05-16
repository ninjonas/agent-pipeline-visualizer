import os
import json
import shutil
import uuid
from typing import Dict, Any, List, Optional
from .agent_factory import AgentFactory
from .agent_interface import AgentInterface

class AgentManager:
    """
    Manages multiple agent instances, each in their own directory.
    
    This class handles the creation, retrieval, starting, stopping,
    and monitoring of multiple agent instances.
    """
    
    def __init__(self, base_dir: str = "agents"):
        """
        Initialize the agent manager.
        
        Args:
            base_dir (str): The base directory where agent folders will be created
        """
        # Ensure base directory exists (create relative to the backend folder)
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", base_dir))
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Dictionary to store active agent instances
        self.agents: Dict[str, AgentInterface] = {}
        
        # Load existing agents from disk
        self._load_existing_agents()
    
    def _load_existing_agents(self) -> None:
        """Load and initialize agents from existing directories"""
        if not os.path.exists(self.base_dir):
            return
            
        for agent_id in os.listdir(self.base_dir):
            agent_dir = os.path.join(self.base_dir, agent_id)
            config_path = os.path.join(agent_dir, "agent_config.json")
            
            if os.path.isdir(agent_dir) and os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                    agent_type = config.get('agent_type')
                    agent_config = config.get('config', {})
                    
                    if agent_type:
                        # Create the agent instance but don't auto-start
                        self.agents[agent_id] = AgentFactory.get_agent(agent_type, **agent_config)
                except Exception as e:
                    print(f"Error loading agent {agent_id}: {str(e)}")
    
    def create_agent(self, agent_type: str, config: Dict[str, Any] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new agent of the specified type.
        
        Args:
            agent_type (str): The type of agent to create
            config (Dict[str, Any]): Configuration for the agent
            name (Optional[str]): A friendly name for the agent
            
        Returns:
            Dict[str, Any]: Status information including the new agent ID
        """
        # Generate a unique ID for the agent
        agent_id = str(uuid.uuid4())
        
        # Create a directory for this agent
        agent_dir = os.path.join(self.base_dir, agent_id)
        os.makedirs(agent_dir, exist_ok=True)
        
        # Store the configuration
        agent_config = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'name': name or f"Agent-{agent_id[:8]}",
            'config': config or {}
        }
        
        with open(os.path.join(agent_dir, "agent_config.json"), 'w') as f:
            json.dump(agent_config, f, indent=2)
        
        try:
            # Create the agent instance
            self.agents[agent_id] = AgentFactory.get_agent(agent_type, **(config or {}))
            return {
                'status': 'success',
                'agent_id': agent_id,
                'message': f'Created agent of type: {agent_type}'
            }
        except Exception as e:
            # Clean up on failure
            shutil.rmtree(agent_dir, ignore_errors=True)
            return {'error': f'Failed to create agent: {str(e)}'}
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an agent and its associated directory.
        
        Args:
            agent_id (str): The ID of the agent to delete
            
        Returns:
            Dict[str, Any]: Status information
        """
        if agent_id not in self.agents:
            return {'error': f'Agent with ID {agent_id} not found'}
        
        # Stop the agent if it's running
        if self.agents[agent_id].get_status().get('running', False):
            self.agents[agent_id].stop()
        
        # Remove from active agents dictionary
        agent = self.agents.pop(agent_id)
        
        # Delete the agent directory
        agent_dir = os.path.join(self.base_dir, agent_id)
        if os.path.exists(agent_dir):
            shutil.rmtree(agent_dir)
        
        return {
            'status': 'success',
            'message': f'Agent {agent_id} deleted'
        }
    
    def get_agent(self, agent_id: str) -> Optional[AgentInterface]:
        """
        Get the agent instance by ID.
        
        Args:
            agent_id (str): The ID of the agent to retrieve
            
        Returns:
            Optional[AgentInterface]: The agent instance or None if not found
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Get a list of all agents and their statuses.
        
        Returns:
            List[Dict[str, Any]]: List of agent information
        """
        result = []
        for agent_id, agent in self.agents.items():
            # Get agent config
            config_path = os.path.join(self.base_dir, agent_id, "agent_config.json")
            config = {}
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                except:
                    pass
            
            # Get status
            status = agent.get_status()
            
            result.append({
                'agent_id': agent_id,
                'name': config.get('name', f"Agent-{agent_id[:8]}"),
                'agent_type': config.get('agent_type', 'unknown'),
                'status': status.get('status', 'unknown'),
                'running': status.get('running', False)
            })
        
        return result
    
    def start_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Start a specific agent.
        
        Args:
            agent_id (str): The ID of the agent to start
            
        Returns:
            Dict[str, Any]: Status information
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {'error': f'Agent with ID {agent_id} not found'}
        
        return agent.start()
    
    def stop_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Stop a specific agent.
        
        Args:
            agent_id (str): The ID of the agent to stop
            
        Returns:
            Dict[str, Any]: Status information
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {'error': f'Agent with ID {agent_id} not found'}
        
        return agent.stop()
    
    def get_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific agent.
        
        Args:
            agent_id (str): The ID of the agent to get status for
            
        Returns:
            Dict[str, Any]: Status information
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {'error': f'Agent with ID {agent_id} not found'}
        
        return agent.get_status()
    
    def query_agent(self, agent_id: str, prompt: str) -> Dict[str, Any]:
        """
        Send a query to a specific agent.
        
        Args:
            agent_id (str): The ID of the agent to query
            prompt (str): The prompt to send to the agent
            
        Returns:
            Dict[str, Any]: Response from the agent
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {'error': f'Agent with ID {agent_id} not found'}
        
        return agent.query_agent(prompt)


# Create a global instance of the agent manager
agent_manager = AgentManager()