import os
import json
import random
from agent.step_base import StepBase

class DataAnalysisStep(StepBase):
    """
    Implementation of the Data Analysis step.
    
    This step analyzes performance data to identify trends and areas for improvement.
    """
    
    def execute(self) -> bool:
        """
        Execute the step.
        
        Returns:
            bool: True if the step was successful, False otherwise.
        """
        self.logger.info("Executing Data Analysis step")
        
        # Create sample data if it doesn't exist
        if not self.list_input_files():
            self._create_sample_data()
        
        # Analyze the data
        team_data = self._load_team_data()
        analysis_results = self._analyze_data(team_data)
        
        # Write the analysis results
        self.write_output_file("analysis_results.json", json.dumps(analysis_results, indent=2))
        self.write_output_file("analysis_summary.md", self._generate_summary(analysis_results))
        
        return True
    
    def _create_sample_data(self) -> None:
        """Create sample data for demonstration purposes"""
        team_members = [
            {"id": 1, "name": "John Smith", "role": "Software Engineer"},
            {"id": 2, "name": "Emily Johnson", "role": "UX Designer"},
            {"id": 3, "name": "Michael Brown", "role": "Product Manager"},
            {"id": 4, "name": "Sarah Davis", "role": "Data Scientist"},
            {"id": 5, "name": "David Wilson", "role": "DevOps Engineer"}
        ]
        
        metrics = [
            "code_quality", "productivity", "collaboration", 
            "innovation", "reliability", "customer_focus"
        ]
        
        # Generate random performance data for each team member
        team_data = []
        for member in team_members:
            performance = {}
            for metric in metrics:
                # Generate scores for the last 3 quarters
                performance[metric] = {
                    "Q1": round(random.uniform(2.0, 5.0), 1),
                    "Q2": round(random.uniform(2.0, 5.0), 1),
                    "Q3": round(random.uniform(2.0, 5.0), 1)
                }
            
            # Add some projects
            projects = [
                "Customer Portal Redesign",
                "API Performance Optimization",
                "Mobile App Launch",
                "Data Pipeline Modernization",
                "Cloud Migration"
            ]
            
            member_projects = random.sample(projects, random.randint(1, 3))
            
            team_data.append({
                "member": member,
                "performance": performance,
                "projects": member_projects,
                "feedback": []  # Will be filled in later steps
            })
        
        # Save the team data
        self.write_output_file("team_data.json", json.dumps(team_data, indent=2))
    
    def _load_team_data(self) -> list:
        """Load team data from the input directory or create sample data"""
        team_data_path = self.get_input_path("team_data.json")
        
        if os.path.exists(team_data_path):
            with open(team_data_path, "r") as f:
                return json.load(f)
        
        # If no input data, check if we already created sample data
        team_data_path = self.get_output_path("team_data.json")
        
        if os.path.exists(team_data_path):
            with open(team_data_path, "r") as f:
                return json.load(f)
        
        # If we get here, we need to create sample data
        self._create_sample_data()
        
        with open(team_data_path, "r") as f:
            return json.load(f)
    
    def _analyze_data(self, team_data: list) -> dict:
        """Analyze the team performance data"""
        metrics = ["code_quality", "productivity", "collaboration", 
                  "innovation", "reliability", "customer_focus"]
        
        results = {
            "team_average": {},
            "trends": {},
            "individual_analysis": []
        }
        
        # Calculate team averages
        for metric in metrics:
            q1_total = sum(member["performance"][metric]["Q1"] for member in team_data)
            q2_total = sum(member["performance"][metric]["Q2"] for member in team_data)
            q3_total = sum(member["performance"][metric]["Q3"] for member in team_data)
            
            q1_avg = round(q1_total / len(team_data), 1)
            q2_avg = round(q2_total / len(team_data), 1)
            q3_avg = round(q3_total / len(team_data), 1)
            
            results["team_average"][metric] = {
                "Q1": q1_avg,
                "Q2": q2_avg,
                "Q3": q3_avg
            }
            
            # Calculate trends
            q1_to_q2 = round(((q2_avg - q1_avg) / q1_avg) * 100, 1) if q1_avg > 0 else 0
            q2_to_q3 = round(((q3_avg - q2_avg) / q2_avg) * 100, 1) if q2_avg > 0 else 0
            
            results["trends"][metric] = {
                "Q1_to_Q2": q1_to_q2,
                "Q2_to_Q3": q2_to_q3,
                "direction": "up" if q2_to_q3 > 0 else "down" if q2_to_q3 < 0 else "stable"
            }
        
        # Individual analysis
        for member in team_data:
            member_id = member["member"]["id"]
            member_name = member["member"]["name"]
            
            strengths = []
            improvement_areas = []
            
            # Find strengths and areas for improvement
            for metric in metrics:
                q3_score = member["performance"][metric]["Q3"]
                team_avg = results["team_average"][metric]["Q3"]
                
                if q3_score >= 4.0:
                    strengths.append(metric)
                elif q3_score <= 3.0:
                    improvement_areas.append(metric)
            
            results["individual_analysis"].append({
                "member_id": member_id,
                "member_name": member_name,
                "strengths": strengths,
                "improvement_areas": improvement_areas,
                "overall_rating": self._calculate_overall_rating(member["performance"])
            })
        
        return results
    
    def _calculate_overall_rating(self, performance: dict) -> float:
        """Calculate overall rating based on Q3 performance"""
        metrics = performance.keys()
        total = sum(performance[metric]["Q3"] for metric in metrics)
        return round(total / len(metrics), 1)
    
    def _generate_summary(self, analysis: dict) -> str:
        """Generate a markdown summary of the analysis results"""
        summary = "# Performance Data Analysis Summary\n\n"
        
        summary += "## Team Performance Trends\n\n"
        summary += "| Metric | Q1 | Q2 | Q3 | Q2→Q3 Trend |\n"
        summary += "|--------|----|----|----|-----------|\n"
        
        for metric in analysis["team_average"].keys():
            display_metric = metric.replace('_', ' ').title()
            q1 = analysis["team_average"][metric]["Q1"]
            q2 = analysis["team_average"][metric]["Q2"]
            q3 = analysis["team_average"][metric]["Q3"]
            trend = analysis["trends"][metric]["Q2_to_Q3"]
            trend_str = f"+{trend}%" if trend > 0 else f"{trend}%"
            
            summary += f"| {display_metric} | {q1} | {q2} | {q3} | {trend_str} |\n"
        
        summary += "\n## Individual Performance Highlights\n\n"
        
        for individual in analysis["individual_analysis"]:
            summary += f"### {individual['member_name']} (Overall: {individual['overall_rating']})\n\n"
            
            summary += "**Strengths:** "
            if individual["strengths"]:
                strengths = [s.replace('_', ' ').title() for s in individual["strengths"]]
                summary += ", ".join(strengths)
            else:
                summary += "None identified"
            summary += "\n\n"
            
            summary += "**Areas for Improvement:** "
            if individual["improvement_areas"]:
                areas = [a.replace('_', ' ').title() for a in individual["improvement_areas"]]
                summary += ", ".join(areas)
            else:
                summary += "None identified"
            summary += "\n\n"
        
        summary += "## Recommendations\n\n"
        summary += "1. Focus on team-wide improvements in " + self._get_lowest_metric(analysis) + "\n"
        summary += "2. Recognize and share best practices from high performers\n"
        summary += "3. Consider targeted training for individuals with specific improvement areas\n"
        summary += "4. Continue to monitor trends into the next quarter\n"
        
        return summary
    
    def _get_lowest_metric(self, analysis: dict) -> str:
        """Get the lowest performing metric for the team"""
        metrics = analysis["team_average"].keys()
        lowest_metric = None
        lowest_score = float('inf')
        
        for metric in metrics:
            score = analysis["team_average"][metric]["Q3"]
            if score < lowest_score:
                lowest_score = score
                lowest_metric = metric
        
        return lowest_metric.replace('_', ' ').title() if lowest_metric else "all areas"
