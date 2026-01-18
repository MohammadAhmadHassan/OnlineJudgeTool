# -*- coding: utf-8 -*-
"""
Unified Data Manager
Automatically uses Firebase if configured, falls back to local JSON storage
"""
import os
from typing import Dict, List, Optional
from firebase_config import FirebaseConfig


class DataManager:
    """
    Unified data manager that automatically chooses between Firebase and local JSON.
    
    Priority:
    1. Firebase (if credentials are configured)
    2. Local JSON (fallback)
    """
    
    def __init__(self):
        """Initialize the appropriate data manager"""
        self.backend = None
        self.backend_type = None
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Choose and initialize the appropriate backend"""
        # Try Firebase first
        if FirebaseConfig.is_configured():
            try:
                from firebase_data_manager import FirebaseDataManager
                self.backend = FirebaseDataManager()
                self.backend_type = "firebase"
                print("[OK] Connected to Firebase Firestore")
                return
            except Exception as e:
                print(f"[WARNING] Firebase initialization failed: {e}")
                print("[INFO] Falling back to local JSON storage")
        else:
            print("[INFO] Firebase not configured, using local JSON storage")
            print("  To use Firebase: Create 'firebase_credentials.json' with your service account key")
        
        # Fallback to JSON
        from competition_data_manager import CompetitionDataManager
        self.backend = CompetitionDataManager()
        self.backend_type = "json"
    
    def get_backend_type(self) -> str:
        """Get the current backend type"""
        return self.backend_type
    
    def is_firebase(self) -> bool:
        """Check if using Firebase backend"""
        return self.backend_type == "firebase"
    
    def is_json(self) -> bool:
        """Check if using JSON backend"""
        return self.backend_type == "json"
    
    # Proxy all methods to the backend
    
    def start_competition(self):
        """Mark competition as started"""
        return self.backend.start_competition()
    
    def register_competitor(self, name: str) -> bool:
        """Register a new competitor"""
        return self.backend.register_competitor(name)
    
    def update_competitor_problem(self, name: str, problem_id: int):
        """Update which problem the competitor is currently viewing"""
        return self.backend.update_competitor_problem(name, problem_id)
    
    def submit_solution(self, name: str, problem_id: int, code: str, 
                       test_results: List[dict], all_passed: bool):
        """Record a solution submission"""
        return self.backend.submit_solution(name, problem_id, code, test_results, all_passed)
    
    def get_competitor_data(self, name: str) -> Optional[dict]:
        """Get data for a specific competitor"""
        return self.backend.get_competitor_data(name)
    
    def get_all_competitors(self) -> Dict[str, dict]:
        """Get data for all competitors"""
        return self.backend.get_all_competitors()
    
    def get_leaderboard(self) -> List[dict]:
        """Generate leaderboard data"""
        return self.backend.get_leaderboard()
    
    def get_problem_statistics(self) -> dict:
        """Get statistics for each problem"""
        return self.backend.get_problem_statistics()
    
    def reset_competition(self):
        """Reset all competition data"""
        return self.backend.reset_competition()
    
    def is_name_taken(self, name: str) -> bool:
        """Check if a competitor name is already taken"""
        return self.backend.is_name_taken(name)
    
    def set_judge_approval(self, name: str, problem_id: int, status: str):
        """Set judge approval status for a problem (approved/rejected)"""
        return self.backend.set_judge_approval(name, problem_id, status)
    
    def add_listener(self, callback):
        """
        Add a real-time listener (Firebase only)
        Falls back gracefully for JSON backend
        """
        if hasattr(self.backend, 'add_listener'):
            return self.backend.add_listener(callback)
        return None
    
    # ===== PROBLEM MANAGEMENT METHODS =====
    
    def upload_problems(self, problems_data: dict, session_name: str = "session1", level: int = 1) -> bool:
        """Upload problems to Firebase"""
        if hasattr(self.backend, 'upload_problems'):
            return self.backend.upload_problems(problems_data, session_name, level)
        print("[ERROR] Problem upload not supported by current backend")
        return False
    
    def get_problems(self, week: Optional[int] = None, level: Optional[int] = None) -> dict:
        """Retrieve problems, optionally filtered by week and level"""
        if hasattr(self.backend, 'get_problems'):
            return self.backend.get_problems(week=week, level=level)
        print("[ERROR] Problem retrieval not supported by current backend")
        return {}
    
    def get_problem_by_id(self, problem_id: int, week: Optional[int] = None) -> Optional[dict]:
        """Retrieve a specific problem by ID"""
        if hasattr(self.backend, 'get_problem_by_id'):
            return self.backend.get_problem_by_id(problem_id, week=week)
        return None
    
    def update_problem(self, session_name: str, problem_id: int, updates: dict) -> bool:
        """Update a specific problem"""
        if hasattr(self.backend, 'update_problem'):
            return self.backend.update_problem(session_name, problem_id, updates)
        return False
    
    def delete_problem(self, session_name: str, problem_id: int) -> bool:
        """Delete a specific problem"""
        if hasattr(self.backend, 'delete_problem'):
            return self.backend.delete_problem(session_name, problem_id)
        return False


# Convenience function for creating data manager
def create_data_manager():
    """Create and return a data manager instance"""
    return DataManager()
