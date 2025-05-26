import os
import json
from agent.step_base import StepBase

class CreateDevelopmentItemStep(StepBase):
    """
    Implementation of the Create Development Item step.
    
    This step creates development items to help team members improve their skills and performance.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        self.logger.info("Executing Create Development Item step")
        
        # Read evaluations from previous step
        evaluations_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "evaluation_generation",
            "out",
            "evaluations.json"
        )
        
        if not os.path.exists(evaluations_path):
            self.logger.error("Evaluations not found. Please run evaluation_generation step first.")
            return False
        
        # Load evaluations
        with open(evaluations_path, "r") as f:
            evaluations = json.load(f)
        
        # Generate development items
        development_items = self._generate_development_items(evaluations)
        
        # Write development items to output
        self.write_output_file("development_items.json", json.dumps(development_items, indent=2))
        
        # Also write a markdown summary for each team member
        for member_items in development_items:
            member_name = member_items["member_name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_development.md",
                self._generate_development_markdown(member_items)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "development_items_summary.md",
            self._generate_summary_markdown(development_items)
        )
        
        return True
    
    def _generate_development_items(self, evaluations):
        """Generate development items for each team member"""
        development_items = []
        
        for evaluation in evaluations:
            member_id = evaluation["member_id"]
            member_name = evaluation["member_name"]
            role = evaluation["role"]
            
            # Generate development items based on improvement areas
            items = []
            for area in evaluation["improvement_areas"]:
                items.extend(self._generate_items_for_area(area, role))
            
            # Generate additional development items based on role
            items.extend(self._generate_role_specific_items(role))
            
            # Generate a stretch development item
            items.append(self._generate_stretch_item(role))
            
            # Add to the list
            development_items.append({
                "member_id": member_id,
                "member_name": member_name,
                "role": role,
                "items": items
            })
        
        return development_items
    
    def _generate_items_for_area(self, area, role):
        """Generate development items for a specific improvement area"""
        items = []
        
        if area == "code_quality":
            items.append({
                "title": "Code Quality Improvement",
                "type": "Technical Skill",
                "description": "Improve code quality by focusing on clean code principles, testing, and code reviews.",
                "actions": [
                    "Complete the 'Clean Code: Writing Code for Humans' course",
                    "Implement unit tests for all new code with at least 80% coverage",
                    "Actively participate in code reviews and incorporate feedback"
                ],
                "resources": [
                    {
                        "name": "Clean Code: A Handbook of Agile Software Craftsmanship",
                        "type": "Book",
                        "link": "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882"
                    },
                    {
                        "name": "Effective Unit Testing",
                        "type": "Course",
                        "link": "https://www.pluralsight.com/courses/unit-testing-principles-practices-patterns"
                    }
                ],
                "success_criteria": "Decrease in code review comments related to code quality by 50% over the next quarter"
            })
        
        elif area == "productivity":
            items.append({
                "title": "Productivity Enhancement",
                "type": "Work Management",
                "description": "Improve productivity through better time management and prioritization techniques.",
                "actions": [
                    "Implement time-blocking technique for at least 4 weeks",
                    "Use the Eisenhower Matrix for daily task prioritization",
                    "Eliminate or delegate low-value tasks"
                ],
                "resources": [
                    {
                        "name": "Deep Work: Rules for Focused Success in a Distracted World",
                        "type": "Book",
                        "link": "https://www.amazon.com/Deep-Work-Focused-Success-Distracted/dp/1455586692"
                    },
                    {
                        "name": "Time Management Fundamentals",
                        "type": "Course",
                        "link": "https://www.linkedin.com/learning/time-management-fundamentals"
                    }
                ],
                "success_criteria": "Complete 25% more tasks per sprint while maintaining quality standards"
            })
        
        elif area == "collaboration":
            items.append({
                "title": "Collaboration Enhancement",
                "type": "Soft Skill",
                "description": "Improve team collaboration and communication skills.",
                "actions": [
                    "Proactively participate in at least 3 cross-functional projects",
                    "Practice active listening in all team meetings",
                    "Schedule regular check-ins with key team members"
                ],
                "resources": [
                    {
                        "name": "Crucial Conversations: Tools for Talking When Stakes Are High",
                        "type": "Book",
                        "link": "https://www.amazon.com/Crucial-Conversations-Talking-Stakes-Second/dp/1469266822"
                    },
                    {
                        "name": "Effective Team Collaboration",
                        "type": "Workshop",
                        "link": "https://www.linkedin.com/learning/collaboration-principles-and-process"
                    }
                ],
                "success_criteria": "Positive feedback from team members on collaboration skills in next review cycle"
            })
        
        elif area == "innovation":
            items.append({
                "title": "Innovation Development",
                "type": "Creative Skill",
                "description": "Develop creative thinking and innovation skills.",
                "actions": [
                    "Dedicate 10% of work time to exploring new ideas and approaches",
                    "Participate in an innovation workshop or hackathon",
                    "Document and share at least 3 innovative ideas per month"
                ],
                "resources": [
                    {
                        "name": "The Innovator's Dilemma",
                        "type": "Book",
                        "link": "https://www.amazon.com/Innovators-Dilemma-Technologies-Management-Innovation/dp/1633691780"
                    },
                    {
                        "name": "Design Thinking: Understanding the Process",
                        "type": "Course",
                        "link": "https://www.linkedin.com/learning/design-thinking-understanding-the-process"
                    }
                ],
                "success_criteria": "Successfully implement at least one innovative solution that delivers measurable value"
            })
        
        elif area == "reliability":
            items.append({
                "title": "Work Reliability Improvement",
                "type": "Professional Skill",
                "description": "Enhance reliability by improving estimation, planning, and delivery consistency.",
                "actions": [
                    "Implement a personal task tracking system",
                    "Practice breaking down tasks into smaller, more manageable units",
                    "Proactively communicate progress and blockers to stakeholders"
                ],
                "resources": [
                    {
                        "name": "The Effective Engineer",
                        "type": "Book",
                        "link": "https://www.effectiveengineer.com/book"
                    },
                    {
                        "name": "Agile Estimation",
                        "type": "Course",
                        "link": "https://www.pluralsight.com/courses/agile-estimation"
                    }
                ],
                "success_criteria": "Deliver 90% of commitments on time over the next quarter"
            })
        
        elif area == "customer_focus":
            items.append({
                "title": "Customer Focus Development",
                "type": "Business Skill",
                "description": "Strengthen understanding of customer needs and develop customer-focused mindset.",
                "actions": [
                    "Participate in at least 5 customer interviews or feedback sessions",
                    "Shadow customer support for at least 4 hours per month",
                    "Create user personas and journey maps for key features"
                ],
                "resources": [
                    {
                        "name": "Inspired: How to Create Products Customers Love",
                        "type": "Book",
                        "link": "https://www.amazon.com/INSPIRED-Create-Tech-Products-Customers/dp/1119387507"
                    },
                    {
                        "name": "Customer-Focused Product Development",
                        "type": "Course",
                        "link": "https://www.linkedin.com/learning/customer-focused-product-development"
                    }
                ],
                "success_criteria": "Incorporate specific customer feedback into at least 2 features or improvements"
            })
        
        return items
    
    def _generate_role_specific_items(self, role):
        """Generate role-specific development items"""
        items = []
        
        if role == "Software Engineer":
            items.append({
                "title": "Advanced Programming Concepts",
                "type": "Technical Skill",
                "description": "Deepen understanding of advanced programming concepts relevant to current projects.",
                "actions": [
                    "Complete an advanced course in relevant technology stack",
                    "Implement at least one feature using new techniques",
                    "Present a tech talk on an advanced topic to the team"
                ],
                "resources": [
                    {
                        "name": "Design Patterns: Elements of Reusable Object-Oriented Software",
                        "type": "Book",
                        "link": "https://www.amazon.com/Design-Patterns-Elements-Reusable-Object-Oriented/dp/0201633612"
                    },
                    {
                        "name": "Advanced Programming Concepts",
                        "type": "Course",
                        "link": "https://www.pluralsight.com/paths/advanced-programming-concepts"
                    }
                ],
                "success_criteria": "Successfully apply advanced concepts in at least two projects"
            })
        
        elif role == "UX Designer":
            items.append({
                "title": "Advanced User Research Techniques",
                "type": "Technical Skill",
                "description": "Develop expertise in advanced user research methodologies.",
                "actions": [
                    "Design and conduct a comprehensive user research study",
                    "Experiment with at least two new research methodologies",
                    "Create a research playbook for the team"
                ],
                "resources": [
                    {
                        "name": "Just Enough Research",
                        "type": "Book",
                        "link": "https://abookapart.com/products/just-enough-research"
                    },
                    {
                        "name": "Advanced User Research Techniques",
                        "type": "Course",
                        "link": "https://www.interaction-design.org/courses/user-research-methods-and-best-practices"
                    }
                ],
                "success_criteria": "Research findings directly influence at least three product decisions"
            })
        
        elif role == "Product Manager":
            items.append({
                "title": "Strategic Product Management",
                "type": "Business Skill",
                "description": "Develop strategic product thinking and roadmap planning capabilities.",
                "actions": [
                    "Create a long-term vision and roadmap for your product area",
                    "Conduct competitive analysis and market research",
                    "Define clear metrics for product success"
                ],
                "resources": [
                    {
                        "name": "Escaping the Build Trap",
                        "type": "Book",
                        "link": "https://www.amazon.com/Escaping-Build-Trap-Effective-Management/dp/149197379X"
                    },
                    {
                        "name": "Strategic Product Management",
                        "type": "Course",
                        "link": "https://www.productschool.com/product-management-certification/"
                    }
                ],
                "success_criteria": "Create a compelling product strategy that aligns with business goals and receives stakeholder approval"
            })
        
        elif role == "Data Scientist":
            items.append({
                "title": "Advanced Machine Learning Techniques",
                "type": "Technical Skill",
                "description": "Develop expertise in advanced machine learning methodologies.",
                "actions": [
                    "Implement at least one project using advanced ML techniques",
                    "Participate in a Kaggle competition",
                    "Create a learning resource for the team on an advanced topic"
                ],
                "resources": [
                    {
                        "name": "Deep Learning",
                        "type": "Book",
                        "link": "https://www.deeplearningbook.org/"
                    },
                    {
                        "name": "Advanced Machine Learning Specialization",
                        "type": "Course",
                        "link": "https://www.coursera.org/specializations/aml"
                    }
                ],
                "success_criteria": "Successfully implement an advanced model that outperforms current solutions by at least 15%"
            })
        
        elif role == "DevOps Engineer":
            items.append({
                "title": "Infrastructure as Code Mastery",
                "type": "Technical Skill",
                "description": "Develop expertise in infrastructure as code and automated deployment.",
                "actions": [
                    "Implement infrastructure as code for a key system",
                    "Create a CI/CD pipeline that reduces deployment time by 50%",
                    "Document best practices for the team"
                ],
                "resources": [
                    {
                        "name": "Infrastructure as Code",
                        "type": "Book",
                        "link": "https://www.amazon.com/Infrastructure-Code-Managing-Servers-Cloud/dp/1491924357"
                    },
                    {
                        "name": "DevOps Engineering on AWS",
                        "type": "Course",
                        "link": "https://aws.amazon.com/training/course-descriptions/devops-engineering/"
                    }
                ],
                "success_criteria": "Reduce infrastructure provisioning time by 75% and eliminate manual configuration errors"
            })
        
        return items
    
    def _generate_stretch_item(self, role):
        """Generate a stretch development item based on role"""
        if role == "Software Engineer":
            return {
                "title": "System Architecture Design",
                "type": "Stretch Skill",
                "description": "Develop system architecture design skills by taking on a more senior technical role.",
                "actions": [
                    "Lead the architecture design for a new feature or service",
                    "Create architecture documentation including diagrams and decision records",
                    "Present the architecture to stakeholders and incorporate feedback"
                ],
                "resources": [
                    {
                        "name": "Clean Architecture",
                        "type": "Book",
                        "link": "https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164"
                    },
                    {
                        "name": "Software Architecture Fundamentals",
                        "type": "Course",
                        "link": "https://www.pluralsight.com/courses/software-architecture-fundamentals"
                    }
                ],
                "success_criteria": "Successfully design and implement a system architecture that receives positive feedback from senior architects"
            }
        
        elif role == "UX Designer":
            return {
                "title": "Design System Leadership",
                "type": "Stretch Skill",
                "description": "Take a leadership role in developing or enhancing the company's design system.",
                "actions": [
                    "Audit current design patterns and identify inconsistencies",
                    "Create or enhance at least 10 design system components",
                    "Document usage guidelines and best practices"
                ],
                "resources": [
                    {
                        "name": "Atomic Design",
                        "type": "Book",
                        "link": "https://atomicdesign.bradfrost.com/table-of-contents/"
                    },
                    {
                        "name": "Design Systems: A Practical Guide",
                        "type": "Course",
                        "link": "https://www.designbetter.co/design-systems-handbook"
                    }
                ],
                "success_criteria": "Design system adoption increases by 40% across product teams"
            }
        
        elif role == "Product Manager":
            return {
                "title": "Data-Driven Product Development",
                "type": "Stretch Skill",
                "description": "Develop advanced data analysis skills to drive product decisions.",
                "actions": [
                    "Implement a comprehensive product analytics framework",
                    "Create dashboards for key product metrics",
                    "Run at least three A/B tests to optimize key features"
                ],
                "resources": [
                    {
                        "name": "Lean Analytics",
                        "type": "Book",
                        "link": "https://www.amazon.com/Lean-Analytics-Better-Startup-Faster/dp/1449335675"
                    },
                    {
                        "name": "Product Analytics",
                        "type": "Course",
                        "link": "https://www.mixpanel.com/blog/analytics-academy/"
                    }
                ],
                "success_criteria": "Make at least five significant product decisions based on data insights that lead to measurable improvements"
            }
        
        elif role == "Data Scientist":
            return {
                "title": "Production ML Systems",
                "type": "Stretch Skill",
                "description": "Develop skills in designing and implementing production-ready machine learning systems.",
                "actions": [
                    "Design and implement a production ML pipeline",
                    "Implement monitoring and alerting for model performance",
                    "Create a system for continuous model retraining"
                ],
                "resources": [
                    {
                        "name": "Designing Machine Learning Systems",
                        "type": "Book",
                        "link": "https://www.amazon.com/Designing-Machine-Learning-Systems-Production-Ready/dp/1098107969"
                    },
                    {
                        "name": "MLOps: Machine Learning Operations",
                        "type": "Course",
                        "link": "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops"
                    }
                ],
                "success_criteria": "Successfully deploy and maintain a machine learning model in production with 99% uptime"
            }
        
        elif role == "DevOps Engineer":
            return {
                "title": "Site Reliability Engineering",
                "type": "Stretch Skill",
                "description": "Develop SRE skills to enhance system reliability and performance.",
                "actions": [
                    "Implement comprehensive monitoring and alerting",
                    "Create runbooks for incident response",
                    "Conduct chaos engineering experiments"
                ],
                "resources": [
                    {
                        "name": "Site Reliability Engineering",
                        "type": "Book",
                        "link": "https://sre.google/sre-book/table-of-contents/"
                    },
                    {
                        "name": "Implementing SRE Practices",
                        "type": "Course",
                        "link": "https://www.coursera.org/learn/site-reliability-engineering-slos"
                    }
                ],
                "success_criteria": "Reduce system downtime by 90% and mean time to recovery by 75%"
            }
        
        else:
            return {
                "title": "Leadership Development",
                "type": "Stretch Skill",
                "description": "Develop leadership skills by taking on more responsibility and mentoring others.",
                "actions": [
                    "Lead a cross-functional project or initiative",
                    "Mentor at least one junior team member",
                    "Create and present a training session on an area of expertise"
                ],
                "resources": [
                    {
                        "name": "The Leadership Challenge",
                        "type": "Book",
                        "link": "https://www.amazon.com/Leadership-Challenge-Extraordinary-Things-Organizations/dp/1119278961"
                    },
                    {
                        "name": "Developing Leadership Skills",
                        "type": "Course",
                        "link": "https://www.linkedin.com/learning/paths/develop-your-leadership-skills"
                    }
                ],
                "success_criteria": "Successfully lead a project to completion and receive positive feedback from team members"
            }
    
    def _generate_development_markdown(self, member_items):
        """Generate a markdown summary of development items for a team member"""
        markdown = f"# Development Plan: {member_items['member_name']}\n\n"
        markdown += f"**Role:** {member_items['role']}\n\n"
        
        markdown += "## Development Items\n\n"
        
        for i, item in enumerate(member_items["items"], 1):
            markdown += f"### {i}. {item['title']} ({item['type']})\n\n"
            markdown += f"**Description:** {item['description']}\n\n"
            
            markdown += "**Actions:**\n\n"
            for action in item["actions"]:
                markdown += f"- {action}\n"
            
            markdown += "\n**Resources:**\n\n"
            for resource in item["resources"]:
                markdown += f"- [{resource['name']}]({resource['link']}) ({resource['type']})\n"
            
            markdown += f"\n**Success Criteria:** {item['success_criteria']}\n\n"
            
            markdown += "---\n\n"
        
        markdown += "## Quarterly Check-in Schedule\n\n"
        markdown += "| Month | Date | Focus Areas |\n"
        markdown += "|-------|------|-------------|\n"
        markdown += "| Month 1 | TBD | Initial plan review and adjustment |\n"
        markdown += "| Month 2 | TBD | Progress check and feedback |\n"
        markdown += "| Month 3 | TBD | Final review and next steps |\n\n"
        
        markdown += "## Notes\n\n"
        markdown += "- This development plan should be reviewed and updated regularly\n"
        markdown += "- Progress should be discussed during regular 1:1 meetings\n"
        markdown += "- Resources and support will be provided to help achieve development goals\n"
        
        return markdown
    
    def _generate_summary_markdown(self, all_items):
        """Generate a summary markdown for all development items"""
        markdown = "# Team Development Plans Summary\n\n"
        
        markdown += "## Overview\n\n"
        markdown += f"This document summarizes the development plans for {len(all_items)} team members.\n\n"
        
        markdown += "## Team Members and Focus Areas\n\n"
        markdown += "| Team Member | Role | Primary Development Areas |\n"
        markdown += "|------------|------|-------------------------|\n"
        
        for member_items in all_items:
            name = member_items["member_name"]
            role = member_items["role"]
            
            focus_areas = ", ".join([item["title"] for item in member_items["items"]])
            
            markdown += f"| {name} | {role} | {focus_areas} |\n"
        
        markdown += "\n## Common Development Areas\n\n"
        
        # Collect all development areas
        development_areas = {}
        for member_items in all_items:
            for item in member_items["items"]:
                area = item["type"]
                if area in development_areas:
                    development_areas[area] += 1
                else:
                    development_areas[area] = 1
        
        # Sort by frequency
        sorted_areas = sorted(development_areas.items(), key=lambda x: x[1], reverse=True)
        
        for area, count in sorted_areas:
            markdown += f"- **{area}**: {count} team members\n"
        
        markdown += "\n## Recommended Team Training\n\n"
        markdown += "Based on the individual development plans, the following team training sessions are recommended:\n\n"
        
        # Suggest some team training based on common areas
        common_areas = [area for area, count in sorted_areas if count >= 2]
        
        if "Technical Skill" in common_areas:
            markdown += "1. **Technical Excellence Workshop**: A workshop focusing on code quality, testing, and best practices.\n"
        
        if "Soft Skill" in common_areas or "Professional Skill" in common_areas:
            markdown += "2. **Effective Communication and Collaboration**: A workshop to improve team communication and collaboration.\n"
        
        if "Business Skill" in common_areas:
            markdown += "3. **Customer-Focused Development**: A session on understanding and addressing customer needs.\n"
        
        if "Creative Skill" in common_areas:
            markdown += "4. **Innovation and Design Thinking**: A workshop on creative problem-solving and innovation.\n"
        
        if "Stretch Skill" in common_areas:
            markdown += "5. **Leadership Development**: A program to develop leadership skills across the team.\n"
        
        return markdown
