"""Registry of all step classes."""

# Import all step classes
from agent.steps.data_analysis.data_analysis import DataAnalysisStep
from agent.steps.evaluation_generation.evaluation_generation import EvaluationGenerationStep
from agent.steps.create_contribution_goal.create_contribution_goal import CreateContributionGoalStep
from agent.steps.create_development_item.create_development_item import CreateDevelopmentItemStep
from agent.steps.update_contribution_goal.update_contribution_goal import UpdateContributionGoalStep
from agent.steps.update_development_item.update_development_item import UpdateDevelopmentItemStep
from agent.steps.timely_feedback.timely_feedback import TimelyFeedbackStep
from agent.steps.coaching.coaching import CoachingStep

# Define a registry of all step classes
STEP_REGISTRY = {
    "data_analysis": DataAnalysisStep,
    "evaluation_generation": EvaluationGenerationStep,
    "create_contribution_goal": CreateContributionGoalStep,
    "create_development_item": CreateDevelopmentItemStep,
    "update_contribution_goal": UpdateContributionGoalStep,
    "update_development_item": UpdateDevelopmentItemStep,
    "timely_feedback": TimelyFeedbackStep,
    "coaching": CoachingStep
}

def get_step_class(step_id):
    """Get a step class by ID."""
    return STEP_REGISTRY.get(step_id)
