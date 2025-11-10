# -*- coding: utf-8 -*-
"""
Firebase Data Manager
Handles shared data storage using Firebase Firestore for multi-device competition system
"""
import threading
from datetime import datetime
from typing import Dict, List, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_config import FirebaseConfig


class FirebaseDataManager:
    """Manages competition data using Firebase Firestore with real-time synchronization"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one Firebase connection"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase connection"""
        if not hasattr(self, 'initialized'):
            self.initialized = False
            self.db = None
            self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if self.initialized:
            return
        
        try:
            # Check if already initialized
            firebase_admin.get_app()
        except ValueError:
            # Not initialized, so initialize it
            creds_dict = FirebaseConfig.load_credentials()
            
            if not creds_dict:
                raise Exception(
                    "Firebase credentials not found! Please create 'firebase_credentials.json' "
                    "with your Firebase service account credentials.\n"
                    "Get it from: Firebase Console > Project Settings > Service Accounts > Generate New Private Key"
                )
            
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        self.db = firestore.client()
        self.initialized = True
        
        # Collection references
        self.competitors_ref = self.db.collection('competitors')
        self.competition_ref = self.db.collection('competition')
        self.problems_ref = self.db.collection('problems')
        
        # Initialize competition metadata if not exists
        self._initialize_competition_metadata()
    
    def _initialize_competition_metadata(self):
        """Initialize competition metadata document"""
        try:
            doc_ref = self.competition_ref.document('metadata')
            doc = doc_ref.get()
            
            if not doc.exists:
                doc_ref.set({
                    'competition_started': False,
                    'start_time': None,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'problems_loaded': []
                })
        except Exception as e:
            print(f"Error initializing competition metadata: {e}")
    
    def start_competition(self):
        """Mark competition as started"""
        try:
            doc_ref = self.competition_ref.document('metadata')
            doc_ref.update({
                'competition_started': True,
                'start_time': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error starting competition: {e}")
    
    def register_competitor(self, name: str) -> bool:
        """Register a new competitor"""
        try:
            # Check if competitor exists
            doc_ref = self.competitors_ref.document(name)
            doc = doc_ref.get()
            
            if doc.exists:
                return False  # Competitor already exists
            
            # Create new competitor
            doc_ref.set({
                'name': name,
                'joined_at': datetime.now().isoformat(),
                'current_problem': 1,
                'problems': {},
                'last_activity': datetime.now().isoformat(),
                'created_at': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error registering competitor: {e}")
            return False
    
    def update_competitor_problem(self, name: str, problem_id: int):
        """Update which problem the competitor is currently viewing"""
        try:
            doc_ref = self.competitors_ref.document(name)
            doc_ref.update({
                'current_problem': problem_id,
                'last_activity': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error updating competitor problem: {e}")
    
    def submit_solution(self, name: str, problem_id: int, code: str, 
                       test_results: List[dict], all_passed: bool):
        """Record a solution submission"""
        try:
            doc_ref = self.competitors_ref.document(name)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            competitor_data = doc.to_dict()
            
            submission = {
                'code': code,
                'submitted_at': datetime.now().isoformat(),
                'test_results': test_results,
                'all_passed': all_passed,
                'total_tests': len(test_results),
                'passed_tests': sum(1 for t in test_results if t.get('passed', False))
            }
            
            # Initialize problem data if not exists
            problems = competitor_data.get('problems', {})
            problem_key = str(problem_id)
            
            if problem_key not in problems:
                problems[problem_key] = {
                    'submissions': [],
                    'best_result': None
                }
            
            # Add submission
            problems[problem_key]['submissions'].append(submission)
            
            # Update best result if this is better
            current_best = problems[problem_key]['best_result']
            if current_best is None or submission['passed_tests'] > current_best.get('passed_tests', 0):
                problems[problem_key]['best_result'] = submission
            
            # Update document
            doc_ref.update({
                'problems': problems,
                'last_activity': datetime.now().isoformat()
            })
            
            return True
        except Exception as e:
            print(f"Error submitting solution: {e}")
            return False
    
    def get_competitor_data(self, name: str) -> Optional[dict]:
        """Get data for a specific competitor"""
        try:
            doc_ref = self.competitors_ref.document(name)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting competitor data: {e}")
            return None
    
    def get_all_competitors(self) -> Dict[str, dict]:
        """Get data for all competitors"""
        try:
            competitors = {}
            docs = self.competitors_ref.stream()
            
            for doc in docs:
                competitors[doc.id] = doc.to_dict()
            
            return competitors
        except Exception as e:
            print(f"Error getting all competitors: {e}")
            return {}
    
    def get_leaderboard(self) -> List[dict]:
        """Generate leaderboard data"""
        try:
            competitors = self.get_all_competitors()
            leaderboard = []
            
            for name, competitor in competitors.items():
                total_solved = 0
                total_tests_passed = 0
                total_submissions = 0
                
                problems = competitor.get('problems', {})
                for problem_id, problem_data in problems.items():
                    best_result = problem_data.get('best_result', {})
                    if best_result and best_result.get('all_passed', False):
                        total_solved += 1
                    if best_result:
                        total_tests_passed += best_result.get('passed_tests', 0)
                    total_submissions += len(problem_data.get('submissions', []))
                
                leaderboard.append({
                    'name': name,
                    'problems_solved': total_solved,
                    'total_tests_passed': total_tests_passed,
                    'total_submissions': total_submissions,
                    'current_problem': competitor.get('current_problem', 1),
                    'last_activity': competitor.get('last_activity', '')
                })
            
            # Sort by problems solved (desc), then by total tests passed (desc)
            leaderboard.sort(key=lambda x: (-x['problems_solved'], -x['total_tests_passed']))
            return leaderboard
        except Exception as e:
            print(f"Error generating leaderboard: {e}")
            return []
    
    def get_problem_statistics(self) -> dict:
        """Get statistics for each problem"""
        try:
            competitors = self.get_all_competitors()
            stats = {}
            
            for name, competitor in competitors.items():
                problems = competitor.get('problems', {})
                for problem_id, problem_data in problems.items():
                    if problem_id not in stats:
                        stats[problem_id] = {
                            'total_attempts': 0,
                            'total_solvers': 0,
                            'total_submissions': 0
                        }
                    
                    stats[problem_id]['total_attempts'] += 1
                    stats[problem_id]['total_submissions'] += len(problem_data.get('submissions', []))
                    
                    best_result = problem_data.get('best_result', {})
                    if best_result and best_result.get('all_passed', False):
                        stats[problem_id]['total_solvers'] += 1
            
            return stats
        except Exception as e:
            print(f"Error getting problem statistics: {e}")
            return {}
    
    def reset_competition(self):
        """Reset all competition data"""
        try:
            # Delete all competitor documents
            docs = self.competitors_ref.stream()
            for doc in docs:
                doc.reference.delete()
            
            # Reset competition metadata
            doc_ref = self.competition_ref.document('metadata')
            doc_ref.set({
                'competition_started': False,
                'start_time': None,
                'created_at': firestore.SERVER_TIMESTAMP,
                'problems_loaded': []
            })
            
            print("Competition data reset successfully")
        except Exception as e:
            print(f"Error resetting competition: {e}")
    
    def is_name_taken(self, name: str) -> bool:
        """Check if a competitor name is already taken"""
        try:
            doc_ref = self.competitors_ref.document(name)
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            print(f"Error checking name: {e}")
            return False
    
    def add_listener(self, callback):
        """
        Add a real-time listener for competitor updates
        callback: function(snapshot, changes, read_time)
        """
        try:
            return self.competitors_ref.on_snapshot(callback)
        except Exception as e:
            print(f"Error adding listener: {e}")
            return None
