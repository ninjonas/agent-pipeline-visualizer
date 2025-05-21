from agent.steps.step_interface import PipelineStep, create_result

class Step(PipelineStep):
    """Step implementation for evaluation generation."""
    
    def requires_acknowledgment(self) -> bool:
        """This step requires user acknowledgment before proceeding."""
        return True
    
    def execute(self):
        """Logic for the evaluation generation step."""
        # Generate the evaluation data (simulated)
        evaluation_data = {
            "overall_score": 85,
            "strengths": ["Communication", "Problem solving", "Technical skills"],
            "areas_for_improvement": ["Time management", "Documentation"],
            "recommendations": "Focus on improving documentation practices and time management."
        }
        
        # Return the result with requires_acknowledgment=True
        return create_result(
            status="success",
            message="Evaluation generated and ready for review. Please acknowledge to continue.",
            data={"evaluation": evaluation_data},
            requires_acknowledgment=True
        )

# For backward compatibility with function-based approach
def execute():
    """Legacy function-based implementation."""
    step = Step()
    return step.execute()
