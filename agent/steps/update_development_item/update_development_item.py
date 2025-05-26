import os
import json
import random
from datetime import datetime
from agent.step_base import StepBase

class UpdateDevelopmentItemStep(StepBase):
    """
    Implementation of the Update Development Item step.
    
    This step updates existing development items based on employee progress and feedback.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        self.logger.info("Executing Update Development Item step")
        
        # Read original development items from the create_development_item step
        development_items_path = os.path.join(
            os.path.dirname(os.path.dirname(self.input_dir)),
            "create_development_item",
            "out",
            "development_items.json"
        )
        
        if not os.path.exists(development_items_path):
            self.logger.error("Development items not found. Please run create_development_item step first.")
            return False
        
        # Load development items
        with open(development_items_path, "r") as f:
            original_items = json.load(f)
        
        # Generate progress data for each development item
        updated_items = self._update_development_items(original_items)
        
        # Write updated development items to output
        self.write_output_file("updated_development_items.json", json.dumps(updated_items, indent=2))
        
        # Also write a markdown summary for each team member
        for member_items in updated_items:
            member_name = member_items["member_name"].replace(" ", "_").lower()
            self.write_output_file(
                f"{member_name}_updated_development.md",
                self._generate_updated_development_markdown(member_items)
            )
        
        # Write a summary markdown file
        self.write_output_file(
            "updated_development_summary.md",
            self._generate_summary_markdown(updated_items)
        )
        
        return True
    
    def _update_development_items(self, original_items):
        """Update development items for each team member with progress data"""
        updated_items = []
        
        for member_items in original_items:
            member_id = member_items["member_id"]
            member_name = member_items["member_name"]
            role = member_items["role"]
            
            # Update development items with progress
            updated_member_items = []
            for item in member_items["items"]:
                # Generate random progress (weighted toward progress since last check-in)
                progress = random.randint(20, 90)
                status = "In Progress"
                if progress < 35:
                    status = "Not Started"
                elif progress >= 75:
                    status = "Completed"
                elif progress >= 50:
                    status = "Advanced"
                
                # Determine if modifications are needed
                needs_modification = random.random() < 0.3  # 30% chance of needing modification
                
                updated_item = item.copy()
                updated_item.update({
                    "progress": progress,
                    "status": status,
                    "comments": self._generate_progress_comment(item["title"], progress),
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "needs_modification": needs_modification,
                    "modification_reason": self._generate_modification_reason(item, needs_modification)
                })
                
                if needs_modification:
                    updated_item["suggested_modifications"] = self._generate_suggested_modifications(item, role)
                
                updated_member_items.append(updated_item)
            
            # Create the updated items
            updated_items.append({
                "member_id": member_id,
                "member_name": member_name,
                "role": role,
                "items": updated_member_items,
                "overall_progress": self._calculate_overall_progress(updated_member_items),
                "needs_additional_items": self._determine_if_additional_items_needed(updated_member_items),
                "suggested_additional_items": self._generate_additional_items(updated_member_items, role)
            })
        
        return updated_items
    
    def _generate_progress_comment(self, title, progress):
        """Generate a comment based on the progress of a development item"""
        if progress < 35:
            comments = [
                f"Not yet started on {title}. Will prioritize in the coming weeks.",
                f"Initial planning for {title} is underway, but formal work hasn't begun.",
                f"Still gathering resources to begin {title}."
            ]
        elif progress < 50:
            comments = [
                f"Early stages of work on {title}. Making steady progress.",
                f"Started {title} but progress is slower than expected due to competing priorities.",
                f"Working through initial challenges with {title}."
            ]
        elif progress < 75:
            comments = [
                f"Good progress on {title}. Key concepts have been mastered.",
                f"Moving forward well with {title}. Some advanced topics still to cover.",
                f"Significant advancement in {title}. Applying new skills in daily work."
            ]
        else:
            comments = [
                f"Nearly complete with {title}. Only final refinement needed.",
                f"Successfully completed most aspects of {title}. Looking for opportunities to share knowledge.",
                f"Excellent progress on {title}. Ready to move to more advanced topics."
            ]
        return random.choice(comments)
    
    def _generate_modification_reason(self, item, needs_modification):
        """Generate a reason for modification if needed"""
        if not needs_modification:
            return None
        
        reasons = [
            "Current approach is not yielding expected results",
            "New project requirements necessitate a shift in focus",
            "More specialized knowledge is required than originally anticipated",
            "Found more efficient learning resources",
            "Time constraints require a more focused approach"
        ]
        return random.choice(reasons)
    
    def _generate_suggested_modifications(self, item, role):
        """Generate suggested modifications for a development item"""
        if "Technical Skill" in item["type"]:
            modifications = [
                "Focus on practical application rather than theoretical knowledge",
                "Add pair programming sessions with a senior developer",
                "Substitute the online course with a more hands-on workshop"
            ]
        elif "Leadership" in item["type"]:
            modifications = [
                "Add shadowing opportunities with senior leaders",
                "Include facilitation of team retrospectives for practical experience",
                "Focus on specific leadership scenarios relevant to current team challenges"
            ]
        elif "Communication" in item["type"]:
            modifications = [
                "Include more presentation opportunities in team meetings",
                "Add documentation writing exercises for technical concepts",
                "Focus on stakeholder communication specifically"
            ]
        else:
            modifications = [
                "Make the learning more project-specific",
                "Include more regular check-ins to assess progress",
                "Break down into smaller, more manageable milestones"
            ]
        
        return random.choice(modifications)
    
    def _calculate_overall_progress(self, items):
        """Calculate the overall progress across all development items"""
        if not items:
            return 0
        
        total_progress = sum(item["progress"] for item in items)
        return int(total_progress / len(items))
    
    def _determine_if_additional_items_needed(self, items):
        """Determine if additional development items are needed"""
        completed_items = len([item for item in items if item["status"] == "Completed"])
        return completed_items > len(items) / 2
    
    def _generate_additional_items(self, current_items, role):
        """Generate additional development items if needed"""
        if not self._determine_if_additional_items_needed(current_items):
            return []
        
        additional_items = []
        
        # Check for item types that might be missing
        current_types = set(item["type"] for item in current_items)
        
        if "Technical Skill" not in current_types and role in ["Software Engineer", "Data Scientist", "DevOps Engineer"]:
            additional_items.append({
                "title": f"Advanced {role} Techniques",
                "type": "Technical Skill",
                "description": f"Develop expertise in advanced techniques specific to {role} responsibilities.",
                "suggested_actions": [
                    f"Complete an advanced certification in {role} specialization",
                    "Apply new techniques to current projects",
                    "Create knowledge-sharing sessions for the team"
                ]
            })
        
        if "Leadership" not in current_types:
            additional_items.append({
                "title": "Strategic Thinking Development",
                "type": "Leadership",
                "description": "Enhance ability to think strategically about team and project direction.",
                "suggested_actions": [
                    "Participate in strategic planning sessions",
                    "Lead a small cross-functional initiative",
                    "Create a long-term vision document for your area of responsibility"
                ]
            })
        
        if "Communication" not in current_types:
            additional_items.append({
                "title": "Stakeholder Communication",
                "type": "Communication",
                "description": "Improve ability to communicate effectively with diverse stakeholders.",
                "suggested_actions": [
                    "Lead presentations to senior leadership",
                    "Create communication plan for a project",
                    "Gather and incorporate feedback on communication style"
                ]
            })
        
        return additional_items
    
    def _generate_updated_development_markdown(self, member_items):
        """Generate a markdown report of the updated development items for a team member"""
        member_name = member_items["member_name"]
        role = member_items["role"]
        overall_progress = member_items["overall_progress"]
        
        markdown = f"# Updated Development Plan for {member_name}\n\n"
        markdown += f"**Role:** {role}\n\n"
        markdown += f"**Overall Progress:** {overall_progress}%\n\n"
        
        markdown += "## Development Items Progress\n\n"
        for item in member_items["items"]:
            markdown += f"### {item['title']} - {item['status']} ({item['progress']}%)\n\n"
            markdown += f"**Type:** {item['type']}\n\n"
            markdown += f"**Description:** {item['description']}\n\n"
            markdown += f"**Comments:** {item['comments']}\n\n"
            markdown += f"**Last Updated:** {item['last_updated']}\n\n"
            
            if item["needs_modification"]:
                markdown += f"**Needs Modification:** Yes\n\n"
                markdown += f"**Reason:** {item['modification_reason']}\n\n"
                markdown += f"**Suggested Modification:** {item['suggested_modifications']}\n\n"
            else:
                markdown += f"**Needs Modification:** No\n\n"
        
        if member_items["needs_additional_items"] and member_items["suggested_additional_items"]:
            markdown += "## Suggested Additional Development Items\n\n"
            for item in member_items["suggested_additional_items"]:
                markdown += f"### {item['title']}\n\n"
                markdown += f"**Type:** {item['type']}\n\n"
                markdown += f"**Description:** {item['description']}\n\n"
                markdown += "**Suggested Actions:**\n\n"
                for action in item["suggested_actions"]:
                    markdown += f"- {action}\n"
                markdown += "\n"
        
        return markdown
    
    def _generate_summary_markdown(self, updated_items):
        """Generate a summary markdown report of all updated development items"""
        markdown = "# Development Items Update Summary\n\n"
        
        markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        markdown += f"**Number of Team Members:** {len(updated_items)}\n\n"
        
        # Overall progress statistics
        all_items = []
        for member_items in updated_items:
            all_items.extend(member_items["items"])
        
        not_started = len([i for i in all_items if i["status"] == "Not Started"])
        in_progress = len([i for i in all_items if i["status"] == "In Progress"])
        advanced = len([i for i in all_items if i["status"] == "Advanced"])
        completed = len([i for i in all_items if i["status"] == "Completed"])
        total = len(all_items)
        
        markdown += "## Overall Progress\n\n"
        markdown += f"- **Not Started:** {not_started} ({int(not_started/total*100)}%)\n"
        markdown += f"- **In Progress:** {in_progress} ({int(in_progress/total*100)}%)\n"
        markdown += f"- **Advanced:** {advanced} ({int(advanced/total*100)}%)\n"
        markdown += f"- **Completed:** {completed} ({int(completed/total*100)}%)\n\n"
        
        # Team member summaries
        markdown += "## Team Member Summaries\n\n"
        for items in updated_items:
            member_name = items["member_name"]
            role = items["role"]
            overall_progress = items["overall_progress"]
            
            member_items = items["items"]
            member_not_started = len([i for i in member_items if i["status"] == "Not Started"])
            member_in_progress = len([i for i in member_items if i["status"] == "In Progress"])
            member_advanced = len([i for i in member_items if i["status"] == "Advanced"])
            member_completed = len([i for i in member_items if i["status"] == "Completed"])
            
            markdown += f"### {member_name} ({role})\n\n"
            markdown += f"- **Overall Progress:** {overall_progress}%\n"
            markdown += f"- **Items Not Started:** {member_not_started}\n"
            markdown += f"- **Items In Progress:** {member_in_progress}\n"
            markdown += f"- **Items Advanced:** {member_advanced}\n"
            markdown += f"- **Items Completed:** {member_completed}\n"
            markdown += f"- **Needs Additional Items:** {'Yes' if items['needs_additional_items'] else 'No'}\n\n"
        
        return markdown
