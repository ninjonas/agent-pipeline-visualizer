# This file ensures the app directory is treated as a Python package

# First import the interface
from .agent_interface import AgentInterface

# Next import the factory
from .agent_factory import AgentFactory

# Then import the concrete implementations from their respective folders
from .agents.openai import OpenAIAgent
from .agents.dummy import DummyAgent
from .agents.custom import CustomAgent

# Now we can register the implementations with the factory
AgentFactory.register_agent("openai", OpenAIAgent)
AgentFactory.register_agent("dummy", DummyAgent)
AgentFactory.register_agent("custom", CustomAgent)

# Create a default agent instance for backward compatibility
default_agent = AgentFactory.get_agent("openai")

__all__ = [
    'AgentInterface',
    'OpenAIAgent',
    'DummyAgent',
    'CustomAgent',
    'AgentFactory',
    'default_agent'
]
