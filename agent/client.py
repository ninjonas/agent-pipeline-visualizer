#!/usr/bin/env python3
"""
Client script t    api_url = args.api_url
    step_name = args.step
    mode = args.mode
    api_mode_flag = args.api_mode
    acknowledge_mode = args.acknowledge
    
    # Set pipeline ID if provided
    if args.pipeline_id:
        setattr(sys, "pipeline_id", args.pipeline_id)
    
    # Create agent instance
    agent = PipelineAgent(api_url=api_url)
    
    # Register pipeline
    pipeline_id = agent.register_pipeline()
    
    output = {}
    try:
        # Handle acknowledgment mode
        if acknowledge_mode:
            # Acknowledge a step that was waiting for user confirmation
            if not step_name:
                error_output = {
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "message": "Step parameter is required for acknowledgment",
                    "data": {}
                }
                if api_mode_flag:
                    print(json.dumps(error_output))
                else:
                    print("Error: Step parameter is required for acknowledgment")
                return error_output
            
            # Call the acknowledge_step method
            if api_mode_flag:
                # When in API mode, capture stdout and return JSON
                try:
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, "w", encoding="utf-8")
                    ack_result = agent.acknowledge_step(step_name)
                    
                    output = {
                        "pipeline_id": pipeline_id,
                        "status": ack_result["status"],
                        "message": ack_result["message"],
                        "step": step_name
                    }
                finally:
                    if "original_stdout" in locals():
                        sys.stdout = original_stdout
                        print(json.dumps(output))
            else:
                # Human-readable output
                ack_result = agent.acknowledge_step(step_name)
                status_emoji = "✅" if ack_result["status"] == "success" else "❌"
                print(f"{status_emoji} Step '{step_name}' acknowledgment: {ack_result['status']}")
                print(f"Message: {ack_result['message']}")
                
                output = {
                    "pipeline_id": pipeline_id,
                    "status": ack_result["status"],
                    "message": ack_result["message"],
                    "step": step_name
                }
            
            return output
            
        elif mode == "full":e PipelineAgent.
Demonstrates how to use the agent in a client application.
"""

import argparse
import json
import os
import sys
import importlib.util
import traceback

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the agent module and PipelineAgent directly
agent_path = os.path.join(project_root, "agent", "agent.py")
spec = importlib.util.spec_from_file_location("agent_module", agent_path)
agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_module)
PipelineAgent = agent_module.PipelineAgent

