"""
Competitor Interface - Streamlit Version
Solve programming problems and submit solutions
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
import os
import io
import contextlib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import create_data_manager

# Check if running in single-dashboard mode and hide sidebar navigation
DASHBOARD_MODE = os.environ.get('DASHBOARD_MODE', None)
if DASHBOARD_MODE is None:
    try:
        DASHBOARD_MODE = st.secrets.get('DASHBOARD_MODE', 'all')
    except:
        DASHBOARD_MODE = 'all'

# Hide sidebar navigation if in competitor-only mode
if DASHBOARD_MODE and DASHBOARD_MODE.lower() == 'competitor':
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="Competitor Interface",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .problem-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .problem-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    .problem-solved {
        border-color: #27ae60;
        background: #d4edda;
    }
    .problem-failed {
        border-color: #e74c3c;
        background: #f8d7da;
    }
    .test-result {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        border-left: 4px solid;
    }
    .test-passed {
        background: #d4edda;
        border-color: #27ae60;
    }
    .test-failed {
        background: #f8d7da;
        border-color: #e74c3c;
    }
    .code-output {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
    }
    .stat-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-warning { background: #fff3cd; color: #856404; }
    .badge-info { background: #d1ecf1; color: #0c5460; }
    .badge-danger { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()

# Initialize session state
if 'competitor_name' not in st.session_state:
    st.session_state.competitor_name = None
if 'current_problem' not in st.session_state:
    st.session_state.current_problem = None
if 'code' not in st.session_state:
    st.session_state.code = ""
if 'test_results' not in st.session_state:
    st.session_state.test_results = None

# Function to load problems
@st.cache_data
def load_problems():
    """Load all problems from JSON files"""
    problems = {}
    problems_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'problems')
    
    if os.path.exists(problems_dir):
        for filename in os.listdir(problems_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(problems_dir, filename), 'r') as f:
                        problem = json.load(f)
                        
                        # Extract problem ID from filename if not in JSON
                        problem_id = problem.get('id')
                        if not problem_id:
                            # Extract number from filename (e.g., problem1.json -> 1)
                            import re
                            match = re.search(r'(\d+)', filename)
                            if match:
                                problem_id = int(match.group(1))
                        
                        if problem_id:
                            # Add default starter code if not present
                            if 'starter_code' not in problem:
                                problem['starter_code'] = f'''def solution(input_value):
    """
    {problem.get('description', 'Solve the problem')}
    
    Args:
        input_value: The input for the problem
        
    Returns:
        The expected output
    """
    # Write your code here
    pass
'''
                            problems[problem_id] = problem
                except Exception as e:
                    st.error(f"Error loading {filename}: {e}")
    
    return problems

# Function to run code with test cases
def run_code_with_tests(code, test_cases):
    """Execute code and run test cases"""
    results = []
    
    for i, test in enumerate(test_cases):
        try:
            # Capture stdout
            stdout_capture = io.StringIO()
            
            # Create execution context
            exec_globals = {}
            
            # Mock input() function for entry-level programmers
            # Split test input into lines for multiple input() calls
            input_lines = str(test['input']).strip().split('\n')
            input_index = [0]  # Use list to allow modification in nested function
            
            def mock_input(prompt=''):
                """Mock input function that returns test case inputs"""
                if input_index[0] < len(input_lines):
                    value = input_lines[input_index[0]]
                    input_index[0] += 1
                    return value
                return ''  # Return empty string if no more inputs
            
            # Add mock input to execution environment
            exec_globals['input'] = mock_input
            
            # Execute the code
            with contextlib.redirect_stdout(stdout_capture):
                exec(code, exec_globals)
            
            # Get printed output
            printed_output = stdout_capture.getvalue().strip()
            
            # Check if solution function exists
            if 'solution' in exec_globals:
                # Function-based solution
                solution_func = exec_globals['solution']
                
                # Parse input - keep as string for most problems
                input_val = test['input']
                
                # Run the function
                if isinstance(input_val, list):
                    # Multiple arguments
                    output = solution_func(*input_val)
                else:
                    # Single argument
                    output = solution_func(input_val)
                
                # Convert to string for comparison
                output = str(output).strip()
                
            elif printed_output:
                # Code uses print() instead of return (common for beginners)
                output = printed_output
            else:
                results.append({
                    'test_num': i + 1,
                    'passed': False,
                    'input': test['input'],
                    'expected': test['output'],
                    'output': 'Error: No output produced (no solution function or print statements)',
                    'error': 'No output'
                })
                continue
            
            # Get expected output
            expected = str(test['output']).strip()
            
            # Compare output (handle both exact match and string comparison)
            passed = (output == expected) or (str(output).strip() == str(expected).strip())
            
            results.append({
                'test_num': i + 1,
                'passed': passed,
                'input': str(test['input']),
                'expected': expected,
                'output': output,
                'error': None
            })
            
        except Exception as e:
            results.append({
                'test_num': i + 1,
                'passed': False,
                'input': str(test.get('input', '')),
                'expected': str(test.get('output', '')),
                'output': f"Error: {str(e)}",
                'error': str(e)
            })
    
    return results

# Header
st.markdown("# 👨‍💻 Competitor Interface")

# Registration/Login Section
if st.session_state.competitor_name is None:
    st.markdown("## 📝 Registration")
    st.markdown("Enter your name to start competing!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        name_input = st.text_input("Your Name", placeholder="Enter your full name")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Start Competition", type="primary", use_container_width=True):
            if name_input and name_input.strip():
                # Register competitor
                data_manager.register_competitor(name_input.strip())
                st.session_state.competitor_name = name_input.strip()
                st.success(f"Welcome, {name_input}! 🎉")
                st.rerun()
            else:
                st.error("Please enter your name")
    
    st.markdown("---")
    st.info("💡 **Tip:** Make sure to enter your full name for the leaderboard!")

else:
    # Competitor is logged in
    competitor_name = st.session_state.competitor_name
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {competitor_name}")
        
        # Get competitor stats
        comp_data = data_manager.get_competitor_data(competitor_name) or {}
        problems_data = comp_data.get('problems', {})
        
        solved_count = sum(
            1 for p in problems_data.values() 
            if p.get('best_result', {}).get('all_passed', False)
        )
        total_submissions = sum(
            len(p.get('submissions', [])) for p in problems_data.values()
        )
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; text-align: center;">
            <div style="font-size: 2rem; font-weight: bold;">{solved_count}</div>
            <div>Problems Solved</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Total Submissions:** {total_submissions}")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.competitor_name = None
            st.session_state.current_problem = None
            st.session_state.code = ""
            st.rerun()
    
    # Main content
    problems = load_problems()
    
    if st.session_state.current_problem is None:
        # Problem selection view
        st.markdown("## 📚 Available Problems")
        st.markdown("Select a problem to start solving!")
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            filter_option = st.radio(
                "Filter:",
                ["All Problems", "Not Attempted", "In Progress", "Solved"],
                horizontal=True
            )
        
    # Display problems
        for problem_id, problem in sorted(problems.items()):
            # Reload fresh data for each problem to get latest submissions
            fresh_comp_data = data_manager.get_competitor_data(competitor_name) or {}
            fresh_problems_data = fresh_comp_data.get('problems', {})
            
            # Convert problem_id to string for Firebase lookup
            problem_id_str = str(problem_id)
            problem_data = fresh_problems_data.get(problem_id_str, {})
            best_result = problem_data.get('best_result', {})
            submissions = problem_data.get('submissions', [])
            
            # Apply filter
            if filter_option == "Not Attempted" and submissions:
                continue
            if filter_option == "In Progress" and (not submissions or best_result.get('all_passed')):
                continue
            if filter_option == "Solved" and not best_result.get('all_passed'):
                continue
            
            # Determine card style
            card_class = "problem-card"
            if best_result.get('all_passed'):
                card_class += " problem-solved"
                status_badge = '<span class="stat-badge badge-success">✓ Solved</span>'
            elif submissions:
                card_class += " problem-failed"
                status_badge = '<span class="stat-badge badge-warning">⚠ In Progress</span>'
            else:
                status_badge = '<span class="stat-badge badge-info">○ Not Attempted</span>'
            
            with st.container():
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### Problem {problem_id}: {problem['title']}")
                    st.markdown(status_badge, unsafe_allow_html=True)
                    if submissions:
                        st.markdown(
                            f'<span class="stat-badge badge-info">Attempts: {len(submissions)}</span>',
                            unsafe_allow_html=True
                        )
                    st.markdown(f"**Difficulty:** {problem.get('difficulty', 'Medium')}")
                    st.markdown(f"**Description:** {problem.get('description', 'No description')}")
                
                with col2:
                    if st.button("Solve", key=f"solve_{problem_id}", type="primary", use_container_width=True):
                        st.session_state.current_problem = problem_id
                        # Load last submitted code if exists
                        if submissions:
                            st.session_state.code = submissions[-1].get('code', '')
                        else:
                            st.session_state.code = problem.get('starter_code', '')
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Problem solving view
        problem_id = st.session_state.current_problem
        problem = problems.get(problem_id, {})
        
        # Get all problem IDs sorted
        all_problem_ids = sorted(problems.keys())
        current_index = all_problem_ids.index(problem_id) if problem_id in all_problem_ids else 0
        
        # Navigation buttons
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
        
        with nav_col1:
            if st.button("← Back to Problems", use_container_width=True):
                st.session_state.current_problem = None
                st.session_state.test_results = None
                st.rerun()
        
        with nav_col2:
            # Previous button
            if current_index > 0:
                prev_problem_id = all_problem_ids[current_index - 1]
                if st.button(f"← Previous (Problem {prev_problem_id})", use_container_width=True):
                    st.session_state.current_problem = prev_problem_id
                    # Load code for previous problem
                    prev_problem_data = problems_data.get(prev_problem_id, {})
                    prev_submissions = prev_problem_data.get('submissions', [])
                    if prev_submissions:
                        st.session_state.code = prev_submissions[-1].get('code', '')
                    else:
                        st.session_state.code = problems[prev_problem_id].get('starter_code', '')
                    st.session_state.test_results = None
                    st.rerun()
        
        with nav_col4:
            # Next button
            if current_index < len(all_problem_ids) - 1:
                next_problem_id = all_problem_ids[current_index + 1]
                if st.button(f"Next (Problem {next_problem_id}) →", use_container_width=True):
                    st.session_state.current_problem = next_problem_id
                    # Load code for next problem
                    next_problem_data = problems_data.get(next_problem_id, {})
                    next_submissions = next_problem_data.get('submissions', [])
                    if next_submissions:
                        st.session_state.code = next_submissions[-1].get('code', '')
                    else:
                        st.session_state.code = problems[next_problem_id].get('starter_code', '')
                    st.session_state.test_results = None
                    st.rerun()
        
        st.markdown(f"## Problem {problem_id}: {problem.get('title', 'Unknown')}")
        
        # Problem description
        with st.expander("📖 Problem Description", expanded=True):
            st.markdown(f"**Difficulty:** {problem.get('difficulty', 'Medium')}")
            st.markdown(problem.get('description', 'No description available'))
            
            # Show input/output format if available
            if 'input_format' in problem:
                st.markdown(f"**Input Format:** {problem['input_format']}")
            if 'output_format' in problem:
                st.markdown(f"**Output Format:** {problem['output_format']}")
            
            # Show examples
            if 'examples' in problem:
                st.markdown("**Examples:**")
                for i, example in enumerate(problem['examples'], 1):
                    st.code(f"Input: {example.get('input', '')}\nOutput: {example.get('output', '')}")
        
        # Show test cases BEFORE running
        with st.expander("🧪 Test Cases", expanded=True):
            st.markdown("**Your solution will be tested against these cases:**")
            test_cases = problem.get('test_cases', [])
            
            if test_cases:
                for i, test in enumerate(test_cases, 1):
                    st.markdown(f"**Test Case {i}:**")
                    col_input, col_output = st.columns(2)
                    with col_input:
                        st.markdown("**Input:**")
                        st.code(test.get('input', ''), language="text")
                    with col_output:
                        st.markdown("**Expected Output:**")
                        st.code(test.get('output', ''), language="text")
                    st.markdown("---")
            else:
                st.info("No test cases available for this problem")
        
        # Code editor and testing
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("### 💻 Your Solution")
            
            # Code editor
            code = st.text_area(
                "Write your code here:",
                value=st.session_state.code,
                height=400,
                key="code_editor",
                help="Define a function named 'solution' that solves the problem"
            )
            st.session_state.code = code
            
            # Action buttons
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button("▶️ Run Tests", type="primary", use_container_width=True):
                    if code.strip():
                        test_cases = problem.get('test_cases', [])
                        with st.spinner("Running tests..."):
                            results = run_code_with_tests(code, test_cases)
                            st.session_state.test_results = results
                            st.rerun()
                    else:
                        st.error("Please write some code first!")
            
            with btn_col2:
                if st.button("📤 Submit Solution", type="secondary", use_container_width=True):
                    if code.strip():
                        test_cases = problem.get('test_cases', [])
                        with st.spinner("Running tests..."):
                            results = run_code_with_tests(code, test_cases)
                            
                            # Check if all passed
                            all_passed = all(r['passed'] for r in results)
                            
                            # Submit to data manager
                            data_manager.submit_solution(
                                competitor_name,
                                problem_id,
                                code,
                                results,
                                all_passed
                            )
                            
                            st.session_state.test_results = results
                            
                            if all_passed:
                                st.success("🎉 All tests passed! Solution submitted successfully!")
                            else:
                                st.warning("⚠️ Some tests failed. Keep trying!")
                            
                            st.rerun()
                    else:
                        st.error("Please write some code first!")
            
            with btn_col3:
                if st.button("🔄 Reset Code", use_container_width=True):
                    st.session_state.code = problem.get('starter_code', '')
                    st.session_state.test_results = None
                    st.rerun()
        
        with col2:
            st.markdown("### 🧪 Test Results")
            
            if st.session_state.test_results:
                results = st.session_state.test_results
                
                # Summary
                passed_count = sum(1 for r in results if r['passed'])
                total_count = len(results)
                
                if passed_count == total_count:
                    st.success(f"✅ All {total_count} tests passed!")
                else:
                    st.warning(f"⚠️ {passed_count}/{total_count} tests passed")
                
                # Individual test results
                for result in results:
                    test_class = "test-passed" if result['passed'] else "test-failed"
                    icon = "✅" if result['passed'] else "❌"
                    
                    with st.expander(f"{icon} Test {result['test_num']} - {'Passed' if result['passed'] else 'Failed'}", expanded=not result['passed']):
                        st.markdown(f"**Input:** `{result['input']}`")
                        st.markdown(f"**Expected:** `{result['expected']}`")
                        st.markdown(f"**Your Output:** `{result['output']}`")
                        
                        if result['error']:
                            st.error(f"Error: {result['error']}")
            else:
                st.info("Click 'Run Tests' to see results here")
            
            # Submission history
            st.markdown("### 📜 Your Submissions")
            # Reload fresh data to show latest submissions
            fresh_comp_data = data_manager.get_competitor_data(competitor_name) or {}
            fresh_problems_data = fresh_comp_data.get('problems', {})
            
            # Convert problem_id to string for Firebase lookup
            problem_id_str = str(problem_id)
            problem_data = fresh_problems_data.get(problem_id_str, {})
            submissions = problem_data.get('submissions', [])
            
            # Debug info
            # if not submissions:
            #     with st.expander("🔍 Debug - Why no submissions?", expanded=False):
            #         st.write(f"Looking for problem_id: `{problem_id}` (type: {type(problem_id).__name__})")
            #         st.write(f"Looking for problem_id_str: `{problem_id_str}`")
            #         st.write(f"Available problems in database: `{list(fresh_problems_data.keys())}`")
            #         st.write(f"Problem data found: `{bool(problem_data)}`")
            #         if problem_data:
            #             st.write(f"Submissions in problem data: `{problem_data.get('submissions', 'NO SUBMISSIONS KEY')}`")
            
            if submissions:
                for i, sub in enumerate(reversed(submissions[-5:]), 1):  # Show last 5
                    passed = sub.get('all_passed', False)
                    icon = "✅" if passed else "❌"
                    # Try both field names for backwards compatibility
                    passed_tests = sub.get('passed_tests', sub.get('tests_passed', 0))
                    total_tests = sub.get('total_tests', 0)
                    timestamp = sub.get('submitted_at', sub.get('timestamp', 'Unknown time'))
                    tests = f"{passed_tests}/{total_tests}"
                    
                    st.markdown(f"{icon} **Attempt {len(submissions) - i + 1}** - {tests} tests - {timestamp}")
            else:
                st.info("No submissions yet")

# Footer
st.markdown("---")
st.caption("💡 Tip: Test your code before submitting to ensure all test cases pass!")
