import os
import json
from agent.step_base import StepBase
from loguru import logger

class CreateContributionGoalStep(StepBase):
    """
    Implementation of the Create Contribution Goal step.
    
    This step creates specific, measurable contribution goals for team members based on performance data.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        logger.info("Executing Create Contribution Goal step")
        
        # Read evaluations from previous step
        evaluations_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "evaluation_generation",
            "out",
            "evaluations.json"
        )
        
        if not os.path.exists(evaluations_path):
            logger.error("Evaluations not found. Please run evaluation_generation step first.")
            return False
        
        # Load evaluations
        with open(evaluations_path, "r", encoding="utf-8") as f:
            evaluations = json.load(f)
        
        # Generate contribution goals
        contribution_goals = self._generate_contribution_goals(evaluations)
        
        # Write contribution goals to output
        self.write_output_file("contribution_goals.json", json.dumps(contribution_goals, indent=2))
        
        # Also write a markdown summary for each team member
        for member_goals in contribution_goals:
            member_name = member_goals["member_name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_goals.md",
                self._generate_goals_markdown(member_goals)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "contribution_goals_summary.md",
            self._generate_summary_markdown(contribution_goals)
        )
        
        return True
    
    def _generate_contribution_goals(self, evaluations):
        """Generate contribution goals for each team member"""
        contribution_goals = []
        
        for evaluation in evaluations:
            member_id = evaluation["member_id"]
            member_name = evaluation["member_name"]
            role = evaluation["role"]
            
            # Generate the contribution goals
            goals = {
                "member_id": member_id,
                "member_name": member_name,
                "role": role,
                "quarterly_goals": self._generate_quarterly_goals(evaluation),
                "key_results": self._generate_key_results(evaluation),
                "development_focus": self._get_development_focus(evaluation)
            }
            
            contribution_goals.append(goals)
        
        return contribution_goals
    
    def _generate_quarterly_goals(self, evaluation):
        """Generate quarterly goals based on the evaluation"""
        quarterly_goals = []
        role = evaluation["role"]
        strengths = evaluation["strengths"]
        improvement_areas = evaluation["improvement_areas"]
        
        # Goal 1: Role-specific goal
        if role == "Software Engineer":
            quarterly_goals.append({
                "title": "Code Quality Improvement",
                "description": "Improve code quality metrics across assigned projects",
                "target": "Achieve code quality score of 85% or higher on all new code"
            })
        elif role == "UX Designer":
            quarterly_goals.append({
                "title": "User Experience Enhancement",
                "description": "Enhance user experience for key product features",
                "target": "Improve user satisfaction ratings by 15% for redesigned features"
            })
        elif role == "Product Manager":
            quarterly_goals.append({
                "title": "Feature Delivery Optimization",
                "description": "Optimize feature delivery process to improve time-to-market",
                "target": "Reduce average feature delivery time by 20%"
            })
        elif role == "Data Scientist":
            quarterly_goals.append({
                "title": "Data Model Improvement",
                "description": "Improve accuracy and performance of data models",
                "target": "Increase model accuracy by 10% while maintaining or improving inference speed"
            })
        elif role == "DevOps Engineer":
            quarterly_goals.append({
                "title": "Infrastructure Reliability",
                "description": "Enhance infrastructure reliability and performance",
                "target": "Reduce system downtime by 25% and improve response time by 15%"
            })
        else:
            quarterly_goals.append({
                "title": "Professional Growth",
                "description": "Focus on professional growth and skill development",
                "target": "Acquire at least two new relevant skills or certifications"
            })
        
        # Goal 2: Strength-based goal
        if strengths:
            top_strength = strengths[0]
            if top_strength == "code_quality":
                quarterly_goals.append({
                    "title": "Code Quality Leadership",
                    "description": "Lead initiatives to improve team-wide code quality",
                    "target": "Implement at least 3 team-wide code quality improvements"
                })
            elif top_strength == "productivity":
                quarterly_goals.append({
                    "title": "Productivity Optimization",
                    "description": "Optimize workflows and processes to improve team productivity",
                    "target": "Implement at least 2 workflow improvements that save 5+ hours per week"
                })
            elif top_strength == "collaboration":
                quarterly_goals.append({
                    "title": "Cross-team Collaboration",
                    "description": "Strengthen cross-team collaboration on key projects",
                    "target": "Successfully lead at least 2 cross-team initiatives"
                })
            elif top_strength == "innovation":
                quarterly_goals.append({
                    "title": "Innovation Leadership",
                    "description": "Lead innovation initiatives to solve key challenges",
                    "target": "Propose and implement at least 2 innovative solutions to existing problems"
                })
            elif top_strength == "reliability":
                quarterly_goals.append({
                    "title": "Reliability Improvement",
                    "description": "Improve system or process reliability",
                    "target": "Reduce failure rate by 30% in assigned areas of responsibility"
                })
            elif top_strength == "customer_focus":
                quarterly_goals.append({
                    "title": "Customer Satisfaction",
                    "description": "Drive improvements in customer satisfaction",
                    "target": "Increase customer satisfaction score by 15% for key features"
                })
        
        # Goal 3: Improvement-focused goal
        if improvement_areas:
            top_improvement = improvement_areas[0]
            if top_improvement == "code_quality":
                quarterly_goals.append({
                    "title": "Code Quality Improvement",
                    "description": "Improve personal code quality metrics",
                    "target": "Reduce code review feedback by 50% through improved initial submissions"
                })
            elif top_improvement == "productivity":
                quarterly_goals.append({
                    "title": "Productivity Enhancement",
                    "description": "Enhance personal productivity through improved practices",
                    "target": "Increase task completion rate by 25%"
                })
            elif top_improvement == "collaboration":
                quarterly_goals.append({
                    "title": "Team Collaboration",
                    "description": "Strengthen collaboration with team members",
                    "target": "Actively participate in at least 3 collaborative projects"
                })
            elif top_improvement == "innovation":
                quarterly_goals.append({
                    "title": "Innovation Development",
                    "description": "Develop innovation skills through structured exploration",
                    "target": "Submit at least 3 innovative ideas and implement at least 1"
                })
            elif top_improvement == "reliability":
                quarterly_goals.append({
                    "title": "Work Reliability",
                    "description": "Improve reliability of work and commitments",
                    "target": "Meet 95% of commitments on time"
                })
            elif top_improvement == "customer_focus":
                quarterly_goals.append({
                    "title": "Customer Understanding",
                    "description": "Deepen understanding of customer needs",
                    "target": "Participate in at least 5 customer interviews or feedback sessions"
                })
        
        return quarterly_goals
    
    def _generate_key_results(self, evaluation):
        """Generate key results based on the evaluation"""
        key_results = []
        
        # Project-specific key results
        for project in evaluation["projects"]:
            if "Portal" in project:
                key_results.append({
                    "title": f"{project} Enhancement",
                    "description": "Successfully deliver enhancements to improve user experience",
                    "measure": "Positive user feedback and 10% increase in engagement metrics"
                })
            elif "API" in project:
                key_results.append({
                    "title": f"{project} Optimization",
                    "description": "Optimize API performance and reliability",
                    "measure": "30% reduction in API response time and 99.9% uptime"
                })
            elif "App" in project:
                key_results.append({
                    "title": f"{project} Development",
                    "description": "Successful development and deployment",
                    "measure": "On-time delivery with fewer than 5 critical bugs"
                })
            elif "Data" in project:
                key_results.append({
                    "title": f"{project} Implementation",
                    "description": "Successfully implement data pipeline improvements",
                    "measure": "50% improvement in data processing time and 99% accuracy"
                })
            elif "Cloud" in project:
                key_results.append({
                    "title": f"{project} Completion",
                    "description": "Complete cloud migration with minimal disruption",
                    "measure": "Zero downtime during migration and 20% cost reduction"
                })
            else:
                key_results.append({
                    "title": f"{project} Delivery",
                    "description": "Successfully deliver project milestones",
                    "measure": "On-time delivery of all key milestones"
                })
        
        # Role-specific key results
        role = evaluation["role"]
        if role == "Software Engineer":
            key_results.append({
                "title": "Code Quality",
                "description": "Maintain high code quality standards",
                "measure": "90% code coverage and fewer than 3 bugs per release"
            })
        elif role == "UX Designer":
            key_results.append({
                "title": "Design System",
                "description": "Contribute to the design system",
                "measure": "Add at least 5 new components to the design system"
            })
        elif role == "Product Manager":
            key_results.append({
                "title": "Feature Adoption",
                "description": "Drive adoption of new features",
                "measure": "Achieve 40% adoption rate for new features within first month"
            })
        elif role == "Data Scientist":
            key_results.append({
                "title": "Model Accuracy",
                "description": "Improve model accuracy",
                "measure": "Increase model accuracy by 15% over current baseline"
            })
        elif role == "DevOps Engineer":
            key_results.append({
                "title": "Deployment Frequency",
                "description": "Increase deployment frequency",
                "measure": "Enable daily deployments with 99% success rate"
            })
        
        # Add one more generic result
        key_results.append({
            "title": "Professional Development",
            "description": "Continuous learning and skill development",
            "measure": "Complete at least 2 relevant courses or certifications"
        })
        
        return key_results
    
    def _get_development_focus(self, evaluation):
        """Determine development focus areas based on evaluation"""
        development_focus = []
        
        # Add focus areas based on improvement areas
        for area in evaluation["improvement_areas"]:
            if area == "code_quality":
                development_focus.append({
                    "area": "Technical Excellence",
                    "description": "Focus on improving code quality, testing, and best practices",
                    "success_criteria": "Consistently high code review ratings with minimal rework"
                })
            elif area == "productivity":
                development_focus.append({
                    "area": "Efficiency",
                    "description": "Improve work efficiency and output",
                    "success_criteria": "Consistent delivery of high-quality work on schedule"
                })
            elif area == "collaboration":
                development_focus.append({
                    "area": "Teamwork",
                    "description": "Enhance collaboration and communication with team members",
                    "success_criteria": "Positive feedback from team members on collaboration"
                })
            elif area == "innovation":
                development_focus.append({
                    "area": "Creative Problem-Solving",
                    "description": "Develop creative approaches to solving challenges",
                    "success_criteria": "Implementation of at least 2 innovative solutions"
                })
            elif area == "reliability":
                development_focus.append({
                    "area": "Dependability",
                    "description": "Improve reliability and consistency of work",
                    "success_criteria": "Meeting 95% of commitments on time with high quality"
                })
            elif area == "customer_focus":
                development_focus.append({
                    "area": "Customer Orientation",
                    "description": "Strengthen understanding of and focus on customer needs",
                    "success_criteria": "Customer feedback incorporated into all deliverables"
                })
        
        # Add one career development focus
        role = evaluation["role"]
        if role == "Software Engineer":
            development_focus.append({
                "area": "Technical Leadership",
                "description": "Develop technical leadership skills",
                "success_criteria": "Successfully lead at least one technical initiative"
            })
        elif role == "UX Designer":
            development_focus.append({
                "area": "Design Innovation",
                "description": "Explore innovative design approaches",
                "success_criteria": "Implementation of at least one innovative design concept"
            })
        elif role == "Product Manager":
            development_focus.append({
                "area": "Strategic Thinking",
                "description": "Develop strategic product thinking",
                "success_criteria": "Create a compelling long-term vision for assigned product area"
            })
        elif role == "Data Scientist":
            development_focus.append({
                "area": "Advanced Analytics",
                "description": "Expand knowledge of advanced analytics techniques",
                "success_criteria": "Successfully apply at least one new advanced technique"
            })
        elif role == "DevOps Engineer":
            development_focus.append({
                "area": "Infrastructure Innovation",
                "description": "Explore innovative infrastructure solutions",
                "success_criteria": "Implement at least one infrastructure improvement"
            })
        else:
            development_focus.append({
                "area": "Professional Growth",
                "description": "Focus on professional development in key skill areas",
                "success_criteria": "Acquisition of at least two new relevant skills"
            })
        
        return development_focus
    
    def _generate_goals_markdown(self, goals):
        """Generate a markdown summary of contribution goals for a team member"""
        markdown = f"# Contribution Goals: {goals['member_name']}\n\n"
        markdown += f"**Role:** {goals['role']}\n\n"
        
        markdown += "## Quarterly Goals\n\n"
        for i, goal in enumerate(goals["quarterly_goals"], 1):
            markdown += f"### Goal {i}: {goal['title']}\n\n"
            markdown += f"**Description:** {goal['description']}\n\n"
            markdown += f"**Target:** {goal['target']}\n\n"
        
        markdown += "## Key Results\n\n"
        for i, result in enumerate(goals["key_results"], 1):
            markdown += f"### KR {i}: {result['title']}\n\n"
            markdown += f"**Description:** {result['description']}\n\n"
            markdown += f"**Measure:** {result['measure']}\n\n"
        
        markdown += "## Development Focus\n\n"
        for i, focus in enumerate(goals["development_focus"], 1):
            markdown += f"### Focus {i}: {focus['area']}\n\n"
            markdown += f"**Description:** {focus['description']}\n\n"
            markdown += f"**Success Criteria:** {focus['success_criteria']}\n\n"
        
        return markdown
    
    def _generate_summary_markdown(self, all_goals):
        """Generate a summary markdown for all contribution goals"""
        markdown = "# Team Contribution Goals Summary\n\n"
        
        markdown += "## Overview\n\n"
        markdown += f"This document summarizes the contribution goals for {len(all_goals)} team members.\n\n"
        
        markdown += "## Team Members and Goals\n\n"
        markdown += "| Team Member | Role | Primary Goals |\n"
        markdown += "|------------|------|---------------|\n"
        
        for member_goals in all_goals:
            name = member_goals["member_name"]
            role = member_goals["role"]
            
            primary_goals = ", ".join([goal["title"] for goal in member_goals["quarterly_goals"]])
            
            markdown += f"| {name} | {role} | {primary_goals} |\n"
        
        markdown += "\n## Key Development Focus Areas\n\n"
        
        # Collect all development focus areas
        focus_areas = {}
        for member_goals in all_goals:
            for focus in member_goals["development_focus"]:
                area = focus["area"]
                if area in focus_areas:
                    focus_areas[area] += 1
                else:
                    focus_areas[area] = 1
        
        # Sort by frequency
        sorted_areas = sorted(focus_areas.items(), key=lambda x: x[1], reverse=True)
        
        for area, count in sorted_areas:
            markdown += f"- **{area}**: {count} team members\n"
        
        return markdown
