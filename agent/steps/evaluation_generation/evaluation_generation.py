import os
import json
from agent.step_base import StepBase
from loguru import logger

class EvaluationGenerationStep(StepBase):
    """
    Implementation of the Evaluation Generation step.
    
    This step generates performance evaluations based on the analysis of data and feedback.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        logger.info("Executing Evaluation Generation step")
        
        # Read analysis results from previous step
        analysis_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "data_analysis",
            "out",
            "analysis_results.json"
        )
        
        if not os.path.exists(analysis_path):
            logger.error("Analysis results not found. Please run data_analysis step first.")
            return False
        
        # Load analysis results
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        # Also read the team data
        team_data_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "data_analysis",
            "out",
            "team_data.json"
        )
        
        if not os.path.exists(team_data_path):
            logger.error("Team data not found. Please run data_analysis step first.")
            return False
        
        # Load team data
        with open(team_data_path, "r", encoding="utf-8") as f:
            team_data = json.load(f)
        
        # Generate evaluations
        evaluations = self._generate_evaluations(analysis_data, team_data)
        
        # Write evaluations to output
        self.write_output_file("evaluations.json", json.dumps(evaluations, indent=2))
        
        # Also write a markdown summary for each team member
        for member_eval in evaluations:
            member_name = member_eval["member_name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_evaluation.md",
                self._generate_evaluation_markdown(member_eval)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "evaluation_summary.md",
            self._generate_summary_markdown(evaluations)
        )
        
        return True
    
    def _generate_evaluations(self, analysis_data, team_data):
        """Generate evaluations for each team member"""
        evaluations = []
        
        individual_analyses = analysis_data.get("individual_analysis", [])
        
        for analysis in individual_analyses:
            member_id = analysis["member_id"]
            
            # Find the team member data
            member_data = next(
                (m for m in team_data if m["member"]["id"] == member_id),
                None
            )
            
            if not member_data:
                continue
            
            # Generate the evaluation
            evaluation = {
                "member_id": member_id,
                "member_name": analysis["member_name"],
                "role": member_data["member"]["role"],
                "overall_rating": analysis["overall_rating"],
                "strengths": analysis["strengths"],
                "improvement_areas": analysis["improvement_areas"],
                "projects": member_data["projects"],
                "performance": member_data["performance"],
                "evaluation_text": self._generate_evaluation_text(analysis, member_data),
                "recommendations": self._generate_recommendations(analysis)
            }
            
            evaluations.append(evaluation)
        
        return evaluations
    
    def _generate_evaluation_text(self, analysis, member_data):
        """Generate evaluation text for a team member"""
        strengths = [s.replace("_", " ").title() for s in analysis["strengths"]]
        improvement_areas = [a.replace("_", " ").title() for a in analysis["improvement_areas"]]
        
        evaluation_text = []
        
        # Overall assessment
        if analysis["overall_rating"] >= 4.5:
            evaluation_text.append(
                f"{analysis['member_name']} has demonstrated exceptional performance this quarter, "
                f"exceeding expectations in multiple areas."
            )
        elif analysis["overall_rating"] >= 4.0:
            evaluation_text.append(
                f"{analysis['member_name']} has performed very well this quarter, "
                f"consistently meeting and often exceeding expectations."
            )
        elif analysis["overall_rating"] >= 3.5:
            evaluation_text.append(
                f"{analysis['member_name']} has performed well this quarter, "
                f"meeting expectations in most areas."
            )
        elif analysis["overall_rating"] >= 3.0:
            evaluation_text.append(
                f"{analysis['member_name']} has performed adequately this quarter, "
                f"meeting expectations in key areas but with room for improvement."
            )
        else:
            evaluation_text.append(
                f"{analysis['member_name']} has struggled to meet expectations this quarter "
                f"and requires additional support and development."
            )
        
        # Strengths
        if strengths:
            evaluation_text.append(
                f"\nParticularly notable is {analysis['member_name']}'s strength in "
                f"{', '.join(strengths[:-1]) + ' and ' + strengths[-1] if len(strengths) > 1 else strengths[0]}."
            )
            
            # Add specific comments for each strength
            for strength in strengths:
                if strength == "Code Quality":
                    evaluation_text.append(
                        f"{analysis['member_name']} consistently delivers well-structured, maintainable code "
                        "with appropriate documentation and test coverage."
                    )
                elif strength == "Productivity":
                    evaluation_text.append(
                        f"{analysis['member_name']} has demonstrated high productivity, "
                        "efficiently completing tasks and consistently meeting deadlines."
                    )
                elif strength == "Collaboration":
                    evaluation_text.append(
                        f"{analysis['member_name']} works effectively with team members, "
                        "actively participates in discussions, and provides valuable input to the team."
                    )
                elif strength == "Innovation":
                    evaluation_text.append(
                        f"{analysis['member_name']} regularly contributes innovative ideas "
                        "and approaches to solving problems."
                    )
                elif strength == "Reliability":
                    evaluation_text.append(
                        f"{analysis['member_name']} is highly reliable, consistently delivering on commitments "
                        "and maintaining high standards of work."
                    )
                elif strength == "Customer Focus":
                    evaluation_text.append(
                        f"{analysis['member_name']} demonstrates strong customer focus, "
                        "understanding user needs and delivering solutions that address those needs effectively."
                    )
        
        # Areas for improvement
        if improvement_areas:
            evaluation_text.append(
                f"\\nAreas where {analysis['member_name']} could focus on improvement include "
                f"{', '.join(improvement_areas[:-1]) + ' and ' + improvement_areas[-1] if len(improvement_areas) > 1 else improvement_areas[0]}."
            )
            
            # Add specific suggestions for each improvement area
            for area in improvement_areas:
                if area == "Code Quality":
                    evaluation_text.append(
                        "Consider investing more time in code reviews, writing unit tests, "
                        "and ensuring code is well-documented and maintainable."
                    )
                elif area == "Productivity":
                    evaluation_text.append(
                        "Focus on time management and prioritization to increase productivity. "
                        "Consider techniques like time-blocking or the Pomodoro method."
                    )
                elif area == "Collaboration":
                    evaluation_text.append(
                        "Seek more opportunities to collaborate with team members, "
                        "actively participate in discussions, and share knowledge."
                    )
                elif area == "Innovation":
                    evaluation_text.append(
                        "Challenge yourself to think creatively about problems and solutions. "
                        "Consider dedicating time to explore new technologies or approaches."
                    )
                elif area == "Reliability":
                    evaluation_text.append(
                        "Work on setting realistic expectations and consistently meeting commitments. "
                        "Communicate proactively if you anticipate challenges in meeting deadlines."
                    )
                elif area == "Customer Focus":
                    evaluation_text.append(
                        "Deepen your understanding of user needs and perspectives. "
                        "Consider participating in user research or customer interviews."
                    )
        
        # Project contributions
        if member_data["projects"]:
            evaluation_text.append(
                f"\n{analysis['member_name']} has made valuable contributions to the following projects: "
                f"{', '.join(member_data['projects'])}."
            )
        
        return "\n".join(evaluation_text)
    
    def _generate_recommendations(self, analysis):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # General recommendation
        recommendations.append(
            "Continue to leverage strengths while focusing on development areas"
        )
        
        # Strength-based recommendations
        for strength in analysis["strengths"]:
            if strength == "code_quality":
                recommendations.append(
                    "Share code quality best practices with the team through knowledge sharing sessions"
                )
            elif strength == "productivity":
                recommendations.append(
                    "Consider mentoring others on productivity techniques and strategies"
                )
            elif strength == "collaboration":
                recommendations.append(
                    "Take on more leadership opportunities in team settings"
                )
            elif strength == "innovation":
                recommendations.append(
                    "Explore innovation time to pursue new ideas or improvements"
                )
            elif strength == "reliability":
                recommendations.append(
                    "Continue building on reliability by taking on more responsibility"
                )
            elif strength == "customer_focus":
                recommendations.append(
                    "Consider participating in customer-facing activities to further leverage this strength"
                )
        
        # Improvement area recommendations
        for area in analysis["improvement_areas"]:
            if area == "code_quality":
                recommendations.append(
                    "Complete a course on software quality and testing practices"
                )
            elif area == "productivity":
                recommendations.append(
                    "Practice time management techniques and use productivity tools"
                )
            elif area == "collaboration":
                recommendations.append(
                    "Increase participation in team meetings and collaborative projects"
                )
            elif area == "innovation":
                recommendations.append(
                    "Dedicate time to exploring new technologies or approaches"
                )
            elif area == "reliability":
                recommendations.append(
                    "Develop a more structured approach to planning and tracking work"
                )
            elif area == "customer_focus":
                recommendations.append(
                    "Participate in user research or customer interviews to better understand needs"
                )
        
        return recommendations
    
    def _generate_evaluation_markdown(self, evaluation):
        """Generate a markdown evaluation for a team member"""
        markdown = f"# Performance Evaluation: {evaluation['member_name']}\n\n"
        markdown += f"**Role:** {evaluation['role']}\n"
        markdown += f"**Overall Rating:** {evaluation['overall_rating']}/5.0\n\n"
        
        markdown += "## Evaluation Summary\n\n"
        markdown += f"{evaluation['evaluation_text']}\n\n"
        
        markdown += "## Performance Metrics\n\n"
        markdown += "| Metric | Q1 | Q2 | Q3 | Trend |\n"
        markdown += "|--------|----|----|----|-----------|\n"
        
        for metric, data in evaluation['performance'].items():
            display_metric = metric.replace('_', ' ').title()
            q1 = data["Q1"]
            q2 = data["Q2"]
            q3 = data["Q3"]
            
            trend = ""
            if q3 > q2:
                trend = "↑ Improving"
            elif q3 < q2:
                trend = "↓ Declining"
            else:
                trend = "→ Stable"
            
            markdown += f"| {display_metric} | {q1} | {q2} | {q3} | {trend} |\n"
        
        markdown += "\n## Strengths\n\n"
        if evaluation["strengths"]:
            for strength in evaluation["strengths"]:
                markdown += f"- {strength.replace('_', ' ').title()}\n"
        else:
            markdown += "No specific strengths identified.\n"
        
        markdown += "\n## Areas for Improvement\n\n"
        if evaluation["improvement_areas"]:
            for area in evaluation["improvement_areas"]:
                markdown += f"- {area.replace('_', ' ').title()}\n"
        else:
            markdown += "No specific improvement areas identified.\n"
        
        markdown += "\n## Projects\n\n"
        if evaluation["projects"]:
            for project in evaluation["projects"]:
                markdown += f"- {project}\n"
        else:
            markdown += "No projects assigned during this period.\n"
        
        markdown += "\n## Recommendations\n\n"
        for recommendation in evaluation["recommendations"]:
            markdown += f"- {recommendation}\n"
        
        return markdown
    
    def _generate_summary_markdown(self, evaluations):
        """Generate a summary markdown for all evaluations"""
        markdown = "# Team Performance Evaluation Summary\n\n"
        
        markdown += "## Overview\n\n"
        
        average_rating = sum(e["overall_rating"] for e in evaluations) / len(evaluations)
        markdown += f"Team Average Rating: {average_rating:.1f}/5.0\n\n"
        
        markdown += "## Individual Ratings\n\n"
        markdown += "| Team Member | Role | Rating | Top Strength | Primary Development Area |\n"
        markdown += "|------------|------|--------|-------------|-------------------------|\\n"
        
        for eval_item in evaluations:
            name = eval_item["member_name"]
            role = eval_item["role"]
            rating = eval_item["overall_rating"]
            
            top_strength = eval_item["strengths"][0].replace("_", " ").title() if eval_item["strengths"] else "N/A"
            top_improvement = eval_item["improvement_areas"][0].replace("_", " ").title() if eval_item["improvement_areas"] else "N/A"
            
            markdown += f"| {name} | {role} | {rating} | {top_strength} | {top_improvement} |\\n"
        
        markdown += "\\n## Common Strengths\\n\\n"
        
        # Collect all strengths
        all_strengths = {}
        for eval_item in evaluations:
            for strength in eval_item["strengths"]:
                if strength in all_strengths:
                    all_strengths[strength] += 1
                else:
                    all_strengths[strength] = 1
        
        # Sort by frequency
        sorted_strengths = sorted(all_strengths.items(), key=lambda x: x[1], reverse=True)
        
        for strength, count in sorted_strengths:
            display_strength = strength.replace("_", " ").title()
            markdown += f"- {display_strength}: {count} team members\n"
        
        markdown += "\n## Common Development Areas\n\n"
        
        # Collect all improvement areas
        all_improvements = {}
        for eval_item in evaluations:
            for area in eval_item["improvement_areas"]:
                if area in all_improvements:
                    all_improvements[area] += 1
                else:
                    all_improvements[area] = 1
        
        # Sort by frequency
        sorted_improvements = sorted(all_improvements.items(), key=lambda x: x[1], reverse=True)
        
        for area, count in sorted_improvements:
            display_area = area.replace("_", " ").title()
            markdown += f"- {display_area}: {count} team members\n"
        
        return markdown
