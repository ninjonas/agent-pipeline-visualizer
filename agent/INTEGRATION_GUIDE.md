# Agent Integration Guide

This document provides instructions on how to integrate your own AI agent implementations with the Agent Pipeline Visualizer.

## Overview

The Agent Pipeline Visualizer is designed to work with any agent implementation that follows a multi-step processing pipeline model. The integration is done through a simple REST API.

## API Endpoints

The following endpoints are available for agent integration:

### 1. Register a Pipeline

```
POST /api/agent/register
```

Register a new pipeline and get a unique pipeline ID.

**Request Body:**

```json
{
  "agent_name": "YourAgentName",
  "total_steps": 5
}
```

**Response:**

```json
{
  "pipeline_id": "uuid-string",
  "status": "registered"
}
```

### 2. Update Step Status

```
POST /api/agent/update
```

Update the status of a pipeline step.

**Request Body:**

```json
{
  "pipeline_id": "uuid-string",
  "step": "step_name",
  "status": "running|completed|failed",
  "message": "Optional message about the step",
  "data": {} // Optional data output from the step
}
```

**Response:**

```json
{
  "pipeline_id": "uuid-string",
  "step": "step_name",
  "status": "updated"
}
```

### 3. Get Pipeline Status

```
GET /api/agent/status/<pipeline_id>
```

Get the current status of a pipeline.

**Response:**

```json
{
  "id": "uuid-string",
  "agent_name": "YourAgentName",
  "status": "in_progress|completed|failed",
  "created_at": 1621234567.89,
  "completed_steps": 2,
  "total_steps": 5,
  "steps": {
    "step_name": {
      "status": "running|completed|failed",
      "message": "Step message",
      "updated_at": 1621234567.89,
      "data": {} // Optional data output
    }
  }
}
```

### 4. List All Pipelines

```
GET /api/agent/pipelines
```

List all registered pipelines.

**Response:**

```json
{
  "pipelines": [
    {
      "id": "uuid-string",
      "agent_name": "YourAgentName",
      "status": "in_progress",
      "created_at": 1621234567.89,
      "completed_steps": 2,
      "total_steps": 5
    }
  ]
}
```

## Integration Steps

### 1. Register Your Pipeline

Before starting your agent's execution, register a new pipeline:

```python
import requests

def register_pipeline():
    response = requests.post(
        "http://localhost:4000/api/agent/register",
        json={
            "agent_name": "YourAgent",
            "total_steps": 5  # Number of steps in your pipeline
        }
    )
    response.raise_for_status()
    result = response.json()
    pipeline_id = result["pipeline_id"]
    return pipeline_id
```

### 2. Update Step Status During Execution

As your agent processes each step, update the status:

```python
def update_step(pipeline_id, step_name, status, message="", data=None):
    payload = {
        "pipeline_id": pipeline_id,
        "step": step_name,
        "status": status,  # "running", "completed", or "failed"
        "message": message
    }

    if data:
        payload["data"] = data

    response = requests.post(
        "http://localhost:4000/api/agent/update",
        json=payload
    )
    response.raise_for_status()
    return response.json()
```

### 3. Example Usage Pattern

Here's a simple pattern for integrating the visualizer with your agent:

```python
def run_agent():
    # Register pipeline
    pipeline_id = register_pipeline()

    # Define steps
    steps = ["data_collection", "preprocessing", "analysis", "output_generation", "cleanup"]

    # Execute steps
    for step in steps:
        try:
            # Mark step as running
            update_step(pipeline_id, step, "running", f"Starting {step}...")

            # Your actual step processing code
            result = process_step(step)

            # Mark step as completed
            update_step(pipeline_id, step, "completed", f"Completed {step}", result)
        except Exception as e:
            # Mark step as failed
            update_step(pipeline_id, step, "failed", f"Error in {step}: {str(e)}")
            break
```

## Best Practices

1. **Provide Meaningful Messages**: Include descriptive messages when updating step status to make it easier to track progress.

2. **Include Output Data**: When a step is completed, include the output data to visualize the results.

3. **Report Errors**: If a step fails, provide detailed error information to aid debugging.

4. **Batch Updates**: For long-running steps, consider providing periodic updates with the "running" status to show progress.

5. **Step Naming**: Use consistent naming for steps across all your agents for better organization.

## Advanced Integration

For more advanced integration scenarios, consider adding custom visualization components or extending the API to support your specific agent capabilities.

## Reference Implementation

For a reference implementation, see the `agent.py` file in the `agent` directory.
