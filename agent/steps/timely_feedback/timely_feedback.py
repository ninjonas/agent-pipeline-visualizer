import os
import json
import random
from datetime import datetime, timedelta
from agent.step_base import StepBase
from loguru import logger

class TimelyFeedbackStep(StepBase):
    """
    Implementation of the Timely Feedback step.
    
    This step generates timely feedback for team members based on recent accomplishments and behaviors.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        logger.info("Executing Timely Feedback step")
        
        # Read team data from the data_analysis step
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
        
        # Generate timely feedback
        feedback_data = self._generate_timely_feedback(team_data)
        
        # Write feedback data to output
        self.write_output_file("timely_feedback.json", json.dumps(feedback_data, indent=2))
        
        # Also write a markdown summary for each team member
        for member_feedback in feedback_data:
            member_name = member_feedback["member"]["name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_feedback.md",
                self._generate_feedback_markdown(member_feedback)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "feedback_summary.md",
            self._generate_summary_markdown(feedback_data)
        )
        
        return True
    
    def _generate_timely_feedback(self, team_data):
        """Generate timely feedback for each team member"""
        feedback_data = []
        
        for member_data in team_data:
            member = member_data["member"]
            role = member["role"]
            projects = member_data["projects"]
            
            # Generate random recent accomplishments
            accomplishments = self._generate_accomplishments(role, projects)
            
            # Generate positive and constructive feedback
            positive_feedback = self._generate_positive_feedback(role, accomplishments)
            constructive_feedback = self._generate_constructive_feedback(role)
            
            # Generate feedback data
            feedback = {
                "member": member,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "recent_accomplishments": accomplishments,
                "positive_feedback": positive_feedback,
                "constructive_feedback": constructive_feedback,
                "action_items": self._generate_action_items(constructive_feedback),
                "follow_up_date": (datetime.now() + timedelta(days=random.randint(14, 30))).strftime("%Y-%m-%d")
            }
            
            feedback_data.append(feedback)
        
        return feedback_data
    
    def _generate_accomplishments(self, role, projects):
        """Generate random recent accomplishments based on role and projects"""
        accomplishments = []
        num_accomplishments = random.randint(2, 4)
        
        # Role-specific accomplishment templates
        role_accomplishments = {
            "Software Engineer": [
                "Implemented {feature} which improved {metric} by {percentage}%",
                "Refactored {component} resulting in {benefit}",
                "Fixed {number} critical bugs in {project} ahead of deadline",
                "Designed and implemented {architecture} to support {need}",
                "Improved test coverage for {project} by {percentage}%"
            ],
            "UX Designer": [
                "Completed user research for {project} revealing key insights about {area}",
                "Redesigned {feature} which led to {percentage}% increase in user satisfaction",
                "Created {deliverable} for {project} that was well-received by stakeholders",
                "Conducted {number} usability tests identifying {benefit}",
                "Implemented design system improvements for {benefit}"
            ],
            "Product Manager": [
                "Led successful launch of {feature} resulting in {benefit}",
                "Defined product requirements for {project} that aligned team efforts",
                "Prioritized backlog effectively, increasing team velocity by {percentage}%",
                "Gathered customer feedback that led to {benefit}",
                "Facilitated cross-team coordination for {project}"
            ],
            "Data Scientist": [
                "Developed {model} that improved prediction accuracy by {percentage}%",
                "Analyzed {dataset} revealing insights about {area}",
                "Implemented {technique} resulting in {benefit}",
                "Optimized {process} reducing processing time by {percentage}%",
                "Created dashboard for {metric} that improved decision-making"
            ],
            "DevOps Engineer": [
                "Improved CI/CD pipeline reducing build time by {percentage}%",
                "Implemented {tool} for {benefit}",
                "Resolved {number} infrastructure issues improving system stability",
                "Set up monitoring for {component} providing {benefit}",
                "Reduced cloud costs by {percentage}% through {technique}"
            ]
        }
        
        # Get accomplishment templates for the role (use generic if role not found)
        templates = role_accomplishments.get(role, [
            "Completed {project} milestone ahead of schedule",
            "Contributed significantly to {project} success",
            "Demonstrated expertise in {area} that helped the team",
            "Took initiative on {task} that led to {benefit}",
            "Collaborated effectively with {team} to deliver {outcome}"
        ])
        
        # Generate random accomplishments
        for _ in range(num_accomplishments):
            template = random.choice(templates)
            accomplishment = template.format(
                project=random.choice(projects) if projects else "the project",
                feature=random.choice(["user authentication", "data visualization", "reporting module", "search functionality", "notification system"]),
                component=random.choice(["backend services", "frontend components", "database layer", "API endpoints", "authentication system"]),
                architecture=random.choice(["microservice architecture", "event-driven system", "caching layer", "data pipeline", "serverless functions"]),
                need=random.choice(["scalability", "high availability", "real-time processing", "data integrity", "future growth"]), # Added "need"
                area=random.choice(["user behavior", "performance bottlenecks", "customer preferences", "market trends", "system integration"]),
                deliverable=random.choice(["wireframes", "prototypes", "user flow diagrams", "style guide", "interaction models"]),
                model=random.choice(["prediction algorithm", "classification model", "recommendation system", "anomaly detection", "time series forecast"]),
                dataset=random.choice(["customer behavior data", "system performance logs", "market research", "user feedback", "operational metrics"]),
                technique=random.choice(["containerization", "infrastructure as code", "automated testing", "data preprocessing", "feature engineering"]),
                process=random.choice(["ETL pipeline", "build process", "deployment workflow", "data ingestion", "reporting cycle"]),
                tool=random.choice(["Kubernetes", "Terraform", "ELK stack", "Prometheus", "Jenkins"]),
                task=random.choice(["performance optimization", "documentation", "cross-team coordination", "risk assessment", "customer outreach"]),
                team=random.choice(["engineering", "product", "design", "marketing", "customer support"]),
                outcome=random.choice(["successful release", "improved metrics", "positive customer feedback", "system stability", "new capability"]),
                metric=random.choice(["performance", "user engagement", "conversion rate", "system uptime", "customer satisfaction"]),
                benefit=random.choice(["improved maintainability", "faster performance", "better user experience", "reduced costs", "increased reliability"]),
                percentage=random.randint(10, 50),
                number=random.randint(3, 12)
            )
            accomplishments.append(accomplishment)
        
        return accomplishments
    
    def _generate_positive_feedback(self, role, accomplishments):
        """Generate positive feedback based on role and accomplishments"""
        feedback_items = []
        num_items = random.randint(2, 3)
        
        # General positive feedback templates
        templates = [
            "Your {quality} in {context} has been particularly impressive",
            "I've noticed your exceptional {quality} while working on {context}",
            "Your recent work demonstrates strong {quality}, especially in {context}",
            "You've shown excellent {quality} that has {impact}",
            "The team has benefited from your {quality} in {context}"
        ]
        
        # Role-specific qualities
        role_qualities = {
            "Software Engineer": ["technical expertise", "problem-solving ability", "attention to code quality", "architectural thinking", "debugging skills"],
            "UX Designer": ["design thinking", "user empathy", "visual communication", "attention to detail", "innovative solutions"],
            "Product Manager": ["strategic thinking", "stakeholder management", "prioritization skills", "customer focus", "communication clarity"],
            "Data Scientist": ["analytical rigor", "data interpretation", "statistical expertise", "insight generation", "technical communication"],
            "DevOps Engineer": ["system reliability focus", "automation expertise", "proactive monitoring", "troubleshooting ability", "security mindset"]
        }
        
        # Get qualities for the role (use generic if role not found)
        qualities = role_qualities.get(role, ["teamwork", "initiative", "reliability", "adaptability", "communication"])
        
        # Generate positive feedback
        for _ in range(num_items):
            template = random.choice(templates)
            # Extract context from accomplishments if available
            context = "recent projects"
            if accomplishments:
                accomplishment = random.choice(accomplishments)
                words = accomplishment.split()
                if len(words) > 3:
                    context = " ".join(words[:3]) + "..."
            
            feedback = template.format(
                quality=random.choice(qualities),
                context=context,
                impact=random.choice([
                    "positively impacted the team's performance",
                    "contributed to our success",
                    "helped us meet our objectives",
                    "improved our delivery process",
                    "enhanced our product quality"
                ])
            )
            feedback_items.append(feedback)
        
        return feedback_items
    
    def _generate_constructive_feedback(self, role):
        """Generate constructive feedback based on role"""
        feedback_items = []
        num_items = random.randint(1, 2)  # Fewer constructive feedback items than positive
        
        # Role-specific improvement areas
        role_improvements = {
            "Software Engineer": [
                "Consider adding more comprehensive tests to ensure code reliability",
                "Documentation could be more detailed for complex functions",
                "Breaking down large pull requests into smaller ones would make reviews easier",
                "More proactive communication about technical challenges would help with planning"
            ],
            "UX Designer": [
                "Including more context in design presentations would help stakeholders understand decisions",
                "Earlier sharing of design concepts could help catch issues sooner",
                "More detailed documentation of user research findings would benefit the team",
                "Consider more diverse user personas in testing scenarios"
            ],
            "Product Manager": [
                "More detailed acceptance criteria would help development teams",
                "Earlier communication about scope changes would improve planning",
                "More frequent check-ins with development teams could prevent misalignment",
                "Consider gathering more quantitative data to support feature decisions"
            ],
            "Data Scientist": [
                "More documentation of methodologies would help others understand your approach",
                "Consider simpler models for initial solutions before optimizing",
                "More context in presentations would help non-technical stakeholders",
                "Earlier sharing of preliminary findings could guide project direction"
            ],
            "DevOps Engineer": [
                "More documentation for system configurations would help team knowledge",
                "Consider more proactive communication about infrastructure changes",
                "Involving developers earlier in deployment planning could improve outcomes",
                "More comprehensive monitoring alerts would help catch issues sooner"
            ]
        }
        
        # Get improvement areas for the role (use generic if role not found)
        improvements = role_improvements.get(role, [
            "More proactive communication would help with team coordination",
            "Consider documenting your process to help knowledge sharing",
            "Earlier flagging of potential issues would help with risk management",
            "More detailed updates in team meetings would improve visibility"
        ])
        
        # Generate constructive feedback
        for _ in range(num_items):
            feedback_items.append(random.choice(improvements))
        
        return feedback_items
    
    def _generate_action_items(self, constructive_feedback):
        """Generate action items based on constructive feedback"""
        action_items = []
        
        for feedback in constructive_feedback:
            # Extract key theme from feedback
            words = feedback.lower().split()
            if "documentation" in feedback.lower():
                action = "Create a documentation template for future work"
            elif "communication" in feedback.lower():
                action = "Schedule regular check-ins with team members"
            elif "test" in feedback.lower():
                action = "Implement test-driven development approach"
            elif "review" in feedback.lower() or "pull request" in feedback.lower():
                action = "Break down large changes into smaller, focused pull requests"
            elif "design" in feedback.lower():
                action = "Share design concepts earlier in the process"
            elif "data" in feedback.lower():
                action = "Create a data collection and analysis plan"
            elif "monitoring" in feedback.lower() or "alert" in feedback.lower():
                action = "Review and enhance monitoring system"
            else:
                action = "Create a personal improvement plan focused on " + words[1] if len(words) > 1 else "key areas"
            
            action_items.append(action)
        
        # Add one generic action item if we have few items
        if len(action_items) < 2:
            generic_actions = [
                "Schedule a follow-up discussion to review progress",
                "Document learnings and share with the team",
                "Identify a mentor who excels in this area",
                "Research best practices and create a personal guide"
            ]
            action_items.append(random.choice(generic_actions))
        
        return action_items
    
    def _generate_feedback_markdown(self, feedback):
        """Generate a markdown report of the feedback for a team member"""
        member_name = feedback["member"]["name"]
        role = feedback["member"]["role"]
        date = feedback["date"]
        follow_up_date = feedback["follow_up_date"]
        
        markdown = f"# Timely Feedback for {member_name}\n\n"
        markdown += f"**Role:** {role}\n\n"
        markdown += f"**Date:** {date}\n\n"
        markdown += f"**Follow-up Date:** {follow_up_date}\n\n"
        
        markdown += "## Recent Accomplishments\n\n"
        for accomplishment in feedback["recent_accomplishments"]:
            markdown += f"- {accomplishment}\n"
        markdown += "\n"
        
        markdown += "## Positive Feedback\n\n"
        for item in feedback["positive_feedback"]:
            markdown += f"- {item}\n"
        markdown += "\n"
        
        markdown += "## Areas for Growth\n\n"
        for item in feedback["constructive_feedback"]:
            markdown += f"- {item}\n"
        markdown += "\n"
        
        markdown += "## Action Items\n\n"
        for item in feedback["action_items"]:
            markdown += f"- {item}\n"
        markdown += "\n"
        
        return markdown
    
    def _generate_summary_markdown(self, feedback_data):
        """Generate a summary markdown report of all feedback"""
        markdown = "# Timely Feedback Summary\n\n"
        
        markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        markdown += f"**Number of Team Members:** {len(feedback_data)}\n\n"
        
        # Calculate total number of accomplishments and feedback items
        total_accomplishments = sum(len(f["recent_accomplishments"]) for f in feedback_data)
        total_positive = sum(len(f["positive_feedback"]) for f in feedback_data)
        total_constructive = sum(len(f["constructive_feedback"]) for f in feedback_data)
        total_actions = sum(len(f["action_items"]) for f in feedback_data)
        
        markdown += "## Feedback Overview\n\n"
        markdown += f"- **Total Accomplishments Recognized:** {total_accomplishments}\n"
        markdown += f"- **Total Positive Feedback Items:** {total_positive}\n"
        markdown += f"- **Total Areas for Growth Identified:** {total_constructive}\n"
        markdown += f"- **Total Action Items Created:** {total_actions}\n\n"
        
        # Team member summaries
        markdown += "## Team Member Summaries\n\n"
        for feedback in feedback_data:
            member_name = feedback["member"]["name"]
            role = feedback["member"]["role"]
            follow_up = feedback["follow_up_date"]
            
            markdown += f"### {member_name} ({role})\n\n"
            markdown += f"- **Accomplishments:** {len(feedback['recent_accomplishments'])}\n"
            markdown += f"- **Positive Feedback Items:** {len(feedback['positive_feedback'])}\n"
            markdown += f"- **Areas for Growth:** {len(feedback['constructive_feedback'])}\n"
            markdown += f"- **Action Items:** {len(feedback['action_items'])}\n"
            markdown += f"- **Follow-up Date:** {follow_up}\n\n"
        
        return markdown
