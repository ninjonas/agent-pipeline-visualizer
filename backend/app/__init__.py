# This file ensures the app directory is treated as a Python package

# First import the interface
from .agent_interface import AgentInterface

# Next import the factory
from .agent_factory import AgentFactory

# Then import the concrete implementations
from .agent import OpenAIAgent
from .dummy_agent import DummyAgent
from .custom_agent import CustomAgent

# Now we can register the implementations with the factory
AgentFactory.register_agent("openai", OpenAIAgent)
AgentFactory.register_agent("dummy", DummyAgent)
AgentFactory.register_agent("custom", CustomAgent)

# Create a default agent for backward compatibility
from .agent import default_agent as agent

# Replace the default agent with a factory-created one
# This ensures we have the same instance throughout the application
agent = AgentFactory.get_agent("openai")

__all__ = [
    'AgentInterface',
    'OpenAIAgent',
    'DummyAgent',
    'CustomAgent',
    'AgentFactory',
    'agent'  # Default agent instance
]
