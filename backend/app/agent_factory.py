from typing import Dict, Any, Optional, Type
from .agent_interface import AgentInterface

class AgentFactory:
    """
    Factory class for creating different types of agents.
    Developers can register their own agent implementations here.
    """

    # Registry of available agent implementations
    _registry: Dict[str, Type[AgentInterface]] = {}
    
    @classmethod
    def register_agent(cls, name: str, agent_class: Type[AgentInterface]) -> None:
        """
        Register a new agent implementation.
        
        Args:
            name (str): The name to register the agent under
            agent_class (Type[AgentInterface]): The agent class that implements AgentInterface
        """
        cls._registry[name] = agent_class
    
    @classmethod
    def get_agent(cls, agent_type: str, **kwargs) -> AgentInterface:
        """
        Create an instance of the specified agent type.
        
        Args:
            agent_type (str): The type of agent to create
            **kwargs: Configuration parameters for the agent
            
        Returns:
            AgentInterface: An instance of the requested agent
            
        Raises:
            ValueError: If the agent type is not registered
        """
        if agent_type not in cls._registry:
            raise ValueError(f"Agent type '{agent_type}' is not registered")
            
        agent_class = cls._registry[agent_type]
        return agent_class(**kwargs)
    
    @classmethod
    def list_available_agents(cls) -> Dict[str, Type[AgentInterface]]:
        """
        List all available agent implementations.
        
        Returns:
            Dict[str, Type[AgentInterface]]: A dictionary of registered agent types
        """
        return cls._registry.copy()


# Registration of agents will be done in __init__.py to avoid circular imports
