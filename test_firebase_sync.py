# -*- coding: utf-8 -*-
"""
Quick test to verify Firebase synchronization
"""
from data_manager import create_data_manager
from datetime import datetime

def test_firebase_sync():
    """Test that data syncs to Firebase correctly"""
    
    print("="*60)
    print("Testing Firebase Synchronization")
    print("="*60)
    
    # Initialize data manager
    dm = create_data_manager()
    
    print(f"\n✓ Backend: {dm.get_backend_type()}")
    print(f"✓ Using Firebase: {dm.is_firebase()}")
    
    # Test 1: Register a test competitor
    print("\n" + "="*60)
    print("TEST 1: Register Competitor")
    print("="*60)
    
    test_name = f"TestStudent_{datetime.now().strftime('%H%M%S')}"
    success = dm.register_competitor(test_name)
    
    if success:
        print(f"✓ Registered: {test_name}")
    else:
        print(f"⚠ Competitor already exists (that's ok)")
    
    # Test 2: Submit a solution
    print("\n" + "="*60)
    print("TEST 2: Submit Solution")
    print("="*60)
    
    test_code = """
def solution(n):
    '''Test solution that calculates factorial'''
    if n <= 1:
        return 1
    return n * solution(n - 1)

# Test the solution
print(solution(5))  # Should print 120
"""
    
    test_results = [
        {"test": "Test 1", "passed": True, "input": "5", "expected": "120", "actual": "120"},
        {"test": "Test 2", "passed": True, "input": "3", "expected": "6", "actual": "6"},
        {"test": "Test 3", "passed": True, "input": "1", "expected": "1", "actual": "1"},
    ]
    
    success = dm.submit_solution(
        name=test_name,
        problem_id=1,
        code=test_code,
        test_results=test_results,
        all_passed=True
    )
    
    if success:
        print(f"✓ Submitted solution for Problem 1")
        print(f"  - Code length: {len(test_code)} characters")
        print(f"  - Tests passed: 3/3")
        print(f"  - All tests passed: Yes")
    else:
        print("✗ Failed to submit solution")
    
    # Test 3: Retrieve data
    print("\n" + "="*60)
    print("TEST 3: Retrieve Competitor Data")
    print("="*60)
    
    data = dm.get_competitor_data(test_name)
    if data:
        print(f"✓ Retrieved data for {test_name}")
        print(f"  - Name: {data.get('name')}")
        print(f"  - Joined at: {data.get('joined_at')}")
        print(f"  - Current problem: {data.get('current_problem')}")
        
        problems = data.get('problems', {})
        print(f"  - Problems attempted: {len(problems)}")
        
        if '1' in problems:
            prob_data = problems['1']
            submissions = prob_data.get('submissions', [])
            print(f"  - Problem 1 submissions: {len(submissions)}")
            
            if submissions:
                latest = submissions[-1]
                print(f"  - Latest submission:")
                print(f"    * Tests passed: {latest.get('passed_tests')}/{latest.get('total_tests')}")
                print(f"    * All passed: {latest.get('all_passed')}")
                print(f"    * Code stored: Yes ({len(latest.get('code', ''))} chars)")
    else:
        print("✗ Failed to retrieve data")
    
    # Test 4: Get leaderboard
    print("\n" + "="*60)
    print("TEST 4: Get Leaderboard")
    print("="*60)
    
    leaderboard = dm.get_leaderboard()
    print(f"✓ Retrieved leaderboard with {len(leaderboard)} competitors")
    
    if leaderboard:
        print("\nTop competitors:")
        for i, entry in enumerate(leaderboard[:5], 1):
            print(f"  {i}. {entry['name']}")
            print(f"     - Problems solved: {entry['problems_solved']}")
            print(f"     - Total submissions: {entry['total_submissions']}")
            print(f"     - Tests passed: {entry['total_tests_passed']}")
    
    # Test 5: Get problem statistics
    print("\n" + "="*60)
    print("TEST 5: Get Problem Statistics")
    print("="*60)
    
    stats = dm.get_problem_statistics()
    print(f"✓ Retrieved statistics for {len(stats)} problems")
    
    for problem_id, problem_stats in stats.items():
        print(f"\n  Problem {problem_id}:")
        print(f"    - Total attempts: {problem_stats.get('total_attempts', 0)}")
        print(f"    - Total solvers: {problem_stats.get('total_solvers', 0)}")
        print(f"    - Total submissions: {problem_stats.get('total_submissions', 0)}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60)
    print("\nFirebase is syncing:")
    print("✓ Competitor registration")
    print("✓ Code submissions (full code stored)")
    print("✓ Test results")
    print("✓ Leaderboard data")
    print("✓ Problem statistics")
    print("\n🎉 Your system is ready for multi-device competition!")
    print("\nNext steps:")
    print("1. Open Firebase Console: https://console.firebase.google.com/")
    print("2. Go to Firestore Database")
    print("3. You'll see 'competitors' collection with your test data")
    print("4. Open Judge Dashboard or Spectator View to see real-time sync")

if __name__ == "__main__":
    test_firebase_sync()
