# Agent Pipeline Visualizer - Dummy Agent

This directory contains a dummy AI agent implementation that demonstrates a multi-step data processing workflow. This agent serves as a template for developers to understand how to integrate with the web application.

## Features

- Multi-step processing pipeline simulation
- Communication with the Flask backend API
- Progress tracking and status updates
- Step-by-step execution mode
- Full pipeline automation

## Pipeline Steps

The dummy agent implements a typical machine learning workflow with the following steps:

1. **Data Collection**: Gathering data from various sources
2. **Data Preprocessing**: Cleaning and preparing the data
3. **Feature Extraction**: Extracting relevant features from the data
4. **Model Training**: Training a machine learning model
5. **Evaluation**: Evaluating the model performance

## Setup

1. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Client

The client.py script demonstrates how to interact with the agent:

```bash
# Run the full pipeline automatically
python client.py --mode full

# Run the pipeline step by step (interactive mode)
python client.py --mode step

# Run a specific step
python client.py --mode step --step data_collection
```

Available steps:

- data_collection
- data_preprocessing
- feature_extraction
- model_training
- evaluation

### Direct Agent Usage

You can also import and use the agent directly in your code:

```python
from agent import PipelineAgent

# Initialize agent
agent = PipelineAgent(api_url="http://localhost:4000")
pipeline_id = agent.register_pipeline()

# Execute a step
result = agent.execute_step("data_collection")
print(result)

# Get pipeline status
status = agent.get_pipeline_status()
print(status)

# Execute entire pipeline
results = agent.execute_pipeline()
print(results)
```

## Integration with Web Application

The agent is designed to communicate with the web application's Flask backend API. It uses the following endpoints:

1. `/api/agent/register` - Register a new pipeline and get a pipeline ID
2. `/api/agent/update` - Update the status of a pipeline step

The frontend can display the progress of the pipeline steps by querying the backend API.

## Extending the Agent

To extend the agent for your specific use case:

1. Modify the `steps` list in the `PipelineAgent` class to match your workflow
2. Implement the actual processing logic in the `_process_step` method
3. Add any additional parameters or configuration options as needed

## Error Handling

The agent includes error handling and will continue to track progress locally even if the backend API is unavailable.
