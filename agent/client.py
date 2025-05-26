# filepath: /Users/jonas/development/agent-pipeline-visualizer/agent/client.py
import os
import sys
import json
import time
import argparse
import importlib
from typing import Dict, List, Optional, Any, Union
from agent.agent_base import AgentBase

class Agent(AgentBase):
    """Agent implementation for performance evaluations and monthly check-ins"""
    
    def __init__(self, api_url: str = "http://localhost:4000"):
        super().__init__(api_url)

def main():
    parser = argparse.ArgumentParser(description="AI Agent for Performance Evaluations and Monthly Check-ins")
    parser.add_argument("--mode", choices=["step", "full"], default="step", help="Run mode: step-by-step or full pipeline")
    parser.add_argument("--step", type=str, help="Specific step to run (only in step mode)")
    parser.add_argument("--api-url", type=str, default="http://localhost:4000", help="URL of the API server")
    
    args = parser.parse_args()
    
    # Create agent
    agent = Agent(api_url=args.api_url)
    
    if args.mode == "step":
        if args.step:
            # Run specific step
            step_id = args.step
            print(f"Running step: {step_id}")
            success = agent.run_step(step_id)
            if success:
                print(f"Step '{step_id}' completed successfully")
            else:
                print(f"Step '{step_id}' failed")
                sys.exit(1)
        else:
            # Interactive step-by-step mode
            while True:
                available_steps = agent.get_available_steps()
                
                if not available_steps:
                    print("No steps available to run. All steps may be completed or waiting for dependencies.")
                    break
                
                print("\nAvailable steps:")
                for i, step_id in enumerate(available_steps):
                    step_config = agent._get_step_config(step_id)
                    if step_config:
                        step_name = step_config.get("name", step_id)
                        print(f"{i+1}. {step_name} ({step_id})")
                
                choice = input("\nSelect a step to run (number) or 'q' to quit: ")
                
                if choice.lower() == 'q':
                    break
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(available_steps):
                        step_id = available_steps[index]
                        success = agent.run_step(step_id)
                        if success:
                            print(f"Step '{step_id}' completed successfully")
                        else:
                            print(f"Step '{step_id}' failed")
                    else:
                        print("Invalid selection")
                except ValueError:
                    print("Invalid input, please enter a number or 'q'")
    
    elif args.mode == "full":
        # Run all steps
        print("Running all steps...")
        success = agent.run_all_steps()
        if success:
            print("All steps completed successfully")
        else:
            print("Some steps failed")
            sys.exit(1)

if __name__ == "__main__":
    main()