def main():
    parser = argparse.ArgumentParser(description="Run the pipeline agent")
    parser.add_argument("--mode", choices=["full", "step"], default="step",
                        help="Run full pipeline or step-by-step")
    parser.add_argument("--step", type=str, 
                        help="Specific step to run or acknowledge (depending on mode)")
    parser.add_argument("--api-url", type=str, default="http://localhost:4000",
                        help="Backend API URL")
    parser.add_argument("--pipeline-id", type=str, default=None,
                        help="ID of an existing pipeline to update")
    parser.add_argument("--api-mode", action="store_true",
                        help="When enabled, output is JSON formatted for API consumption")
    parser.add_argument("--acknowledge", action="store_true",
                        help="Acknowledge a step that was waiting for user confirmation")
    args = parser.parse_args()
    
    api_url = args.api_url
    step_name = args.step
    mode = args.mode
    api_mode_flag = args.api_mode
    
    # Set pipeline ID if provided
    if args.pipeline_id:
        setattr(sys, "pipeline_id", args.pipeline_id)
    
    # Create agent instance
    agent = PipelineAgent(api_url=api_url)
    
    # Register pipeline
    pipeline_id = agent.register_pipeline()
    
    output = {}
    try:
        if args.acknowledge:
            # Acknowledge a step that was waiting for user confirmation
            if not step_name:
                error_output = {
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "message": "Step parameter is required for acknowledgment",
                    "data": {}
                }
                if api_mode_flag:
                    print(json.dumps(error_output))
                else:
                    print("Error: Step parameter is required for acknowledgment")
                return error_output
            
            # Call the acknowledge_step method
            if api_mode_flag:
                # When in API mode, capture stdout and return JSON
                try:
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, "w", encoding="utf-8")
                    result = agent.acknowledge_step(step_name)
                    
                    output = {
                        "pipeline_id": pipeline_id,
                        "status": result["status"],
                        "message": result["message"],
                        "step": step_name
                    }
                finally:
                    if "original_stdout" in locals():
                        sys.stdout = original_stdout
                        print(json.dumps(output))
            else:
                # Human-readable output
                result = agent.acknowledge_step(step_name)
                status_emoji = "✅" if result["status"] == "success" else "❌"
                print(f"{status_emoji} Step '{step_name}' acknowledgment: {result['status']}")
                print(f"Message: {result['message']}")
                
                output = {
                    "pipeline_id": pipeline_id,
                    "status": result["status"],
                    "message": result["message"],
                    "step": step_name
                }
            
            return output
        
        if mode == "full":
            # Run all steps
            if api_mode_flag:
                # When in API mode, capture stdout and return JSON
                result = agent.execute_pipeline()
                output = {
                    "pipeline_id": pipeline_id,
                    "status": "success",
                    "message": "Pipeline execution completed",
                    "data": result
                }
            else:
                # Human-readable output
                result = agent.execute_pipeline()
                print(f"\nPipeline '{pipeline_id}' executed with result: {result['status']}")
                
                print("\nStep results:")
                for step_name, details in result["steps"].items():
                    status_emoji = "✅" if details["status"] == "success" else "❌"
                    print(f"{status_emoji} {step_name}: {details['message']}")
                
                print("\nFinal pipeline status:")
                print("✅" if result["status"] == "completed" else "❌", result["status"])
                
                output = {
                    "pipeline_id": pipeline_id,
                    "status": "success",
                    "message": "Pipeline execution completed",
                    "data": result
                }
                
        elif mode == "step":
            # Run a single step
            if not step_name:
                error_output = {
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "message": "Step parameter is required when mode=step",
                    "data": {}
                }
                if api_mode_flag:
                    print(json.dumps(error_output))
                else:
                    print("Error: Step parameter is required when mode=step")
                    print(f"Available steps: {', '.join(agent.steps)}")
                return error_output
            
            if step_name not in agent.steps:
                error_output = {
                    "pipeline_id": pipeline_id,
                    "status": "error",
                    "message": f"Unknown step: {step_name}. Available steps: {', '.join(agent.steps)}",
                    "data": {}
                }
                if api_mode_flag:
                    print(json.dumps(error_output))
                else:
                    print(f"Error: Unknown step: {step_name}")
                    print(f"Available steps: {', '.join(agent.steps)}")
                return error_output
            
            # Execute the step
            if api_mode_flag:
                # When in API mode, capture stdout and return JSON
                try:
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, "w", encoding="utf-8")
                    result = agent.execute_step(step_name)
                    # Ensure data is included and not empty
                    if not result.get("data"):
                        result["data"] = {}
                    
                    output = {
                        "pipeline_id": pipeline_id,
                        "status": result["status"],
                        "message": result["message"],
                        "data": result["data"]  # Use direct access since we ensure it exists
                    }
                finally:
                    if "original_stdout" in locals():
                        sys.stdout = original_stdout
                        print(json.dumps(output))
            else:
                # Human-readable output
                result = agent.execute_step(step_name)
                # Ensure data is included and not empty
                if not result.get("data"):
                    result["data"] = {}
                    
                status_emoji = "✅" if result["status"] == "success" else "❌"
                print(f"{status_emoji} Step '{step_name}' executed with status: {result['status']}")
                print(f"Message: {result['message']}")
                
                # Show result data if present
                if result["data"]:  # Will be at least an empty dict now
                    print("\nResult data:")
                    print(json.dumps(result["data"], indent=2))
                
                output = {
                    "pipeline_id": pipeline_id,
                    "status": result["status"],
                    "message": result["message"],
                    "data": result["data"]  # Use direct access since we ensure it exists
                }
    except Exception as e:
        error_message = str(e)
        error_output = {
            "pipeline_id": pipeline_id,
            "status": "error",
            "message": f"Error executing agent: {error_message}",
            "data": {}
        }
        if api_mode_flag:
            print(json.dumps(error_output))
        else:
            print(f"Error executing agent: {e}")
            traceback.print_exc()
        return error_output
    
    return output

if __name__ == "__main__":
    try:
        # Redirect stderr to capture logging output when in API mode
        api_mode_flag = "--api-mode" in sys.argv
        
        if api_mode_flag:
            # Capture and suppress stderr when in API mode
            stderr_backup = sys.stderr
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
        
        result = main()
    except Exception as e:
        if "api_mode_flag" in locals() and api_mode_flag and "stderr_backup" in locals():
            sys.stderr = stderr_backup
        print(json.dumps({
            "status": "error",
            "message": f"Unhandled error: {str(e)}",
            "data": {}
        }))
        traceback.print_exc()
        sys.exit(1)
    finally:
        if "api_mode_flag" in locals() and api_mode_flag and "stderr_backup" in locals():
            sys.stderr = stderr_backup
    
    # Exit with appropriate status code
    if result and result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)
