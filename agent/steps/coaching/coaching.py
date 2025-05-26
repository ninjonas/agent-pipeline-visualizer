import os
import json
import random
from datetime import datetime
from agent.step_base import StepBase
from loguru import logger

class CoachingStep(StepBase):
    """
    Implementation of the Coaching step.
    
    This step generates coaching plans and resources based on development needs and feedback.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        logger.info("Executing Coaching step")
        
        # Read updated development items from previous step
        development_items_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "update_development_item",
            "out",
            "updated_development_items.json"
        )
        
        # If updated development items aren't available, try the original development items
        if not os.path.exists(development_items_path):
            development_items_path = os.path.join(
                os.path.dirname(os.path.dirname(self.input_dir)),
                "create_development_item",
                "out",
                "development_items.json"
            )
        
        if not os.path.exists(development_items_path):
            logger.error("Development items not found. Please run create_development_item or update_development_item step first.")
            return False
        
        # Also read the timely feedback if available
        feedback_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "timely_feedback",
            "out",
            "timely_feedback.json"
        )
        
        feedback_data = None
        if os.path.exists(feedback_path):
            try:
                with open(feedback_path, "r", encoding="utf-8") as f:
                    feedback_data = json.load(f)
            except FileNotFoundError:
                logger.error(f"Feedback file not found at {feedback_path}")
                # Continue without feedback data if not found, as it's optional
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {feedback_path}")
                # Continue without feedback data if JSON is invalid
            except OSError as e:
                logger.error(f"An OS error occurred while reading {feedback_path}: {e}")
                # Continue without feedback data on other OS errors
        
        # Load development items
        try:
            with open(development_items_path, "r", encoding="utf-8") as f:
                development_items = json.load(f)
        except FileNotFoundError:
            logger.error(f"Development items file not found at {development_items_path}")
            return False
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {development_items_path}")
            return False
        except OSError as e:
            logger.error(f"An OS error occurred while reading {development_items_path}: {e}")
            return False
        
        # Generate coaching plans
        coaching_plans = self._generate_coaching_plans(development_items, feedback_data)
        
        # Write coaching plans to output
        self.write_output_file("coaching_plans.json", json.dumps(coaching_plans, indent=2))
        
        # Also write a markdown summary for each team member
        for member_plan in coaching_plans:
            member_name = member_plan["member_name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_coaching_plan.md",
                self._generate_coaching_markdown(member_plan)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "coaching_summary.md",
            self._generate_summary_markdown(coaching_plans)
        )
        
        return True
    
    def _generate_coaching_plans(self, development_items, feedback_data=None):
        """Generate coaching plans for each team member"""
        coaching_plans = []
        
        for member_items in development_items:
            member_id = member_items["member_id"]
            member_name = member_items["member_name"]
            role = member_items["role"]
            
            # Get feedback for this member if available
            member_feedback = None
            if feedback_data:
                member_feedback = next(
                    (f for f in feedback_data if f["member"]["id"] == member_id),
                    None
                )
            
            # Generate coaching focus areas
            focus_areas = self._generate_focus_areas(member_items, member_feedback)
            
            # Generate coaching sessions
            coaching_sessions = self._generate_coaching_sessions(focus_areas, role)
            
            # Generate resources
            resources = self._generate_resources(focus_areas, role)
            
            # Create the coaching plan
            coaching_plan = {
                "member_id": member_id,
                "member_name": member_name,
                "role": role,
                "focus_areas": focus_areas,
                "coaching_sessions": coaching_sessions,
                "resources": resources,
                "check_in_frequency": random.choice(["Weekly", "Bi-weekly", "Monthly"]),
                "success_metrics": self._generate_success_metrics(focus_areas) # Removed role argument
            }
            
            coaching_plans.append(coaching_plan)
        
        return coaching_plans
    
    def _generate_focus_areas(self, member_items, member_feedback=None):
        """Generate coaching focus areas based on development items and feedback"""
        focus_areas = []
        
        # Extract areas from development items
        items = member_items.get("items", [])
        
        # If we have updated development items, prioritize those that need modification
        items_needing_modification = [
            item for item in items 
            if item.get("needs_modification", False)
        ]
        
        # If we have items needing modification, prioritize those
        prioritized_items = items_needing_modification if items_needing_modification else items
        
        # Extract focus areas from development items
        for item in prioritized_items[:2]:  # Limit to top 2 items
            focus_areas.append({
                "title": item["title"],
                "type": item["type"],
                "description": item["description"],
                "current_status": item.get("status", "Not Started"),
                "priority": "High" if item.get("needs_modification", False) else "Medium"
            })
        
        # If we have feedback, add areas from constructive feedback
        if member_feedback and len(focus_areas) < 3:
            constructive_feedback = member_feedback.get("constructive_feedback", [])
            for feedback in constructive_feedback[:3 - len(focus_areas)]:
                # Create a focus area title from the feedback
                words = feedback.split()
                if len(words) > 3:
                    title = " ".join(words[:3]) + "..."
                else:
                    title = feedback
                
                focus_areas.append({
                    "title": title,
                    "type": "Feedback Response",
                    "description": feedback,
                    "current_status": "Not Started",
                    "priority": "High"
                })
        
        # If we still have fewer than 3 focus areas, add generic ones
        role = member_items["role"]
        generic_focus_areas = {
            "Software Engineer": [
                {"title": "Code Review Skills", "type": "Technical Skill", "description": "Improve ability to provide and receive code review feedback effectively."},
                {"title": "System Design", "type": "Technical Skill", "description": "Develop skills in designing scalable and maintainable systems."},
                {"title": "Technical Communication", "type": "Communication", "description": "Enhance ability to communicate technical concepts to non-technical stakeholders."}
            ],
            "UX Designer": [
                {"title": "User Research Methods", "type": "Technical Skill", "description": "Expand toolkit of user research methodologies and techniques."},
                {"title": "Design Systems", "type": "Technical Skill", "description": "Develop expertise in creating and maintaining design systems."},
                {"title": "Cross-functional Collaboration", "type": "Communication", "description": "Improve collaboration with engineering and product teams."}
            ],
            "Product Manager": [
                {"title": "Data-driven Decision Making", "type": "Technical Skill", "description": "Enhance ability to use data to inform product decisions."},
                {"title": "Stakeholder Management", "type": "Leadership", "description": "Improve skills in managing diverse stakeholder expectations."},
                {"title": "Technical Understanding", "type": "Technical Skill", "description": "Deepen technical knowledge to better collaborate with engineering."}
            ],
            "Data Scientist": [
                {"title": "Business Impact Communication", "type": "Communication", "description": "Improve ability to communicate the business impact of data insights."},
                {"title": "Advanced Modeling Techniques", "type": "Technical Skill", "description": "Expand knowledge of advanced modeling approaches."},
                {"title": "Data Storytelling", "type": "Communication", "description": "Enhance ability to create compelling narratives from data."}
            ],
            "DevOps Engineer": [
                {"title": "Security Best Practices", "type": "Technical Skill", "description": "Deepen knowledge of security best practices in infrastructure."},
                {"title": "Incident Management", "type": "Technical Skill", "description": "Improve skills in managing and resolving production incidents."},
                {"title": "Cross-team Collaboration", "type": "Communication", "description": "Enhance ability to collaborate with development teams on infrastructure needs."}
            ]
        }
        
        # Get generic focus areas for the role (use default if role not found)
        role_focus_areas = generic_focus_areas.get(role, [
            {"title": "Project Management", "type": "Leadership", "description": "Develop skills in managing project timelines and resources."},
            {"title": "Stakeholder Communication", "type": "Communication", "description": "Improve communication with diverse stakeholders."},
            {"title": "Strategic Thinking", "type": "Leadership", "description": "Enhance ability to think strategically about long-term goals."}
        ])
        
        # Add generic focus areas if needed
        while len(focus_areas) < 3:
            # Pick a random generic area that's not already included
            generic_area = random.choice(role_focus_areas)
            if not any(area["title"] == generic_area["title"] for area in focus_areas):
                generic_area_copy = generic_area.copy()
                generic_area_copy["current_status"] = "Not Started"
                generic_area_copy["priority"] = "Medium"
                focus_areas.append(generic_area_copy)
        
        return focus_areas
    
    def _generate_coaching_sessions(self, focus_areas, role):
        """Generate coaching sessions based on focus areas"""
        coaching_sessions = []
        
        for _, area in enumerate(focus_areas): # Replaced i with _
            # Generate 2-3 sessions per focus area
            num_sessions = random.randint(2, 3)
            area_title = area["title"]
            area_type = area["type"]
            
            for j in range(num_sessions):
                # Determine session focus based on session number
                if j == 0:
                    session_focus = "Assessment and Goal Setting"
                    approach = f"Assess current abilities in {area_title} and set specific, measurable goals for improvement."
                elif j == num_sessions - 1:
                    session_focus = "Progress Review and Next Steps"
                    approach = f"Review progress in {area_title}, celebrate wins, and identify ongoing development opportunities."
                else:
                    # Middle sessions focus on skill development
                    session_focuses = [
                        "Skill Development", 
                        "Practical Application", 
                        "Challenge Identification", 
                        "Feedback and Adjustment"
                    ]
                    session_focus = random.choice(session_focuses)
                    
                    if session_focus == "Skill Development":
                        approach = f"Focus on building specific skills related to {area_title} through targeted exercises."
                    elif session_focus == "Practical Application":
                        approach = f"Apply learning from previous sessions to current work projects involving {area_title}."
                    elif session_focus == "Challenge Identification":
                        approach = f"Identify and address specific challenges in applying {area_title} skills."
                    else:
                        approach = f"Gather feedback on recent work related to {area_title} and adjust development approach."
                
                # Generate coaching techniques based on area type
                techniques = []
                if area_type == "Technical Skill":
                    techniques = ["Guided practice", "Expert shadowing", "Case study analysis", "Code/design review"]
                elif area_type == "Leadership":
                    techniques = ["Role playing", "Scenario planning", "360-degree feedback discussion", "Leadership assessment"]
                elif area_type == "Communication":
                    techniques = ["Recorded practice presentations", "Feedback analysis", "Communication style assessment", "Stakeholder mapping"]
                else:
                    techniques = ["Goal setting", "Progress review", "Action planning", "Reflection exercises"]
                
                # Create the session
                session = {
                    "title": f"{area_title} - Session {j+1}",
                    "focus_area": area_title,
                    "session_number": j+1,
                    "focus": session_focus,
                    "approach": approach,
                    "duration": f"{random.randint(30, 60)} minutes",
                    "techniques": random.sample(techniques, min(2, len(techniques))),
                    "preparation": self._generate_preparation_steps(area_title, session_focus, role)
                }
                
                coaching_sessions.append(session)
        
        # Sort sessions by focus area and session number
        coaching_sessions.sort(key=lambda s: (s["focus_area"], s["session_number"]))
        
        return coaching_sessions
    
    def _generate_preparation_steps(self, area_title, session_focus, role):
        """Generate preparation steps for coaching sessions"""
        preparation_steps = []
        
        if session_focus == "Assessment and Goal Setting":
            preparation_steps = [
                f"Complete self-assessment of current skills in {area_title}",
                "Identify 2-3 specific situations where improvement would have the most impact",
                "Review relevant performance feedback from past evaluations"
            ]
        elif session_focus == "Skill Development":
            preparation_steps = [
                "Complete pre-reading on assigned topics",
                "Prepare examples of recent work for discussion",
                "Identify specific questions about applying new skills"
            ]
        elif session_focus == "Practical Application":
            preparation_steps = [
                "Select a current project to apply new skills",
                "Document specific challenges in applying skills",
                "Prepare draft work product for review"
            ]
        elif session_focus == "Progress Review and Next Steps":
            preparation_steps = [
                "Reflect on progress made since coaching began",
                "Identify ongoing challenges and support needed",
                "Draft goals for continued development"
            ]
        else:
            preparation_steps = [
                "Review notes from previous sessions",
                "Prepare specific examples or questions",
                "Complete any assigned activities"
            ]
        
        # Add a role-specific preparation step
        if role == "Software Engineer":
            preparation_steps.append("Bring code samples or system designs for discussion")
        elif role == "UX Designer":
            preparation_steps.append("Bring design artifacts or user research findings")
        elif role == "Product Manager":
            preparation_steps.append("Bring product requirements or prioritization examples")
        elif role == "Data Scientist":
            preparation_steps.append("Bring data analysis examples or model documentation")
        elif role == "DevOps Engineer":
            preparation_steps.append("Bring infrastructure diagrams or automation scripts")
        
        # Select a subset of preparation steps
        return random.sample(preparation_steps, min(3, len(preparation_steps)))
    
    def _generate_resources(self, focus_areas, role):
        """Generate resources for each focus area"""
        resources = []
        
        for area in focus_areas:
            area_title = area["title"]
            area_type = area["type"]
            
            # Generate 2-4 resources per focus area
            area_resources = []
            
            # Add a book recommendation
            books = {
                "Software Engineer": [
                    "Clean Code by Robert Martin",
                    "Designing Data-Intensive Applications by Martin Kleppmann",
                    "Refactoring by Martin Fowler",
                    "The Pragmatic Programmer by Andrew Hunt and David Thomas"
                ],
                "UX Designer": [
                    "Don't Make Me Think by Steve Krug",
                    "The Design of Everyday Things by Don Norman",
                    "About Face: The Essentials of Interaction Design by Alan Cooper",
                    "Universal Principles of Design by William Lidwell"
                ],
                "Product Manager": [
                    "Inspired: How to Create Products Customers Love by Marty Cagan",
                    "Hooked: How to Build Habit-Forming Products by Nir Eyal",
                    "Escaping the Build Trap by Melissa Perri",
                    "The Lean Product Playbook by Dan Olsen"
                ],
                "Data Scientist": [
                    "Storytelling with Data by Cole Nussbaumer Knaflic",
                    "Hands-On Machine Learning with Scikit-Learn and TensorFlow by Aurélien Géron",
                    "Python for Data Analysis by Wes McKinney",
                    "Data Science for Business by Foster Provost and Tom Fawcett"
                ],
                "DevOps Engineer": [
                    "The Phoenix Project by Gene Kim",
                    "Site Reliability Engineering by Niall Richard Murphy",
                    "Continuous Delivery by Jez Humble and David Farley",
                    "Infrastructure as Code by Kief Morris"
                ]
            }
            
            # Add a book based on role and area type
            role_books = books.get(role, [
                "The Five Dysfunctions of a Team by Patrick Lencioni",
                "Crucial Conversations by Kerry Patterson",
                "Drive by Daniel Pink",
                "Mindset by Carol Dweck"
            ])
            
            area_resources.append({
                "type": "Book",
                "title": random.choice(role_books),
                "description": f"Comprehensive resource for developing {area_title} skills"
            })
            
            # Add an online course
            online_courses = {
                "Technical Skill": [
                    f"{area_title} Fundamentals on Coursera",
                    f"Advanced {area_title} on Udemy",
                    f"Practical {area_title} on Pluralsight",
                    f"{area_title} Masterclass on LinkedIn Learning"
                ],
                "Leadership": [
                    "Leadership Strategies for Tomorrow's Leaders on Coursera",
                    "Developing Leadership Presence on LinkedIn Learning",
                    "Strategic Leadership Skills on Udemy",
                    "Executive Leadership Program on edX"
                ],
                "Communication": [
                    "Effective Communication Skills for Professionals on Coursera",
                    "Strategic Communication on LinkedIn Learning",
                    "Advanced Presentation Skills on Udemy",
                    "Communication that Drives Results on edX"
                ],
                "Feedback Response": [
                    "Receiving and Implementing Feedback on Coursera",
                    "Feedback as a Tool for Growth on LinkedIn Learning",
                    "Transforming Feedback into Action on Udemy",
                    "The Art of Effective Feedback on edX"
                ]
            }
            
            area_courses = online_courses.get(area_type, [
                f"{area_title} Skills Development on Coursera",
                f"Professional {area_title} on LinkedIn Learning",
                f"Mastering {area_title} on Udemy",
                f"Applied {area_title} on edX"
            ])
            
            area_resources.append({
                "type": "Online Course",
                "title": random.choice(area_courses),
                "description": f"Structured learning path for {area_title}"
            })
            
            # Add internal resources
            internal_resources = [
                {
                    "type": "Internal Workshop",
                    "title": f"{area_title} Best Practices Workshop",
                    "description": "Interactive session with internal experts"
                },
                {
                    "type": "Mentorship",
                    "title": f"Mentorship with {area_title} Expert",
                    "description": "1:1 sessions with an experienced colleague"
                },
                {
                    "type": "Practice Group",
                    "title": f"{area_title} Community of Practice",
                    "description": "Regular meetings with others developing similar skills"
                },
                {
                    "type": "Knowledge Base",
                    "title": f"Internal {area_title} Documentation",
                    "description": "Company-specific best practices and examples"
                }
            ]
            
            # Add 1-2 internal resources
            area_resources.extend(random.sample(internal_resources, random.randint(1, 2)))
            
            # Create the resources entry
            resources.append({
                "focus_area": area_title,
                "resources": area_resources
            })
        
        return resources
    
    def _generate_success_metrics(self, focus_areas): # Removed role parameter
        """Generate success metrics for the coaching plan"""
        metrics = []
        
        for area in focus_areas:
            area_title = area["title"]
            area_type = area["type"]
            
            # Generate metrics based on area type
            if area_type == "Technical Skill":
                metrics.append({
                    "focus_area": area_title,
                    "metrics": [
                        f"Demonstrated application of {area_title} in at least 2 projects",
                        f"Peer feedback indicates improvement in {area_title}",
                        f"Completion of all learning resources related to {area_title}"
                    ]
                })
            elif area_type == "Leadership":
                metrics.append({
                    "focus_area": area_title,
                    "metrics": [
                        f"Successfully led at least 1 initiative demonstrating {area_title}",
                        f"Team feedback indicates improved {area_title}",
                        f"Documented examples of applying {area_title} principles"
                    ]
                })
            elif area_type == "Communication":
                metrics.append({
                    "focus_area": area_title,
                    "metrics": [
                        "Stakeholder feedback indicates improved clarity in {area_title}",
                        f"Successfully delivered presentations demonstrating {area_title} skills",
                        "Reduced incidents of miscommunication in relevant contexts" # Removed f-string
                    ]
                })
            else:
                metrics.append({
                    "focus_area": area_title,
                    "metrics": [
                        f"Demonstrated improvement in {area_title} based on manager feedback",
                        f"Self-assessment indicates increased confidence in {area_title}",
                        f"Application of {area_title} skills in day-to-day work"
                    ]
                })
        
        return metrics
    
    def _generate_coaching_markdown(self, coaching_plan):
        """Generate a markdown report of the coaching plan for a team member"""
        member_name = coaching_plan["member_name"]
        role = coaching_plan["role"]
        check_in_frequency = coaching_plan["check_in_frequency"]
        
        markdown = f"# Coaching Plan for {member_name}\n\n"
        markdown += f"**Role:** {role}\n\n"
        markdown += f"**Check-in Frequency:** {check_in_frequency}\n\n"
        
        markdown += "## Focus Areas\n\n"
        for area in coaching_plan["focus_areas"]:
            markdown += f"### {area['title']}\n\n"
            markdown += f"**Type:** {area['type']}\n\n"
            markdown += f"**Description:** {area['description']}\n\n"
            markdown += f"**Current Status:** {area['current_status']}\n\n"
            markdown += f"**Priority:** {area['priority']}\n\n"
        
        markdown += "## Coaching Sessions\n\n"
        current_focus_area = None
        for session in coaching_plan["coaching_sessions"]:
            if session["focus_area"] != current_focus_area:
                current_focus_area = session["focus_area"]
                markdown += f"### {current_focus_area}\n\n"
            
            markdown += f"#### Session {session['session_number']}: {session['focus']}\n\n"
            markdown += f"**Approach:** {session['approach']}\n\n"
            markdown += f"**Duration:** {session['duration']}\n\n"
            
            markdown += "**Techniques:**\n\n"
            for technique in session["techniques"]:
                markdown += f"- {technique}\n"
            markdown += "\n"
            
            markdown += "**Preparation:**\n\n"
            for step in session["preparation"]:
                markdown += f"- {step}\n"
            markdown += "\n"
        
        markdown += "## Resources\n\n"
        for area_resources in coaching_plan["resources"]:
            markdown += f"### {area_resources['focus_area']}\n\n"
            
            for resource in area_resources["resources"]:
                markdown += f"#### {resource['title']} ({resource['type']})\n\n"
                markdown += f"{resource['description']}\n\n"
        
        markdown += "## Success Metrics\n\n"
        for area_metrics in coaching_plan["success_metrics"]:
            markdown += f"### {area_metrics['focus_area']}\n\n"
            
            for metric in area_metrics["metrics"]:
                markdown += f"- {metric}\n"
            markdown += "\n"
        
        return markdown
    
    def _generate_summary_markdown(self, coaching_plans):
        """Generate a summary markdown report of all coaching plans"""
        markdown = "# Coaching Plans Summary\n\n"
        
        markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        markdown += f"**Number of Team Members:** {len(coaching_plans)}\n\n"
        
        # Calculate totals
        total_focus_areas = sum(len(plan["focus_areas"]) for plan in coaching_plans)
        total_sessions = sum(len(plan["coaching_sessions"]) for plan in coaching_plans)
        
        # Count focus area types
        focus_area_types = {}
        for plan in coaching_plans:
            for area in plan["focus_areas"]:
                area_type = area["type"]
                focus_area_types[area_type] = focus_area_types.get(area_type, 0) + 1
        
        markdown += "## Coaching Overview\n\n"
        markdown += f"- **Total Focus Areas:** {total_focus_areas}\n"
        markdown += f"- **Total Coaching Sessions:** {total_sessions}\n\n"
        
        markdown += "## Focus Area Types\n\n"
        for area_type, count in focus_area_types.items():
            markdown += f"- **{area_type}:** {count} ({int(count/total_focus_areas*100)}%)\n"
        markdown += "\n"
        
        # Team member summaries
        markdown += "## Team Member Summaries\n\n"
        for plan in coaching_plans:
            member_name = plan["member_name"]
            role = plan["role"]
            
            focus_areas = [area["title"] for area in plan["focus_areas"]]
            focus_areas_str = ", ".join(focus_areas)
            
            markdown += f"### {member_name} ({role})\n\n"
            markdown += f"- **Focus Areas:** {focus_areas_str}\n"
            markdown += f"- **Number of Sessions:** {len(plan['coaching_sessions'])}\n"
            markdown += f"- **Check-in Frequency:** {plan['check_in_frequency']}\n\n"
        
        return markdown
