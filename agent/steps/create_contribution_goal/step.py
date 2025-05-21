from agent.steps.step_interface import PipelineStep, create_result

class Step(PipelineStep):
    """Step implementation for creating a contribution goal."""
    
    def requires_acknowledgment(self) -> bool:
        """This step requires user acknowledgment before proceeding."""
        return True
    
    def execute(self):
        """Logic for creating a contribution goal."""
        # Generate the contribution goal data (simulated)
        goal_data = {
            "title": "Improve Code Quality Metrics",
            "description": "Implement better linting, increase test coverage, and reduce technical debt.",
            "metrics": {
                "test_coverage": "Increase from 65% to 80%",
                "linting_errors": "Reduce by 50%",
                "code_complexity": "Reduce average cyclomatic complexity by 15%"
            },
            "estimated_time": "2 weeks"
        }
        
        # Return the result with requires_acknowledgment=True
        return create_result(
            status="success",
            message="Contribution goal created. Please review and acknowledge to continue.",
            data={"goal": goal_data},
            requires_acknowledgment=True
        )

# For backward compatibility with function-based approach
def execute():
    """Legacy function-based implementation."""
    step = Step()
    return step.execute()
