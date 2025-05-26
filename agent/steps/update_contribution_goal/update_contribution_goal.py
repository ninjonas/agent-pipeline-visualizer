import os
import json
import random
from datetime import datetime
from agent.step_base import StepBase

class UpdateContributionGoalStep(StepBase):
    """
    Implementation of the Update Contribution Goal step.
    
    This step updates existing contribution goals based on employee progress and feedback.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        self.logger.info("Executing Update Contribution Goal step")
        
        # Read original contribution goals from the create_contribution_goal step
        contribution_goals_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "create_contribution_goal",
            "out",
            "contribution_goals.json"
        )
        
        if not os.path.exists(contribution_goals_path):
            self.logger.error("Contribution goals not found. Please run create_contribution_goal step first.")
            return False
        
        # Load contribution goals
        with open(contribution_goals_path, "r") as f:
            original_goals = json.load(f)
        
        # Generate progress data for each goal
        updated_goals = self._update_contribution_goals(original_goals)
        
        # Write updated contribution goals to output
        self.write_output_file("updated_contribution_goals.json", json.dumps(updated_goals, indent=2))
        
        # Also write a markdown summary for each team member
        for member_goals in updated_goals:
            member_name = member_goals["member_name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_updated_goals.md",
                self._generate_updated_goals_markdown(member_goals)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "updated_goals_summary.md",
            self._generate_summary_markdown(updated_goals)
        )
        
        return True
    
    def _update_contribution_goals(self, original_goals):
        """Update contribution goals for each team member with progress data"""
        updated_goals = []
        
        for goals in original_goals:
            member_id = goals["member_id"]
            member_name = goals["member_name"]
            role = goals["role"]
            
            # Update quarterly goals with progress
            updated_quarterly_goals = []
            for goal in goals["quarterly_goals"]:
                progress = random.randint(30, 90)
                status = "In Progress"
                if progress < 40:
                    status = "At Risk"
                elif progress >= 80:
                    status = "On Track"
                
                updated_goal = goal.copy()
                updated_goal.update({
                    "progress": progress,
                    "status": status,
                    "comments": self._generate_progress_comment(goal["title"], progress),
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                })
                updated_quarterly_goals.append(updated_goal)
            
            # Update key results with progress
            updated_key_results = []
            for kr in goals["key_results"]:
                progress = random.randint(25, 95)
                status = "In Progress"
                if progress < 40:
                    status = "At Risk"
                elif progress >= 80:
                    status = "On Track"
                
                updated_kr = kr.copy()
                updated_kr.update({
                    "progress": progress,
                    "status": status,
                    "comments": self._generate_progress_comment(kr["title"], progress),
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                })
                updated_key_results.append(updated_kr)
            
            # Create the updated goals
            updated_goals.append({
                "member_id": member_id,
                "member_name": member_name,
                "role": role,
                "quarterly_goals": updated_quarterly_goals,
                "key_results": updated_key_results,
                "development_focus": goals["development_focus"],
                "adjustment_needed": self._determine_if_adjustment_needed(updated_quarterly_goals),
                "adjustment_recommendations": self._generate_adjustment_recommendations(updated_quarterly_goals, role)
            })
        
        return updated_goals
    
    def _generate_progress_comment(self, title, progress):
        """Generate a comment based on the progress of a goal or key result"""
        if progress < 40:
            comments = [
                f"Progress on {title} is slower than expected. Additional support may be needed.",
                f"Facing challenges with {title}. Consider adjusting timeline or scope.",
                f"Encountering obstacles with {title}. Recommend scheduled check-in to discuss blockers."
            ]
        elif progress < 70:
            comments = [
                f"Making steady progress on {title}. On track to meet target with continued focus.",
                f"Progress on {title} is good but there's room for improvement.",
                f"Moving forward with {title} at expected pace. No adjustments needed at this time."
            ]
        else:
            comments = [
                f"Excellent progress on {title}. Exceeding expectations in this area.",
                f"Strong advancement toward completion of {title}. Consider expanding scope if appropriate.",
                f"Nearly complete with {title}. Ready to plan next steps or related goals."
            ]
        return random.choice(comments)
    
    def _determine_if_adjustment_needed(self, quarterly_goals):
        """Determine if goals need adjustment based on progress"""
        at_risk_goals = [g for g in quarterly_goals if g["status"] == "At Risk"]
        return len(at_risk_goals) > 0
    
    def _generate_adjustment_recommendations(self, quarterly_goals, role):
        """Generate recommendations for goal adjustments if needed"""
        at_risk_goals = [g for g in quarterly_goals if g["status"] == "At Risk"]
        
        if not at_risk_goals:
            return []
        
        recommendations = []
        for goal in at_risk_goals:
            recommendations.append({
                "goal_title": goal["title"],
                "current_progress": goal["progress"],
                "recommendation_type": random.choice(["Scope Adjustment", "Timeline Extension", "Resource Addition"]),
                "recommendation_details": self._generate_recommendation_details(goal, role),
                "impact_assessment": "This adjustment will help maintain momentum while ensuring the essence of the goal is still achieved."
            })
        
        return recommendations
    
    def _generate_recommendation_details(self, goal, role):
        """Generate specific recommendation details based on the goal and role"""
        if "Code Quality" in goal["title"] and role == "Software Engineer":
            return "Reduce the scope to focus on code quality for critical components only, rather than all projects."
        elif "User Experience" in goal["title"] and role == "UX Designer":
            return "Extend the timeline by one month to allow for more comprehensive user testing."
        elif "Product Strategy" in goal["title"] and role == "Product Manager":
            return "Add support from the senior product manager to help accelerate progress."
        elif "Data Model" in goal["title"] and role == "Data Scientist":
            return "Focus on the most impactful data models first, deferring secondary models to next quarter."
        elif "Infrastructure" in goal["title"] and role == "DevOps Engineer":
            return "Request temporary assistance from another DevOps engineer to overcome current blockers."
        else:
            return f"Consider breaking down the goal into smaller milestones to make progress more manageable."
    
    def _generate_updated_goals_markdown(self, goals):
        """Generate a markdown report of the updated goals for a team member"""
        member_name = goals["member_name"]
        role = goals["role"]
        
        markdown = f"# Updated Contribution Goals for {member_name}\n\n"
        markdown += f"**Role:** {role}\n\n"
        
        markdown += "## Quarterly Goals Progress\n\n"
        for goal in goals["quarterly_goals"]:
            markdown += f"### {goal['title']} - {goal['status']} ({goal['progress']}%)\n\n"
            markdown += f"**Description:** {goal['description']}\n\n"
            markdown += f"**Target:** {goal['target']}\n\n"
            markdown += f"**Comments:** {goal['comments']}\n\n"
            markdown += f"**Last Updated:** {goal['last_updated']}\n\n"
        
        markdown += "## Key Results Progress\n\n"
        for kr in goals["key_results"]:
            markdown += f"### {kr['title']} - {kr['status']} ({kr['progress']}%)\n\n"
            markdown += f"**Metric:** {kr['metric']}\n\n"
            markdown += f"**Target:** {kr['target']}\n\n"
            markdown += f"**Comments:** {kr['comments']}\n\n"
            markdown += f"**Last Updated:** {kr['last_updated']}\n\n"
        
        if goals["adjustment_needed"]:
            markdown += "## Recommended Adjustments\n\n"
            for rec in goals["adjustment_recommendations"]:
                markdown += f"### {rec['goal_title']} - {rec['recommendation_type']}\n\n"
                markdown += f"**Current Progress:** {rec['current_progress']}%\n\n"
                markdown += f"**Recommendation:** {rec['recommendation_details']}\n\n"
                markdown += f"**Impact Assessment:** {rec['impact_assessment']}\n\n"
        
        return markdown
    
    def _generate_summary_markdown(self, updated_goals):
        """Generate a summary markdown report of all updated goals"""
        markdown = "# Contribution Goals Update Summary\n\n"
        
        markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        markdown += f"**Number of Team Members:** {len(updated_goals)}\n\n"
        
        # Overall progress statistics
        all_goals = []
        for member_goals in updated_goals:
            all_goals.extend(member_goals["quarterly_goals"])
        
        on_track = len([g for g in all_goals if g["status"] == "On Track"])
        in_progress = len([g for g in all_goals if g["status"] == "In Progress"])
        at_risk = len([g for g in all_goals if g["status"] == "At Risk"])
        total = len(all_goals)
        
        markdown += "## Overall Progress\n\n"
        markdown += f"- **On Track:** {on_track} ({int(on_track/total*100)}%)\n"
        markdown += f"- **In Progress:** {in_progress} ({int(in_progress/total*100)}%)\n"
        markdown += f"- **At Risk:** {at_risk} ({int(at_risk/total*100)}%)\n\n"
        
        # Team member summaries
        markdown += "## Team Member Summaries\n\n"
        for goals in updated_goals:
            member_name = goals["member_name"]
            role = goals["role"]
            
            member_goals = goals["quarterly_goals"]
            member_on_track = len([g for g in member_goals if g["status"] == "On Track"])
            member_in_progress = len([g for g in member_goals if g["status"] == "In Progress"])
            member_at_risk = len([g for g in member_goals if g["status"] == "At Risk"])
            
            markdown += f"### {member_name} ({role})\n\n"
            markdown += f"- **Goals On Track:** {member_on_track}\n"
            markdown += f"- **Goals In Progress:** {member_in_progress}\n"
            markdown += f"- **Goals At Risk:** {member_at_risk}\n"
            markdown += f"- **Adjustment Needed:** {'Yes' if goals['adjustment_needed'] else 'No'}\n\n"
        
        return markdown
