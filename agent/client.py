#!/usr/bin/env python3
"""
Client script to interact with the PipelineAgent.
Demonstrates how to use the agent in a client application.
"""

import argparse
import json
import time
import os
import sys

# Ensure the parent directory is in the Python path so 'agent' can be imported as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import the PipelineAgent
from agent import PipelineAgent

def main():
    parser = argparse.ArgumentParser(description="Run the pipeline agent")
    parser.add_argument("--mode", choices=["full", "step"], default="step",
                        help="Run full pipeline or step-by-step")
    parser.add_argument("--step", type=str, 
                        help="Specific step to run (only with --mode=step)")
    parser.add_argument("--api-url", type=str, default="http://localhost:4000",
                        help="Backend API URL")
    parser.add_argument("--pipeline-id", type=str,
                        help="Use an existing pipeline ID instead of creating a new one")
    
    args = parser.parse_args()
    
    # Ensure API URL has correct format
    api_url = args.api_url
    if api_url and not api_url.startswith(("http://", "https://")):
        api_url = f"http://{api_url}"
    
    # Initialize the agent
    agent = PipelineAgent(api_url=api_url)
    
    # Use provided pipeline ID or register a new one
    api_mode = os.environ.get("AGENT_API_MODE") == "1"
    
    if args.pipeline_id:
        # Store pipeline_id in the sys module so the fallback agent can access it
        sys.pipeline_id = args.pipeline_id
        agent.pipeline_id = args.pipeline_id
        if not api_mode:
            print(f"Using existing pipeline ID: {agent.pipeline_id}")
    else:
        agent.register_pipeline()
        if not api_mode:
            print(f"Initialized agent with pipeline ID: {agent.pipeline_id}")
    
    if args.mode == "full":
        # Execute the entire pipeline
        print("Executing full pipeline...")
        results = agent.execute_pipeline()
        print("\nPipeline execution completed!")
        print(f"Final status: {results['status']}")
        print("\nStep details:")
        
        for step, details in results["steps"].items():
            status_emoji = "✅" if details["status"] == "success" else "❌"
            print(f"{status_emoji} {step}: {details['message']}")
            
    elif args.mode == "step":
        if args.step:
            # Execute a specific step
            if args.step in agent.steps:
                # For API integration, we need clean JSON output
                # Check if we're being called from the API
                api_mode = args.pipeline_id or os.environ.get("AGENT_API_MODE") == "1"
                
                if api_mode:  # If we're being called from the API
                    # For API usage, we need a completely clean JSON output with no debugging info
                    
                    # Suppress all initialization output by redirecting stdout
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, 'w')
                    
                    try:
                        # Use a special function that handles all the redirection and cleanup
                        output = api_step_execution(agent, args.step)
                        
                        # Restore stdout and print ONLY the clean JSON output
                        sys.stdout = original_stdout
                        # Print only the JSON, nothing else - this is critical
                        print(json.dumps(output))
                    except Exception as e:
                        # Ensure we restore stdout even if there's an error
                        sys.stdout = original_stdout
                        print(json.dumps({
                            "status": "error",
                            "message": f"Error: {str(e)}",
                            "data": {}
                        }))
                else:  # Interactive mode with human-readable output
                    print(f"Executing step: {args.step}")
                    result = agent.execute_step(args.step)
                    print(f"Step result: {result['status']}")
                    print(f"Message: {result.get('message', '')}")
                    if 'data' in result:
                        print("Data:")
                        print(json.dumps(result['data'], indent=2))
            else:
                # If step not found and in API mode, ensure clean JSON output
                if api_mode:
                    error_output = {
                        "status": "error",
                        "message": f"Unknown step: {args.step}. Available steps: {', '.join(agent.steps)}"
                    }
                    # Ensure we're only outputting clean JSON for API
                    print(json.dumps(error_output), flush=True)
                else:
                    print(f"Error: Unknown step '{args.step}'")
                    print(f"Available steps: {', '.join(agent.steps)}")
        else:
            # Interactive mode - go through steps one by one
            print("Step-by-step execution mode. Press Enter to execute each step...")
            
            for step in agent.steps:
                input(f"Press Enter to execute '{step}'...")
                result = agent.execute_step(step)
                status_emoji = "✅" if result["status"] == "success" else "❌"
                print(f"{status_emoji} {step}: {result['message']}")
                
                # Display current progress
                status = agent.get_pipeline_status()
                completed = sum(1 for s in status["steps"].values() if s == "completed")
                print(f"Progress: {completed}/{len(agent.steps)} steps completed")
                print("-" * 40)
                
    # Final status - only show this in interactive mode, not API mode
    api_mode = os.environ.get("AGENT_API_MODE") == "1"
    if not api_mode:
        status = agent.get_pipeline_status()
        print("\nFinal pipeline status:")
        print(json.dumps(status, indent=2))

def api_step_execution(agent, step):
    """Execute a step purely for API consumption with clean output"""
    try:
        # Clear stdout buffer before we start
        sys.stdout.flush()
        
        result = agent.execute_step(step)
        output = {
            "status": result["status"],
            "message": result.get("message", f"Executed {step}"),
            "data": result.get("data", {})
        }
        return output
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error executing {step}: {str(e)}",
            "data": {}
        }

if __name__ == "__main__":
    # For API mode, catch all exceptions to ensure clean JSON output
    if os.environ.get('AGENT_API_MODE') == '1':
        try:
            # Temporarily redirect stderr to avoid polluting output
            stderr_backup = sys.stderr
            sys.stderr = open(os.devnull, 'w')
            
            try:
                main()
            finally:
                # Restore stderr
                sys.stderr.close()
                sys.stderr = stderr_backup
        except Exception as e:
            # Output any unexpected error as clean JSON
            error_output = {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "data": {"error_type": type(e).__name__}
            }
            # Ensure stdout is clean before printing
            sys.stdout = sys.__stdout__
            print(json.dumps(error_output))
            sys.exit(1)
    else:
        # Normal execution
        main()
