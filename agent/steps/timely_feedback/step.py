from agent.steps.step_interface import PipelineStep, create_result

class Step(PipelineStep):
    """Step implementation for providing timely feedback."""
    
    def requires_acknowledgment(self) -> bool:
        """This step requires user acknowledgment before proceeding."""
        return True
    
    def execute(self):
        """Logic for providing timely feedback."""
        # Generate the feedback data (simulated)
        feedback_data = {
            "feedback_points": [
                {
                    "category": "Technical Skills",
                    "observation": "Strong understanding of system architecture",
                    "suggestion": "Share knowledge with junior team members"
                },
                {
                    "category": "Communication",
                    "observation": "Clear documentation in recent pull requests",
                    "suggestion": "Continue this practice and consider mentoring others"
                },
                {
                    "category": "Time Management",
                    "observation": "Meeting deadlines consistently",
                    "suggestion": "Consider taking on more complex tasks"
                }
            ],
            "summary": "Overall excellent performance with opportunities to grow into a leadership role",
            "next_steps": "Schedule a follow-up discussion to set specific growth targets"
        }
        
        # Return the result with requires_acknowledgment=True
        return create_result(
            status="success",
            message="Timely feedback prepared. Please review and acknowledge to continue.",
            data={"feedback": feedback_data},
            requires_acknowledgment=True
        )

# For backward compatibility with function-based approach
def execute():
    """Legacy function-based implementation."""
    step = Step()
    return step.execute()
