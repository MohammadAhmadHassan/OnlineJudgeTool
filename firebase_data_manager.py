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
    
    def register_competitor(self, name: str, week: int = None, level: int = None) -> bool:
        """Register a new competitor"""
        try:
            # Check if competitor exists
            doc_ref = self.competitors_ref.document(name)
            doc = doc_ref.get()
            
            if doc.exists:
                return False  # Competitor already exists
            
            # Create new competitor
            competitor_data = {
                'name': name,
                'joined_at': datetime.now().isoformat(),
                'current_problem': 1,
                'problems': {},
                'last_activity': datetime.now().isoformat(),
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add week and level if provided
            if week is not None:
                competitor_data['week'] = week
            if level is not None:
                competitor_data['level'] = level
            
            doc_ref.set(competitor_data)
            return True
        except Exception as e:
            print(f"Error registering competitor: {e}")
            return False
    
    def update_competitor_level_week(self, name: str, week: int = None, level: int = None):
        """Update competitor's level and week (for migrating old data)"""
        try:
            doc_ref = self.competitors_ref.document(name)
            update_data = {'last_activity': datetime.now().isoformat()}
            
            if week is not None:
                update_data['week'] = week
            if level is not None:
                update_data['level'] = level
            
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating competitor level/week: {e}")
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
                'timestamp': datetime.now().isoformat(),
                'submitted_at': datetime.now().isoformat(),
                'test_results': test_results,
                'all_passed': all_passed,
                'total_tests': len(test_results),
                'tests_passed': sum(1 for t in test_results if t.get('passed', False)),
                'passed_tests': sum(1 for t in test_results if t.get('passed', False))
            }
            
            # Initialize problem data if not exists
            problems = competitor_data.get('problems', {})
            problem_key = str(problem_id)
            
            if problem_key not in problems:
                problems[problem_key] = {
                    'submissions': [],
                    'best_result': None,
                    'judge_approval': 'pending',  # Initialize approval status
                    'judge_approval_time': None
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
                approved_problems = 0
                total_tests_passed = 0
                total_submissions = 0
                
                problems = competitor.get('problems', {})
                rejected_problems = 0
                
                for problem_id, problem_data in problems.items():
                    best_result = problem_data.get('best_result', {})
                    judge_approval = problem_data.get('judge_approval')
                    
                    # Count as solved if all tests passed
                    if best_result and best_result.get('all_passed', False):
                        total_solved += 1
                        # Count as approved only if judge approved
                        if judge_approval == 'approved':
                            approved_problems += 1
                        elif judge_approval == 'rejected':
                            rejected_problems += 1
                    
                    if best_result:
                        total_tests_passed += best_result.get('passed_tests', 0)
                    total_submissions += len(problem_data.get('submissions', []))
                
                leaderboard.append({
                    'name': name,
                    'problems_solved': total_solved,
                    'approved_problems': approved_problems,  # Judge approved count
                    'rejected_problems': rejected_problems,  # Judge rejected count
                    'total_tests_passed': total_tests_passed,
                    'total_submissions': total_submissions,
                    'current_problem': competitor.get('current_problem', 1),
                    'last_activity': competitor.get('last_activity', '')
                })
            
            # Sort by approved problems (desc), then by problems solved (desc), then by total tests passed (desc)
            leaderboard.sort(key=lambda x: (-x['approved_problems'], -x['problems_solved'], -x['total_tests_passed']))
            
            # Debug: Print leaderboard data
            print(f"[DEBUG] Leaderboard generated with {len(leaderboard)} competitors")
            for entry in leaderboard[:3]:  # Print top 3
                score = entry['approved_problems'] - entry['rejected_problems']
                print(f"  - {entry['name']}: solved={entry['problems_solved']}, approved={entry['approved_problems']}, rejected={entry['rejected_problems']}, score={score:+d}")
            
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
    
    def set_judge_approval(self, name: str, problem_id: int, status: str):
        """Set judge approval status for a problem (approved/rejected)"""
        try:
            problem_id_str = str(problem_id)
            print(f"[DEBUG] Setting judge approval: name={name}, problem_id={problem_id} (str: {problem_id_str}), status={status}")
            
            doc_ref = self.competitors_ref.document(name)
            
            # Get current data and update it
            doc = doc_ref.get()
            if not doc.exists:
                print(f"[ERROR] Competitor {name} not found in database")
                return False
            
            data = doc.to_dict()
            problems = data.get('problems', {})
            
            print(f"[DEBUG] Available problems for {name}: {list(problems.keys())}")
            
            if problem_id_str not in problems:
                print(f"[WARNING] Problem {problem_id_str} not found for {name}. Available problems: {list(problems.keys())}")
                return False
            
            print(f"[DEBUG] Current problem data: {problems.get(problem_id_str, {}).keys()}")
            
            # Check if judge_approval field exists, if not we need to create it first
            current_approval = problems.get(problem_id_str, {}).get('judge_approval')
            if current_approval is None:
                print(f"[INFO] judge_approval field doesn't exist, creating it...")
            
            # Update using Firestore field path notation for nested updates
            # This ensures the update is properly written to Firestore
            update_dict = {
                f'problems.{problem_id_str}.judge_approval': status,
                f'problems.{problem_id_str}.judge_approval_time': datetime.now().isoformat()
            }
            
            print(f"[DEBUG] Attempting to update with: {update_dict}")
            
            # Perform the update
            doc_ref.update(update_dict)
            
            print(f"[OK] Firestore update completed for {name} - Problem {problem_id}")
            
            # Verify the update by reading back
            import time
            time.sleep(0.5)  # Small delay to ensure Firestore has processed the update
            
            verify_doc = doc_ref.get()
            if verify_doc.exists:
                verify_data = verify_doc.to_dict()
                verify_status = verify_data.get('problems', {}).get(problem_id_str, {}).get('judge_approval')
                print(f"[VERIFY] Read back judge_approval status: {verify_status}")
                if verify_status == status:
                    print(f"[SUCCESS] Verification passed! Status is now {verify_status}")
                    return True
                else:
                    print(f"[ERROR] Verification failed! Expected {status}, got {verify_status}")
                    print(f"[DEBUG] Full problem data after update: {verify_data.get('problems', {}).get(problem_id_str, {})}")
                    return False
            return True
        except Exception as e:
            print(f"[ERROR] Exception in set_judge_approval: {e}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
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
    
    def fix_missing_judge_approval_fields(self):
        """
        Utility function to add judge_approval field to all existing problems
        that don't have it. Run this once to fix existing data.
        """
        try:
            print("[INFO] Scanning for problems missing judge_approval field...")
            competitors = self.get_all_competitors()
            fixed_count = 0
            
            for name, comp_data in competitors.items():
                problems = comp_data.get('problems', {})
                doc_ref = self.competitors_ref.document(name)
                
                for problem_id, problem_data in problems.items():
                    if 'judge_approval' not in problem_data:
                        print(f"[FIX] Adding judge_approval to {name} - Problem {problem_id}")
                        # Add the missing field
                        doc_ref.update({
                            f'problems.{problem_id}.judge_approval': 'pending',
                            f'problems.{problem_id}.judge_approval_time': None
                        })
                        fixed_count += 1
            
            print(f"[SUCCESS] Fixed {fixed_count} problems with missing judge_approval fields")
            return fixed_count
        except Exception as e:
            print(f"[ERROR] Failed to fix missing fields: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    # ===== PROBLEM MANAGEMENT METHODS =====
    
    def upload_problems(self, problems_data: dict, session_name: str = "session1", level: int = 1) -> bool:
        """
        Upload problems to Firebase
        
        Args:
            problems_data: Dictionary or list of problem objects
            session_name: Session identifier (e.g., 'session1', 'session2')
            level: Level number (e.g., 1, 2, 3) to prevent overwriting between levels
        
        Returns:
            bool: True if successful
        """
        try:
            # If problems_data is a dict with session keys, upload accordingly
            if isinstance(problems_data, dict) and any(key.startswith('session') for key in problems_data.keys()):
                # Upload each session separately with level prefix
                for session_key, problems_list in problems_data.items():
                    if session_key.startswith('session'):
                        # Add level to document name to prevent overwriting
                        doc_name = f"level{level}_{session_key}"
                        doc_ref = self.problems_ref.document(doc_name)
                        doc_ref.set({
                            'problems': problems_list,
                            'updated_at': firestore.SERVER_TIMESTAMP,
                            'session': session_key,
                            'level': level
                        })
                        print(f"[INFO] Uploaded {len(problems_list)} problems to {doc_name}")
            
            # If problems_data is a list, upload to specified session
            elif isinstance(problems_data, list):
                # Add level to document name to prevent overwriting
                doc_name = f"level{level}_{session_name}"
                doc_ref = self.problems_ref.document(doc_name)
                doc_ref.set({
                    'problems': problems_data,
                    'updated_at': firestore.SERVER_TIMESTAMP,
                    'session': session_name,
                    'level': level
                })
                print(f"[INFO] Uploaded {len(problems_data)} problems to {doc_name}")
            
            else:
                print(f"[ERROR] Invalid problems_data format")
                return False
            
            # Update metadata
            metadata_ref = self.competition_ref.document('metadata')
            metadata_ref.update({
                'problems_uploaded': True,
                'last_problem_update': firestore.SERVER_TIMESTAMP
            })
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to upload problems: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_problems(self, week: Optional[int] = None, level: Optional[int] = None) -> dict:
        """
        Retrieve problems from Firebase, optionally filtered by week and level
        Handles both formats:
        1. Direct: {"session1": [...], "session2": [...]}
        2. Nested: {"sessions": {"session1": {...}, "session2": {...}}}
        
        Args:
            week: Week number (corresponds to session number)
            level: Level number to filter problems
        
        Returns:
            dict: Dictionary of problems with problem_id as key
        """
        try:
            problems = {}
            problem_counter = 1  # Auto-generate numeric IDs
            
            print(f"[DEBUG] get_problems called with week={week}, level={level}")
            
            # First, try to fetch a document called "all_problems" or "Level1_AllProblems"
            # This handles the case where all problems are in one document
            for doc_name in ['Level1_AllProblems', 'all_problems', 'problems']:
                doc_ref = self.problems_ref.document(doc_name)
                doc = doc_ref.get()
                
                if doc.exists:
                    print(f"[DEBUG] Found document: {doc_name}")
                    data = doc.to_dict()
                    print(f"[DEBUG] Document keys: {list(data.keys())}")
                    
                    # Check if this has the nested "sessions" structure
                    if 'sessions' in data:
                        print(f"[DEBUG] Processing nested 'sessions' structure")
                        sessions_data = data.get('sessions', {})
                        
                        # Filter by week if specified
                        if week:
                            session_name = f'session{week}'
                            if session_name in sessions_data:
                                session_data = sessions_data[session_name]
                                problems_list = session_data.get('problems', [])
                                print(f"[DEBUG] Found {len(problems_list)} problems in {session_name}")
                                
                                for problem in problems_list:
                                    if not isinstance(problem, dict):
                                        continue
                                    
                                    problem_id = problem.get('id')
                                    if not isinstance(problem_id, int):
                                        problem_id = problem_counter
                                        problem['id'] = problem_id
                                    
                                    problem_counter += 1
                                    
                                    if 'level' not in problem:
                                        problem['level'] = level if level else 1
                                    
                                    if level is None or str(problem.get('level', '')) == str(level):
                                        problems[problem_id] = problem
                        else:
                            # Get all sessions
                            for session_key, session_data in sessions_data.items():
                                problems_list = session_data.get('problems', [])
                                print(f"[DEBUG] Processing {session_key} with {len(problems_list)} problems")
                                
                                for problem in problems_list:
                                    if not isinstance(problem, dict):
                                        continue
                                    
                                    problem_id = problem.get('id')
                                    if not isinstance(problem_id, int):
                                        problem_id = problem_counter
                                        problem['id'] = problem_id
                                    
                                    problem_counter += 1
                                    
                                    if 'level' not in problem:
                                        problem['level'] = 1
                                    
                                    if level is None or str(problem.get('level', '')) == str(level):
                                        problems[problem_id] = problem
                        
                        print(f"[DEBUG] Returning {len(problems)} problems after filtering")
                        return problems
            
            print(f"[DEBUG] No all_problems document found, trying individual session documents")
            
            # Fallback: Try individual session documents
            # Determine session to fetch
            if week:
                session_name = f'session{week}'
                # Try level-specific document first, then fall back to non-level document
                doc_names_to_try = []
                if level:
                    doc_names_to_try.append(f'level{level}_{session_name}')
                doc_names_to_try.append(session_name)
                
                doc = None
                for doc_name in doc_names_to_try:
                    doc_ref = self.problems_ref.document(doc_name)
                    doc = doc_ref.get()
                    if doc.exists:
                        print(f"[DEBUG] Found session document: {doc_name}")
                        break
                
                if doc and doc.exists:
                    data = doc.to_dict()
                    problems_list = data.get('problems', [])
                    print(f"[DEBUG] Found {len(problems_list)} problems in {session_name}")
                    
                    # Convert list to dict and filter by level if specified
                    for problem in problems_list:
                        # Skip if not a dict (data structure issue)
                        if not isinstance(problem, dict):
                            print(f"[WARNING] Skipping invalid problem data (not a dict): {type(problem)}")
                            continue
                        
                        # Use existing ID or auto-generate
                        problem_id = problem.get('id')
                        if not isinstance(problem_id, int):
                            # If ID is string or missing, generate numeric ID
                            problem_id = problem_counter
                            problem['id'] = problem_id
                        
                        problem_counter += 1
                        
                        # Add level if missing
                        if 'level' not in problem:
                            problem['level'] = level if level else 1
                        
                        # Filter by level if specified
                        if level is None or str(problem.get('level', '')) == str(level):
                            problems[problem_id] = problem
                else:
                    print(f"[DEBUG] No document found for {session_name}")
            else:
                # Fetch all sessions
                docs = self.problems_ref.stream()
                
                for doc in docs:
                    data = doc.to_dict()
                    
                    # Check if this is the nested "sessions" format
                    if 'sessions' in data:
                        sessions_data = data.get('sessions', {})
                        # Iterate through all sessions
                        for session_key, session_data in sessions_data.items():
                            problems_list = session_data.get('problems', [])
                            
                            for problem in problems_list:
                                if not isinstance(problem, dict):
                                    continue
                                
                                problem_id = problem.get('id')
                                if not isinstance(problem_id, int):
                                    problem_id = problem_counter
                                    problem['id'] = problem_id
                                
                                problem_counter += 1
                                
                                if 'level' not in problem:
                                    problem['level'] = 1
                                
                                if level is None or str(problem.get('level', '')) == str(level):
                                    problems[problem_id] = problem
                    else:
                        # Direct format
                        problems_list = data.get('problems', [])
                        
                        for problem in problems_list:
                            if not isinstance(problem, dict):
                                continue
                            
                            problem_id = problem.get('id')
                            if not isinstance(problem_id, int):
                                problem_id = problem_counter
                                problem['id'] = problem_id
                            
                            problem_counter += 1
                            
                            if 'level' not in problem:
                                problem['level'] = 1
                            
                            if level is None or str(problem.get('level', '')) == str(level):
                                problems[problem_id] = problem
            
            return problems
        except Exception as e:
            print(f"[ERROR] Failed to retrieve problems: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_problem_by_id(self, problem_id: int, week: Optional[int] = None) -> Optional[dict]:
        """
        Retrieve a specific problem by ID
        
        Args:
            problem_id: The problem ID
            week: Optional week number to narrow search
        
        Returns:
            dict: Problem data or None if not found
        """
        try:
            problems = self.get_problems(week=week)
            return problems.get(problem_id, None)
        except Exception as e:
            print(f"[ERROR] Failed to retrieve problem {problem_id}: {e}")
            return None
    
    def update_problem(self, session_name: str, problem_id: int, updates: dict) -> bool:
        """
        Update a specific problem in Firebase
        
        Args:
            session_name: Session identifier (e.g., 'session1')
            problem_id: The problem ID to update
            updates: Dictionary of fields to update
        
        Returns:
            bool: True if successful
        """
        try:
            doc_ref = self.problems_ref.document(session_name)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                problems_list = data.get('problems', [])
                
                # Find and update the problem
                for i, problem in enumerate(problems_list):
                    if problem.get('id') == problem_id:
                        problems_list[i].update(updates)
                        
                        # Update in Firebase
                        doc_ref.update({
                            'problems': problems_list,
                            'updated_at': firestore.SERVER_TIMESTAMP
                        })
                        return True
                
                print(f"[WARNING] Problem {problem_id} not found in {session_name}")
                return False
            else:
                print(f"[ERROR] Session {session_name} not found")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to update problem: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_problem(self, session_name: str, problem_id: int) -> bool:
        """
        Delete a specific problem from Firebase
        
        Args:
            session_name: Session identifier (e.g., 'session1')
            problem_id: The problem ID to delete
        
        Returns:
            bool: True if successful
        """
        try:
            doc_ref = self.problems_ref.document(session_name)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                problems_list = data.get('problems', [])
                
                # Filter out the problem to delete
                updated_list = [p for p in problems_list if p.get('id') != problem_id]
                
                if len(updated_list) < len(problems_list):
                    doc_ref.update({
                        'problems': updated_list,
                        'updated_at': firestore.SERVER_TIMESTAMP
                    })
                    print(f"[INFO] Deleted problem {problem_id} from {session_name}")
                    return True
                else:
                    print(f"[WARNING] Problem {problem_id} not found in {session_name}")
                    return False
            else:
                print(f"[ERROR] Session {session_name} not found")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to delete problem: {e}")
            import traceback
            traceback.print_exc()
            return False
