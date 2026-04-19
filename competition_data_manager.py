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
        self.lock = threading.RLock()
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
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self.initialize_data()
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
    
    def save_data(self, data: dict):
        """Save competition data to file"""
        with self.lock:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def get_data_version(self) -> int:
        """Return a lightweight change token for the competition dataset."""
        try:
            return int(os.path.getmtime(self.data_file) * 1000)
        except Exception:
            return int(datetime.now().timestamp() * 1000)
    
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
                "best_result": None,
                "judge_approval": "pending",
                "judge_approval_time": None,
                "review_status": None,
                "review_requested_at": None,
                "review_locked_by": None,
                "review_locked_at": None,
                "review_completed_at": None,
                "review_completed_by": None,
                "review_last_opened_at": None
            }
        
        problem_data = data["competitors"][name]["problems"][str(problem_id)]
        problem_data["submissions"].append(submission)
        
        # Update best result if this is better
        current_best = problem_data["best_result"]
        if current_best is None or submission["passed_tests"] > current_best.get("passed_tests", 0):
            problem_data["best_result"] = submission

        # Any new submission should return to the review queue.
        problem_data["judge_approval"] = "pending"
        problem_data["judge_approval_time"] = None
        problem_data["review_status"] = "pending_review"
        problem_data["review_requested_at"] = submission["submitted_at"]
        problem_data["review_locked_by"] = None
        problem_data["review_locked_at"] = None
        problem_data["review_completed_at"] = None
        problem_data["review_completed_by"] = None
        
        data["competitors"][name]["last_activity"] = datetime.now().isoformat()
        self.save_data(data)
        return True

    def _normalize_review_status(self, problem_data: dict) -> str:
        """Normalize review status across old and new schemas."""
        explicit_status = problem_data.get("review_status")
        if explicit_status in ["pending_review", "under_review", "reviewed"]:
            return explicit_status

        judge_approval = problem_data.get("judge_approval")
        if judge_approval in ["approved", "rejected"]:
            return "reviewed"

        if problem_data.get("submissions", []):
            return "pending_review"

        return "not_ready"

    def get_review_queue(self) -> List[dict]:
        """Return all submitted problems as review queue entries."""
        data = self.load_data()
        queue = []

        for competitor_name, competitor_data in data.get("competitors", {}).items():
            for problem_id, problem_data in competitor_data.get("problems", {}).items():
                submissions = problem_data.get("submissions", [])
                if not submissions:
                    continue

                latest_submission = submissions[-1] if submissions else {}
                queue.append({
                    "competitor": competitor_name,
                    "problem_id": int(problem_id) if str(problem_id).isdigit() else problem_id,
                    "review_status": self._normalize_review_status(problem_data),
                    "judge_approval": problem_data.get("judge_approval", "pending"),
                    "locked_by": problem_data.get("review_locked_by"),
                    "locked_at": problem_data.get("review_locked_at"),
                    "reviewed_at": problem_data.get("review_completed_at") or problem_data.get("judge_approval_time"),
                    "submitted_at": latest_submission.get("submitted_at", latest_submission.get("timestamp")),
                    "attempts": len(submissions),
                    "passed_tests": latest_submission.get("passed_tests", latest_submission.get("tests_passed", 0)),
                    "total_tests": latest_submission.get("total_tests", 0),
                    "all_passed": latest_submission.get("all_passed", False),
                    "level": competitor_data.get("level"),
                    "week": competitor_data.get("week")
                })

        status_order = {
            "pending_review": 0,
            "under_review": 1,
            "reviewed": 2
        }

        def sort_timestamp(entry):
            timestamp = entry.get("submitted_at")
            if not timestamp:
                return 0.0
            try:
                parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                return parsed.timestamp()
            except Exception:
                return 0.0

        queue.sort(key=sort_timestamp, reverse=True)
        queue.sort(key=lambda entry: status_order.get(entry.get("review_status"), 99))
        return queue

    def start_problem_review(self, name: str, problem_id: int, judge_id: str) -> dict:
        """Lock a submitted problem for review so only one judge can access it."""
        try:
            with self.lock:
                data = self.load_data()

                if name not in data["competitors"]:
                    return {
                        "success": False,
                        "message": f"Competitor {name} not found"
                    }

                problem_id_str = str(problem_id)
                problems = data["competitors"][name].get("problems", {})
                if problem_id_str not in problems:
                    return {
                        "success": False,
                        "message": f"Problem {problem_id} not found for {name}"
                    }

                problem_data = problems[problem_id_str]
                submissions = problem_data.get("submissions", [])
                if not submissions:
                    return {
                        "success": False,
                        "message": "Only submitted problems can be reviewed"
                    }

                review_status = self._normalize_review_status(problem_data)
                lock_owner = problem_data.get("review_locked_by")

                if review_status == "under_review":
                    if lock_owner == judge_id:
                        return {
                            "success": True,
                            "message": "Already assigned to you"
                        }
                    owner_label = lock_owner or "another judge"
                    return {
                        "success": False,
                        "message": f"This entry is currently under review by {owner_label}"
                    }

                if review_status == "reviewed":
                    return {
                        "success": False,
                        "message": "This entry has already been reviewed"
                    }

                now = datetime.now().isoformat()
                problem_data["review_status"] = "under_review"
                problem_data["review_locked_by"] = judge_id
                problem_data["review_locked_at"] = now
                problem_data["review_last_opened_at"] = now

                self.save_data(data)

                return {
                    "success": True,
                    "message": "Submission moved to under review"
                }
        except Exception as e:
            print(f"[ERROR] Failed to lock problem for review: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": "Failed to lock submission for review"
            }
    
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
            approved_problems = 0
            rejected_problems = 0
            total_tests_passed = 0
            total_submissions = 0
            
            for problem_id, problem_data in competitor["problems"].items():
                judge_approval = problem_data.get("judge_approval")
                
                if problem_data.get("best_result", {}).get("all_passed", False):
                    total_solved += 1
                    # Count as approved only if judge approved
                    if judge_approval == 'approved':
                        approved_problems += 1
                    elif judge_approval == 'rejected':
                        rejected_problems += 1
                
                total_tests_passed += problem_data.get("best_result", {}).get("passed_tests", 0)
                total_submissions += len(problem_data.get("submissions", []))
            
            leaderboard.append({
                "name": name,
                "problems_solved": total_solved,
                "approved_problems": approved_problems,  # Judge approved count
                "rejected_problems": rejected_problems,  # Judge rejected count
                "total_tests_passed": total_tests_passed,
                "total_submissions": total_submissions,
                "current_problem": competitor.get("current_problem", 1),
                "last_activity": competitor.get("last_activity", "")
            })
        
        # Sort by approved problems (desc), then by problems solved (desc), then by total tests passed (desc)
        leaderboard.sort(key=lambda x: (-x["approved_problems"], -x["problems_solved"], -x["total_tests_passed"]))
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
    
    def set_judge_approval(self, name: str, problem_id: int, status: str, judge_id: str = None):
        """Set judge approval status for a problem (approved/rejected)"""
        try:
            data = self.load_data()
            
            if name not in data["competitors"]:
                print(f"[ERROR] Competitor {name} not found")
                return False
            
            problem_id_str = str(problem_id)
            if "problems" not in data["competitors"][name]:
                data["competitors"][name]["problems"] = {}
            
            # Check if problem has been submitted
            if problem_id_str not in data["competitors"][name]["problems"]:
                print(f"[WARNING] Problem {problem_id_str} not found for {name}. Available: {list(data['competitors'][name]['problems'].keys())}")
                return False

            problem_data = data["competitors"][name]["problems"][problem_id_str]
            review_status = self._normalize_review_status(problem_data)
            lock_owner = problem_data.get("review_locked_by")
            if review_status == "under_review" and lock_owner and judge_id and lock_owner != judge_id:
                print(f"[WARNING] Problem {problem_id_str} is locked by another judge: {lock_owner}")
                return False

            now = datetime.now().isoformat()
            problem_data["judge_approval"] = status
            problem_data["judge_approval_time"] = now
            problem_data["review_status"] = "reviewed"
            problem_data["review_completed_at"] = now
            if judge_id:
                problem_data["review_completed_by"] = judge_id
            elif lock_owner:
                problem_data["review_completed_by"] = lock_owner
            problem_data["review_locked_by"] = None
            problem_data["review_locked_at"] = None
            
            self.save_data(data)
            print(f"[OK] Set judge approval for {name} - Problem {problem_id}: {status}")
            
            # Verify
            verify_data = self.load_data()
            verify_status = verify_data["competitors"][name]["problems"][problem_id_str].get("judge_approval")
            print(f"[VERIFY] Judge approval status is now: {verify_status}")
            
            return verify_status == status
        except Exception as e:
            print(f"[ERROR] Failed to set judge approval: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_name_taken(self, name: str) -> bool:
        """Check if a competitor name is already taken"""
        data = self.load_data()
        return name in data["competitors"]
