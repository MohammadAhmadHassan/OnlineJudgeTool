"""
Competitor Dashboard - Standalone App
For deployment as a separate application
"""
import streamlit as st
import json
import os
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from data_manager import create_data_manager

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
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .problem-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    .problem-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    .problem-solved {
        border-color: #28a745;
        background-color: #f0fff4;
    }
    .problem-failed {
        border-color: #ffc107;
        background-color: #fffef0;
    }
    .code-editor {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        background-color: #f5f5f5;
        border-radius: 5px;
        padding: 1rem;
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
    problems_dir = os.path.join(os.path.dirname(__file__), 'problems')
    
    if os.path.exists(problems_dir):
        for filename in os.listdir(problems_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(problems_dir, filename), 'r') as f:
                        problem = json.load(f)
                        
                        # Extract problem ID from filename
                        import re
                        match = re.search(r'(\d+)', filename)
                        if match:
                            problem_id = int(match.group(1))
                            
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

# Function to run code with tests
def run_code_with_tests(code, test_cases):
    """Execute code against test cases"""
    results = []
    
    for i, test in enumerate(test_cases, 1):
        result = {
            'test_num': i,
            'input': test['input'],
            'expected': test['output'],
            'output': '',
            'passed': False,
            'error': None
        }
        
        try:
            # Create a clean namespace for execution
            namespace = {}
            
            # Execute the solution code
            exec(code, namespace)
            
            if 'solution' not in namespace:
                result['error'] = "No 'solution' function found"
                results.append(result)
                continue
            
            # Capture output
            output_buffer = StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                try:
                    output = namespace['solution'](test['input'])
                    result['output'] = str(output).strip()
                    result['passed'] = result['output'] == str(test['output']).strip()
                except Exception as e:
                    result['error'] = str(e)
                    result['output'] = output_buffer.getvalue()
        
        except Exception as e:
            result['error'] = str(e)
        
        results.append(result)
    
    return results

# Load problems
problems = load_problems()

# Main content
st.markdown('<h1 class="main-header">👨‍💻 Competitor Interface</h1>', unsafe_allow_html=True)

# Login/Registration
if not st.session_state.competitor_name:
    st.markdown("### 🔐 Competitor Login")
    
    with st.form("login_form"):
        name = st.text_input("Enter your name:", placeholder="Your Full Name")
        register_btn = st.form_submit_button("🚀 Join Competition", type="primary", use_container_width=True)
        
        if register_btn:
            if name.strip():
                # Register competitor
                if data_manager.register_competitor(name.strip()):
                    st.session_state.competitor_name = name.strip()
                    st.success(f"Welcome, {name}!")
                    st.rerun()
                else:
                    st.error("Registration failed. Please try again.")
            else:
                st.error("Please enter your name")
    
    st.markdown("---")
    st.info("💡 **Tip:** Make sure to enter your full name for the leaderboard!")

else:
    # Competitor is logged in - Import the competitor page content
    # Since we can't easily import the page content, we'll redirect using a simple message
    st.info("🔄 Loading competitor interface...")
    
    # Import the actual competitor page logic
    import importlib.util
    spec = importlib.util.spec_from_file_location("competitor_page", "pages/1_👨‍💻_Competitor.py")
    competitor_module = importlib.util.module_from_spec(spec)
    
    # Copy the page content by executing it
    # This is a workaround - in production, you'd refactor the page logic into reusable functions
    st.info("⚠️ Please use the multi-page app structure or refactor this code for standalone deployment")
    st.markdown("**For now, this is a placeholder. To deploy, either:**")
    st.markdown("1. Deploy the full app and share only the competitor URL")
    st.markdown("2. Refactor pages/1_👨‍💻_Competitor.py into a reusable module")
