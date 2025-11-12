# -*- coding: utf-8 -*-
"""
Test code viewing in Judge Dashboard
"""
from data_manager import create_data_manager
from datetime import datetime

def test_code_view():
    """Test that submitted code is visible in judge dashboard"""
    
    print("="*60)
    print("Testing Code Submission and Viewing")
    print("="*60)
    
    dm = create_data_manager()
    
    # Create a test student
    student_name = f"CodeTestStudent_{datetime.now().strftime('%H%M%S')}"
    print(f"\n1. Registering student: {student_name}")
    dm.register_competitor(student_name)
    
    # Submit code for problem 1
    test_code = """# Factorial Calculator
def factorial(n):
    '''Calculate factorial of n'''
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Test cases
print(factorial(5))  # Should output 120
print(factorial(0))  # Should output 1
print(factorial(3))  # Should output 6
"""
    
    test_results = [
        {"test": "Test 1", "passed": True, "input": "5", "expected": "120", "actual": "120"},
        {"test": "Test 2", "passed": True, "input": "0", "expected": "1", "actual": "1"},
        {"test": "Test 3", "passed": True, "input": "3", "expected": "6", "actual": "6"},
    ]
    
    print(f"\n2. Submitting code for Problem 1")
    print(f"   Code length: {len(test_code)} characters")
    
    success = dm.submit_solution(
        name=student_name,
        problem_id=1,
        code=test_code,
        test_results=test_results,
        all_passed=True
    )
    
    if success:
        print("   ✓ Code submitted successfully")
    else:
        print("   ✗ Failed to submit code")
        return
    
    # Retrieve the data to verify code is stored
    print(f"\n3. Retrieving data from Firebase...")
    data = dm.get_competitor_data(student_name)
    
    if not data:
        print("   ✗ Failed to retrieve data")
        return
    
    print(f"   ✓ Data retrieved")
    
    # Check if code is in the data
    problems = data.get('problems', {})
    print(f"\n4. Checking stored data:")
    print(f"   - Problems in database: {list(problems.keys())}")
    
    # Check problem 1
    if '1' in problems:
        prob_data = problems['1']
        print(f"   - Problem '1' data exists: Yes")
        
        best_result = prob_data.get('best_result', {})
        print(f"   - Best result exists: {bool(best_result)}")
        
        if best_result:
            stored_code = best_result.get('code', '')
            print(f"   - Code in best_result: {'Yes' if stored_code else 'No'}")
            if stored_code:
                print(f"   - Stored code length: {len(stored_code)} characters")
                print(f"\n   First 100 characters of stored code:")
                print(f"   {stored_code[:100]}...")
            
        submissions = prob_data.get('submissions', [])
        print(f"   - Number of submissions: {len(submissions)}")
        
        if submissions:
            latest = submissions[-1]
            sub_code = latest.get('code', '')
            print(f"   - Code in latest submission: {'Yes' if sub_code else 'No'}")
            if sub_code:
                print(f"   - Submission code length: {len(sub_code)} characters")
    elif 1 in problems:
        print(f"   - Problem 1 (as integer) data exists: Yes")
        prob_data = problems[1]
        best_result = prob_data.get('best_result', {})
        stored_code = best_result.get('code', '')
        print(f"   - Code stored: {'Yes' if stored_code else 'No'}")
    else:
        print(f"   - Problem 1 data: NOT FOUND")
    
    print(f"\n{'='*60}")
    print("✅ Test Complete!")
    print(f"{'='*60}")
    print(f"\nTo view the code in Judge Dashboard:")
    print(f"1. Run: python launcher.py")
    print(f"2. Click 'Open Judge Dashboard'")
    print(f"3. Select competitor: {student_name}")
    print(f"4. Go to 'Problem Status' tab")
    print(f"5. Click on 'Problem 1'")
    print(f"6. Go to 'Code View' tab")
    print(f"\nThe code should be displayed there!")

if __name__ == "__main__":
    test_code_view()
