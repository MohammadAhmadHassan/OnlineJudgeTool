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
            # Cache configuration
            self._cache = {}
            self._cache_timestamps = {}
            self._cache_ttl = {
                'all_competitors': 30,  # guarded by metadata version checks
                'leaderboard': 30,      # guarded by metadata version checks
                'problems': 3600,      # 1 hour cache (problems never change)
                'competitor': 2,       # 2 seconds cache for individual competitor
                'statistics': 5,       # 5 seconds cache for stats
                'data_version': 1      # metadata version polling cache
            }
            self._initialize_firebase()
    
    def _get_from_cache(self, cache_key: str, ttl_key: str = None):
        """Get data from cache if not expired"""
        if cache_key not in self._cache:
            return None
        
        # Check if expired
        if cache_key in self._cache_timestamps:
            age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
            ttl = self._cache_ttl.get(ttl_key or cache_key, 5)
            if age > ttl:
                # Expired, remove from cache
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
                return None
        
        return self._cache[cache_key]
    
    def _set_cache(self, cache_key: str, data):
        """Store data in cache with timestamp"""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
    
    def _invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries matching pattern or all if None"""
        if pattern is None:
            self._cache.clear()
            self._cache_timestamps.clear()
        else:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring"""
        stats = {
            'total_entries': len(self._cache),
            'entries': {}
        }
        
        for key, timestamp in self._cache_timestamps.items():
            age = (datetime.now() - timestamp).total_seconds()
            ttl_key = key.split('_')[0] if '_' in key else key
            ttl = self._cache_ttl.get(ttl_key, 5)
            
            stats['entries'][key] = {
                'age_seconds': round(age, 2),
                'ttl_seconds': ttl,
                'expired': age > ttl,
                'remaining_seconds': max(0, round(ttl - age, 2))
            }
        
        return stats
    
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
                    'problems_loaded': [],
                    'data_version': 0,
                    'last_data_change': None
                })
        except Exception as e:
            print(f"Error initializing competition metadata: {e}")

    def _touch_data_version(self):
        """Increment global data version to signal fresh competition data."""
        try:
            doc_ref = self.competition_ref.document('metadata')
            doc_ref.set({
                'data_version': firestore.Increment(1),
                'last_data_change': firestore.SERVER_TIMESTAMP
            }, merge=True)
            self._invalidate_cache('data_version')
        except Exception as e:
            print(f"Error updating data version: {e}")

    def _get_data_version(self) -> int:
        """Read global data version (cheap single-doc read, cached briefly)."""
        try:
            cache_key = 'data_version'
            cached_version = self._get_from_cache(cache_key, 'data_version')
            if cached_version is not None:
                return int(cached_version)

            doc_ref = self.competition_ref.document('metadata')
            doc = doc_ref.get()
            version = 0
            if doc.exists:
                version = int((doc.to_dict() or {}).get('data_version', 0))

            self._set_cache(cache_key, version)
            return version
        except Exception as e:
            print(f"Error reading data version: {e}")
            return 0

    def get_data_version(self) -> int:
        """Public accessor for current data version token."""
        return self._get_data_version()
    
    def start_competition(self):
        """Mark competition as started"""
        try:
            doc_ref = self.competition_ref.document('metadata')
            doc_ref.update({
                'competition_started': True,
                'start_time': datetime.now().isoformat()
            })
            self._touch_data_version()
            # Invalidate all cache
            self._invalidate_cache()
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
                'notifications': [],
                'last_activity': datetime.now().isoformat(),
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add week and level if provided
            if week is not None:
                competitor_data['week'] = week
            if level is not None:
                competitor_data['level'] = level
            
            doc_ref.set(competitor_data)
            self._touch_data_version()
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
            self._touch_data_version()
            # Invalidate specific competitor cache
            self._invalidate_cache(f'competitor_{name}')
        except Exception as e:
            print(f"Error updating competitor problem: {e}")
    
    def submit_solution(self, name: str, problem_id: int, code: str, 
                       test_results: List[dict], all_passed: bool, problem_name: str = None):
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
                    'problem_name': problem_name or f'Problem {problem_id}',
                    'judge_approval': 'pending',  # Initialize approval status
                    'judge_approval_time': None,
                    'review_status': None,
                    'review_requested_at': None,
                    'review_locked_by': None,
                    'review_locked_at': None,
                    'review_completed_at': None,
                    'review_completed_by': None,
                    'review_last_opened_at': None
                }
            
            # Add submission
            if problem_name:
                problems[problem_key]['problem_name'] = problem_name
            problems[problem_key]['submissions'].append(submission)
            
            # Update best result if this is better
            current_best = problems[problem_key]['best_result']
            if current_best is None or submission['passed_tests'] > current_best.get('passed_tests', 0):
                problems[problem_key]['best_result'] = submission

            # Any new submission should enter the shared review queue.
            problems[problem_key]['judge_approval'] = 'pending'
            problems[problem_key]['judge_approval_time'] = None
            problems[problem_key]['review_status'] = 'pending_review'
            problems[problem_key]['review_requested_at'] = submission['submitted_at']
            problems[problem_key]['review_locked_by'] = None
            problems[problem_key]['review_locked_at'] = None
            problems[problem_key]['review_completed_at'] = None
            problems[problem_key]['review_completed_by'] = None
            
            # Update document
            doc_ref.update({
                'problems': problems,
                'last_activity': datetime.now().isoformat()
            })
            
            # Invalidate relevant caches
            self._invalidate_cache(f'competitor_{name}')
            self._invalidate_cache('all_competitors')
            self._invalidate_cache('leaderboard')
            self._touch_data_version()
            
            return True
        except Exception as e:
            print(f"Error submitting solution: {e}")
            return False

    def _normalize_review_status(self, problem_data: dict) -> str:
        """Normalize review status across old and new schemas."""
        explicit_status = problem_data.get('review_status')
        if explicit_status in ['pending_review', 'under_review', 'reviewed']:
            return explicit_status

        judge_approval = problem_data.get('judge_approval')
        if judge_approval in ['approved', 'rejected']:
            return 'reviewed'

        if problem_data.get('submissions', []):
            return 'pending_review'

        return 'not_ready'

    def get_review_queue(self) -> List[dict]:
        """Return all submitted problems as review queue entries."""
        try:
            competitors = self.get_all_competitors()
            queue = []

            for competitor_name, competitor_data in competitors.items():
                for problem_id, problem_data in competitor_data.get('problems', {}).items():
                    submissions = problem_data.get('submissions', [])
                    if not submissions:
                        continue

                    latest_submission = submissions[-1] if submissions else {}
                    queue.append({
                        'competitor': competitor_name,
                        'problem_id': int(problem_id) if str(problem_id).isdigit() else problem_id,
                        'review_status': self._normalize_review_status(problem_data),
                        'judge_approval': problem_data.get('judge_approval', 'pending'),
                        'locked_by': problem_data.get('review_locked_by'),
                        'locked_at': problem_data.get('review_locked_at'),
                        'reviewed_at': problem_data.get('review_completed_at') or problem_data.get('judge_approval_time'),
                        'submitted_at': latest_submission.get('submitted_at', latest_submission.get('timestamp')),
                        'attempts': len(submissions),
                        'passed_tests': latest_submission.get('passed_tests', latest_submission.get('tests_passed', 0)),
                        'total_tests': latest_submission.get('total_tests', 0),
                        'all_passed': latest_submission.get('all_passed', False),
                        'level': competitor_data.get('level'),
                        'week': competitor_data.get('week')
                    })

            status_order = {
                'pending_review': 0,
                'under_review': 1,
                'reviewed': 2
            }

            def sort_timestamp(entry):
                timestamp = entry.get('submitted_at')
                if not timestamp:
                    return 0.0
                try:
                    parsed = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                    return parsed.timestamp()
                except Exception:
                    return 0.0

            queue.sort(key=sort_timestamp, reverse=True)
            queue.sort(key=lambda entry: status_order.get(entry.get('review_status'), 99))
            return queue
        except Exception as e:
            print(f"Error getting review queue: {e}")
            return []

    def start_problem_review(self, name: str, problem_id: int, judge_id: str) -> dict:
        """Lock a submitted problem for review so only one judge can access it."""
        try:
            problem_id_str = str(problem_id)
            doc_ref = self.competitors_ref.document(name)
            transaction = self.db.transaction()

            @firestore.transactional
            def _lock_for_review(transaction, competitor_ref):
                snapshot = competitor_ref.get(transaction=transaction)
                if not snapshot.exists:
                    return {
                        'success': False,
                        'message': f'Competitor {name} not found'
                    }

                competitor_data = snapshot.to_dict()
                problems = competitor_data.get('problems', {})
                if problem_id_str not in problems:
                    return {
                        'success': False,
                        'message': f'Problem {problem_id} not found for {name}'
                    }

                problem_data = problems.get(problem_id_str, {})
                submissions = problem_data.get('submissions', [])
                if not submissions:
                    return {
                        'success': False,
                        'message': 'Only submitted problems can be reviewed'
                    }

                review_status = self._normalize_review_status(problem_data)
                lock_owner = problem_data.get('review_locked_by')

                if review_status == 'under_review':
                    if lock_owner == judge_id:
                        return {
                            'success': True,
                            'message': 'Already assigned to you'
                        }
                    owner_label = lock_owner or 'another judge'
                    return {
                        'success': False,
                        'message': f'This entry is currently under review by {owner_label}'
                    }

                if review_status == 'reviewed':
                    return {
                        'success': False,
                        'message': 'This entry has already been reviewed'
                    }

                now = datetime.now().isoformat()
                transaction.update(competitor_ref, {
                    f'problems.{problem_id_str}.review_status': 'under_review',
                    f'problems.{problem_id_str}.review_locked_by': judge_id,
                    f'problems.{problem_id_str}.review_locked_at': now,
                    f'problems.{problem_id_str}.review_last_opened_at': now
                })

                return {
                    'success': True,
                    'message': 'Submission moved to under review'
                }

            result = _lock_for_review(transaction, doc_ref)

            if result.get('success'):
                self._invalidate_cache(f'competitor_{name}')
                self._invalidate_cache('all_competitors')
                self._invalidate_cache('leaderboard')
                self._touch_data_version()

            return result
        except Exception as e:
            print(f"Error starting problem review: {e}")
            return {
                'success': False,
                'message': 'Failed to lock submission for review'
            }
    
    def get_competitor_data(self, name: str) -> Optional[dict]:
        """Get data for a specific competitor with caching"""
        try:
            # Check cache first
            cache_key = f'competitor_{name}'
            cached_data = self._get_from_cache(cache_key, 'competitor')
            if cached_data is not None:
                return cached_data
            
            # Fetch from database
            doc_ref = self.competitors_ref.document(name)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Cache the result
                self._set_cache(cache_key, data)
                return data
            return None
        except Exception as e:
            print(f"Error getting competitor data: {e}")
            return None
    
    def get_all_competitors(self) -> Dict[str, dict]:
        """Get data for all competitors with caching"""
        try:
            # Use metadata version to avoid expensive full collection scan when unchanged.
            cache_key = 'all_competitors'
            version_key = 'all_competitors_version'
            current_version = self._get_data_version()
            cached_data = self._get_from_cache(cache_key, 'all_competitors')
            cached_version = self._get_from_cache(version_key, 'all_competitors')

            if cached_data is not None and cached_version is not None and int(cached_version) == int(current_version):
                return cached_data
            
            # Fetch from database
            competitors = {}
            docs = self.competitors_ref.stream()
            
            for doc in docs:
                competitors[doc.id] = doc.to_dict()
            
            # Cache the result
            self._set_cache(cache_key, competitors)
            self._set_cache(version_key, current_version)
            
            return competitors
        except Exception as e:
            print(f"Error getting all competitors: {e}")
            return {}
    
    def get_leaderboard(self) -> List[dict]:
        """Generate leaderboard data with caching"""
        try:
            # Use metadata version to avoid rebuilding leaderboard when unchanged.
            cache_key = 'leaderboard'
            version_key = 'leaderboard_version'
            current_version = self._get_data_version()
            cached_data = self._get_from_cache(cache_key, 'leaderboard')
            cached_version = self._get_from_cache(version_key, 'leaderboard')

            if cached_data is not None and cached_version is not None and int(cached_version) == int(current_version):
                return cached_data
            
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
            
            # Cache the leaderboard
            self._set_cache('leaderboard', leaderboard)
            self._set_cache(version_key, current_version)
            
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
                'problems_loaded': [],
                'data_version': 0,
                'last_data_change': firestore.SERVER_TIMESTAMP
            })
            
            print("Competition data reset successfully")
            # Clear all cache
            self._invalidate_cache()
        except Exception as e:
            print(f"Error resetting competition: {e}")
    
    def set_judge_approval(self, name: str, problem_id: int, status: str, judge_id: str = None, problem_name: str = None):
        """Finalize judge decision and mark review lifecycle as reviewed."""
        try:
            problem_id_str = str(problem_id)
            doc_ref = self.competitors_ref.document(name)
            transaction = self.db.transaction()

            @firestore.transactional
            def _finalize_review(transaction, competitor_ref):
                snapshot = competitor_ref.get(transaction=transaction)
                if not snapshot.exists:
                    return {
                        'success': False,
                        'message': f'Competitor {name} not found'
                    }

                competitor_data = snapshot.to_dict()
                problems = competitor_data.get('problems', {})
                if problem_id_str not in problems:
                    return {
                        'success': False,
                        'message': f'Problem {problem_id} not found for {name}'
                    }

                problem_data = problems.get(problem_id_str, {})
                submissions = problem_data.get('submissions', [])
                if not submissions:
                    return {
                        'success': False,
                        'message': 'Only submitted problems can be reviewed'
                    }

                review_status = self._normalize_review_status(problem_data)
                lock_owner = problem_data.get('review_locked_by')
                if review_status == 'under_review' and lock_owner and judge_id and lock_owner != judge_id:
                    return {
                        'success': False,
                        'message': f'This entry is locked by {lock_owner}'
                    }

                now = datetime.now().isoformat()
                update_dict = {
                    f'problems.{problem_id_str}.judge_approval': status,
                    f'problems.{problem_id_str}.judge_approval_time': now,
                    f'problems.{problem_id_str}.review_status': 'reviewed',
                    f'problems.{problem_id_str}.review_completed_at': now,
                    f'problems.{problem_id_str}.review_locked_by': None,
                    f'problems.{problem_id_str}.review_locked_at': None
                }

                if judge_id:
                    update_dict[f'problems.{problem_id_str}.review_completed_by'] = judge_id
                elif lock_owner:
                    update_dict[f'problems.{problem_id_str}.review_completed_by'] = lock_owner

                if status == 'rejected':
                    resolved_problem_name = problem_name or problem_data.get('problem_name') or f'Problem {problem_id_str}'
                    notifications = list(competitor_data.get('notifications', []))
                    notifications.append({
                        'problem_id': int(problem_id_str) if problem_id_str.isdigit() else problem_id_str,
                        'problem_name': resolved_problem_name,
                        'created_at': now,
                        'status': 'rejected'
                    })
                    update_dict[f'problems.{problem_id_str}.problem_name'] = resolved_problem_name
                    update_dict['notifications'] = notifications[-50:]

                transaction.update(competitor_ref, update_dict)
                return {
                    'success': True,
                    'message': f'Review finalized with status {status}'
                }

            result = _finalize_review(transaction, doc_ref)
            if result.get('success'):
                self._invalidate_cache(f'competitor_{name}')
                self._invalidate_cache('all_competitors')
                self._invalidate_cache('leaderboard')
                self._touch_data_version()
                return True

            print(f"[WARNING] Failed to set judge approval: {result.get('message')}")
            return False
        except Exception as e:
            print(f"[ERROR] Exception in set_judge_approval: {e}")
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
            # If problems_data is a dict, upload each list-valued key as a collection.
            # This supports both session keys (session1/session19/...) and named
            # collections like FinalCompetion / FinalCompetition.
            if isinstance(problems_data, dict):
                uploaded_any = False
                for collection_key, problems_list in problems_data.items():
                    if not isinstance(problems_list, list):
                        continue

                    # Add level to document name to prevent overwriting
                    doc_name = f"level{level}_{collection_key}"
                    doc_ref = self.problems_ref.document(doc_name)
                    doc_ref.set({
                        'problems': problems_list,
                        'updated_at': firestore.SERVER_TIMESTAMP,
                        'session': collection_key,
                        'level': level
                    })
                    uploaded_any = True
                    print(f"[INFO] Uploaded {len(problems_list)} problems to {doc_name}")

                if not uploaded_any:
                    print(f"[ERROR] Invalid problems_data format")
                    return False
            
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
            
            # Invalidate problems cache
            self._invalidate_cache('problems')
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to upload problems: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_problems(self, week: Optional[int] = None, level: Optional[int] = None) -> dict:
        """
        Retrieve problems from Firebase, optionally filtered by week and level with caching
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
            # Check cache first
            cache_key = f'problems_w{week}_l{level}'
            cached_data = self._get_from_cache(cache_key, 'problems')
            if cached_data is not None:
                return cached_data
            
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
                        # Cache the result
                        cache_key = f'problems_w{week}_l{level}'
                        self._set_cache(cache_key, problems)
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
                    
                    # Convert list to dict and filter by level if specified
                    for problem in problems_list:
                        problem_id = problem.get('id')
                        if problem_id:
                            # Filter by level if specified
                            if level is None or str(problem.get('level', '')) == str(level):
                                problems[problem_id] = problem
            else:
                # Fetch all sessions
                docs = self.problems_ref.stream()
                
                for doc in docs:
                    data = doc.to_dict()
                    problems_list = data.get('problems', [])
                    
                    for problem in problems_list:
                        problem_id = problem.get('id')
                        if problem_id:
                            # Filter by level if specified
                            if level is None or str(problem.get('level', '')) == str(level):
                                problems[problem_id] = problem
            
            # Cache the result before returning
            cache_key = f'problems_w{week}_l{level}'
            self._set_cache(cache_key, problems)
            
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
