# -*- coding: utf-8 -*-
"""
Competition Data Manager
Handles shared data storage and synchronization for the competition system
"""
import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional


class CompetitionDataManager:
    """Manages competition data with thread-safe operations"""
    
    def __init__(self, data_file="competition_data.json"):
        self.data_file = data_file
        self.lock = threading.Lock()
        self.initialize_data()
    
    def initialize_data(self):
        """Initialize the data file if it doesn't exist"""
        if not os.path.exists(self.data_file):
            initial_data = {
                "competition_started": False,
                "start_time": None,
                "competitors": {},
                "problems_loaded": []
            }
            self.save_data(initial_data)
    
    def load_data(self) -> dict:
        """Load competition data from file"""
        with self.lock:
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self.initialize_data()
                with open(self.data_file, 'r') as f:
                    return json.load(f)
    
    def save_data(self, data: dict):
        """Save competition data to file"""
        with self.lock:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def start_competition(self):
        """Mark competition as started"""
        data = self.load_data()
        data["competition_started"] = True
        data["start_time"] = datetime.now().isoformat()
        self.save_data(data)
    
    def register_competitor(self, name: str) -> bool:
        """Register a new competitor"""
        data = self.load_data()
        
        if name in data["competitors"]:
            return False  # Competitor already exists
        
        data["competitors"][name] = {
            "name": name,
            "joined_at": datetime.now().isoformat(),
            "current_problem": 1,
            "problems": {},
            "last_activity": datetime.now().isoformat()
        }
        self.save_data(data)
        return True
    
    def update_competitor_problem(self, name: str, problem_id: int):
        """Update which problem the competitor is currently viewing"""
        data = self.load_data()
        
        if name in data["competitors"]:
            data["competitors"][name]["current_problem"] = problem_id
            data["competitors"][name]["last_activity"] = datetime.now().isoformat()
            self.save_data(data)
    
    def submit_solution(self, name: str, problem_id: int, code: str, 
                       test_results: List[dict], all_passed: bool):
        """Record a solution submission"""
        data = self.load_data()
        
        if name not in data["competitors"]:
            return False
        
        submission = {
            "code": code,
            "submitted_at": datetime.now().isoformat(),
            "test_results": test_results,
            "all_passed": all_passed,
            "total_tests": len(test_results),
            "passed_tests": sum(1 for t in test_results if t.get("passed", False))
        }
        
        # Keep submission history
        if str(problem_id) not in data["competitors"][name]["problems"]:
            data["competitors"][name]["problems"][str(problem_id)] = {
                "submissions": [],
                "best_result": None
            }
        
        data["competitors"][name]["problems"][str(problem_id)]["submissions"].append(submission)
        
        # Update best result if this is better
        current_best = data["competitors"][name]["problems"][str(problem_id)]["best_result"]
        if current_best is None or submission["passed_tests"] > current_best.get("passed_tests", 0):
            data["competitors"][name]["problems"][str(problem_id)]["best_result"] = submission
        
        data["competitors"][name]["last_activity"] = datetime.now().isoformat()
        self.save_data(data)
        return True
    
    def get_competitor_data(self, name: str) -> Optional[dict]:
        """Get data for a specific competitor"""
        data = self.load_data()
        return data["competitors"].get(name)
    
    def get_all_competitors(self) -> Dict[str, dict]:
        """Get data for all competitors"""
        data = self.load_data()
        return data["competitors"]
    
    def get_leaderboard(self) -> List[dict]:
        """Generate leaderboard data"""
        data = self.load_data()
        leaderboard = []
        
        for name, competitor in data["competitors"].items():
            total_solved = 0
            total_tests_passed = 0
            total_submissions = 0
            
            for problem_id, problem_data in competitor["problems"].items():
                if problem_data.get("best_result", {}).get("all_passed", False):
                    total_solved += 1
                total_tests_passed += problem_data.get("best_result", {}).get("passed_tests", 0)
                total_submissions += len(problem_data.get("submissions", []))
            
            leaderboard.append({
                "name": name,
                "problems_solved": total_solved,
                "total_tests_passed": total_tests_passed,
                "total_submissions": total_submissions,
                "current_problem": competitor.get("current_problem", 1),
                "last_activity": competitor.get("last_activity", "")
            })
        
        # Sort by problems solved (desc), then by total tests passed (desc)
        leaderboard.sort(key=lambda x: (-x["problems_solved"], -x["total_tests_passed"]))
        return leaderboard
    
    def get_problem_statistics(self) -> dict:
        """Get statistics for each problem"""
        data = self.load_data()
        stats = {}
        
        for name, competitor in data["competitors"].items():
            for problem_id, problem_data in competitor["problems"].items():
                if problem_id not in stats:
                    stats[problem_id] = {
                        "total_attempts": 0,
                        "total_solvers": 0,
                        "total_submissions": 0
                    }
                
                stats[problem_id]["total_attempts"] += 1
                stats[problem_id]["total_submissions"] += len(problem_data.get("submissions", []))
                
                if problem_data.get("best_result", {}).get("all_passed", False):
                    stats[problem_id]["total_solvers"] += 1
        
        return stats
    
    def reset_competition(self):
        """Reset all competition data"""
        initial_data = {
            "competition_started": False,
            "start_time": None,
            "competitors": {},
            "problems_loaded": []
        }
        self.save_data(initial_data)
    
    def is_name_taken(self, name: str) -> bool:
        """Check if a competitor name is already taken"""
        data = self.load_data()
        return name in data["competitors"]
