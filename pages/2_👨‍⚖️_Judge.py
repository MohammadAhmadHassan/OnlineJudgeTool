"""
Judge Dashboard - Streamlit Version
Monitor and review competitor submissions in real-time
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import create_data_manager

# Page configuration
st.set_page_config(
    page_title="Judge Dashboard",
    page_icon="👨‍⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    .success-card { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .warning-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .info-card { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .primary-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    
    .problem-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        background: white;
    }
    .approved { border-left: 4px solid #27ae60; }
    .rejected { border-left: 4px solid #e74c3c; }
    .pending { border-left: 4px solid #f39c12; }
    
    .code-viewer {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
    }
    
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-solved { background: #d4edda; color: #155724; }
    .status-pending { background: #fff3cd; color: #856404; }
    .status-failed { background: #f8d7da; color: #721c24; }
    .status-approved { background: #d1ecf1; color: #0c5460; }
    .status-rejected { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()

# Header
st.markdown("# 👨‍⚖️ Judge Dashboard")
st.markdown("Monitor and review competitor submissions in real-time")
st.markdown("---")

# Auto-refresh toggle in sidebar
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, help="Automatically refresh data every 5 seconds")
    
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Filters")
    show_pending_only = st.checkbox("Show only pending reviews", value=False)
    search_query = st.text_input("🔍 Search competitor", "")
    
    st.markdown("---")
    if st.button("📊 Export Report", use_container_width=True):
        st.info("Export functionality coming soon!")
    
    # Fix missing judge_approval fields button
    if st.button("🔧 Fix Missing Approval Fields", use_container_width=True, 
                 help="Adds judge_approval field to problems that don't have it"):
        if hasattr(data_manager.backend, 'fix_missing_judge_approval_fields'):
            with st.spinner("Fixing database..."):
                count = data_manager.backend.fix_missing_judge_approval_fields()
            st.success(f"✅ Fixed {count} problems!")
            st.rerun()
        else:
            st.warning("This function is only available for Firebase backend")
    
    if st.button("🔄 Reset Competition", use_container_width=True):
        if st.session_state.get('confirm_reset'):
            data_manager.reset_competition()
            st.success("Competition reset!")
            st.session_state.confirm_reset = False
            st.rerun()
        else:
            st.session_state.confirm_reset = True
            st.warning("Click again to confirm reset")

# Auto-refresh timer
if auto_refresh:
    import time
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    if time.time() - st.session_state.last_refresh > 5:
        st.session_state.last_refresh = time.time()
        st.rerun()

# Get data
competitors = data_manager.get_all_competitors()
leaderboard = data_manager.get_leaderboard()

# Calculate statistics
total_competitors = len(competitors)
total_submissions = sum(
    len(comp.get('problems', {}).get(pid, {}).get('submissions', []))
    for comp in competitors.values()
    for pid in comp.get('problems', {})
)
problems_solved = sum(
    1 for comp in competitors.values()
    for pid, pdata in comp.get('problems', {}).items()
    if pdata.get('best_result', {}).get('all_passed', False)
)

# Count pending reviews
pending_count = sum(
    1 for comp in competitors.values()
    for pid, pdata in comp.get('problems', {}).items()
    if pdata.get('best_result', {}).get('all_passed', False) and 
    pdata.get('judge_approval') not in ['approved', 'rejected']
)

# Statistics Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card info-card">
        <p class="stat-value">{total_competitors}</p>
        <p class="stat-label">Total Competitors</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card success-card">
        <p class="stat-value">{pending_count}</p>
        <p class="stat-label">Pending Reviews</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card primary-card">
        <p class="stat-value">{total_submissions}</p>
        <p class="stat-label">Total Submissions</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card warning-card">
        <p class="stat-value">{problems_solved}</p>
        <p class="stat-label">Problems Solved</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Main content - two columns
left_col, right_col = st.columns([2, 3])

with left_col:
    st.markdown("### 👥 Competitors")
    
    # Prepare competitor data for table
    competitor_data = []
    for name, data in competitors.items():
        problems = data.get('problems', {})
        
        # Count pending reviews
        pending_reviews = sum(
            1 for pid, pdata in problems.items()
            if pdata.get('best_result', {}).get('all_passed', False) and 
            pdata.get('judge_approval') not in ['approved', 'rejected']
        )
        
        # Get current problem
        current_problem = data.get('current_problem', '-')
        
        # Count solved
        solved = sum(
            1 for pdata in problems.values()
            if pdata.get('best_result', {}).get('all_passed', False)
        )
        
        # Total submissions
        submissions = sum(len(pdata.get('submissions', [])) for pdata in problems.values())
        
        # Status
        status = "Active" if current_problem != '-' else "Idle"
        
        # Apply filters
        if show_pending_only and pending_reviews == 0:
            continue
        if search_query and search_query.lower() not in name.lower():
            continue
        
        competitor_data.append({
            'Name': name,
            'Pending': pending_reviews,
            'Current': current_problem,
            'Solved': solved,
            'Submissions': submissions,
            'Status': status
        })
    
    if competitor_data:
        # Create dataframe
        df = pd.DataFrame(competitor_data)
        
        # Display table with selection
        selected_competitor = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Get selected competitor name
        if selected_competitor and selected_competitor.selection.rows:
            selected_idx = selected_competitor.selection.rows[0]
            selected_name = competitor_data[selected_idx]['Name']
            st.session_state.selected_competitor = selected_name
        elif 'selected_competitor' not in st.session_state and competitor_data:
            st.session_state.selected_competitor = competitor_data[0]['Name']
    else:
        st.info("No competitors found matching your filters")
        st.session_state.selected_competitor = None

with right_col:
    if st.session_state.get('selected_competitor'):
        competitor_name = st.session_state.selected_competitor
        st.markdown(f"### 📋 {competitor_name}'s Details")
        
        # Get competitor data - RELOAD FRESH DATA
        comp_data = data_manager.get_competitor_data(competitor_name)
        if not comp_data:
            st.error(f"Could not load data for {competitor_name}")
            st.stop()
        
        problems = comp_data.get('problems', {})
        
        # Debug info
        with st.expander("🔍 Debug Info", expanded=False):
            st.write(f"**Backend Type:** {data_manager.get_backend_type()}")
            st.write(f"**Problems keys:** {list(problems.keys())}")
            for pid, pdata in problems.items():
                st.write(f"**Problem {pid} approval status:** {pdata.get('judge_approval', 'NOT SET')}")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📝 Problem Status", "📜 Submission History", "💻 Code Review"])
        
        with tab1:
            st.markdown("#### Problem Status")
            
            # Problem filter
            filter_options = ["All Problems", "Needs Review (Pending)", "Approved Only", 
                            "Rejected Only", "Solved (All Passed)"]
            problem_filter = st.radio("Filter:", filter_options, horizontal=True, key="problem_filter")
            
            if problems:
                for problem_id, problem_data in sorted(problems.items()):
                    best_result = problem_data.get('best_result', {})
                    submissions = problem_data.get('submissions', [])
                    judge_approval = problem_data.get('judge_approval', 'pending')
                    
                    # Apply filter
                    all_passed = best_result.get('all_passed', False)
                    if problem_filter == "Needs Review (Pending)" and (not all_passed or judge_approval != 'pending'):
                        continue
                    if problem_filter == "Approved Only" and judge_approval != 'approved':
                        continue
                    if problem_filter == "Rejected Only" and judge_approval != 'rejected':
                        continue
                    if problem_filter == "Solved (All Passed)" and not all_passed:
                        continue
                    
                    # Status badge
                    if all_passed:
                        status_class = "status-solved"
                        status_text = "✓ Solved"
                    elif submissions:
                        status_class = "status-failed"
                        status_text = "✗ Failed"
                    else:
                        status_class = "status-pending"
                        status_text = "○ Not Attempted"
                    
                    # Approval badge
                    approval_class = f"status-{judge_approval}"
                    approval_text = judge_approval.capitalize()
                    
                    # Problem card CSS class
                    card_class = f"problem-card {judge_approval}"
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                        <strong>Problem {problem_id}</strong>
                        <span class="status-badge {status_class}">{status_text}</span>
                        <span class="status-badge {approval_class}">Judge: {approval_text}</span>
                        <br>
                        <small>Attempts: {len(submissions)} | Tests: {best_result.get('passed_tests', 0)}/{best_result.get('total_tests', 0)}</small>
                        <br>
                        <small>Last: {submissions[-1].get('submitted_at', 'Never') if submissions else 'Never'}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No problems attempted yet")
        
        with tab2:
            st.markdown("#### Submission History")
            
            # Collect all submissions
            all_submissions = []
            for problem_id, problem_data in problems.items():
                for submission in problem_data.get('submissions', []):
                    all_submissions.append({
                        'Time': submission.get('submitted_at', submission.get('timestamp', '')),
                        'Problem': f"Problem {problem_id}",
                        'Tests Passed': f"{submission.get('passed_tests', submission.get('tests_passed', 0))}/{submission.get('total_tests', 0)}",
                        'Status': '✓ All Passed' if submission.get('all_passed') else '✗ Failed'
                    })
            
            if all_submissions:
                # Sort by time (most recent first)
                all_submissions.sort(key=lambda x: x['Time'], reverse=True)
                df_history = pd.DataFrame(all_submissions)
                st.dataframe(df_history, use_container_width=True, hide_index=True)
            else:
                st.info("No submissions yet")
        
        with tab3:
            st.markdown("#### Code Review")
            
            # Problem selector
            problem_ids = sorted(problems.keys())
            if problem_ids:
                # Use a unique key for the selectbox to prevent state issues
                selected_problem = st.selectbox(
                    "Select problem to review:", 
                    problem_ids,
                    format_func=lambda x: f"Problem {x}",
                    key=f"problem_selector_{competitor_name}"
                )
                
                if selected_problem:
                    # Reload fresh data to get latest problem info
                    fresh_comp_data = data_manager.get_competitor_data(competitor_name)
                    if not fresh_comp_data:
                        st.error("Could not load competitor data")
                        st.stop()
                    
                    fresh_problems = fresh_comp_data.get('problems', {})
                    problem_id_str = str(selected_problem)
                    problem_data = fresh_problems.get(problem_id_str, {})
                    submissions = problem_data.get('submissions', [])
                    judge_approval = problem_data.get('judge_approval', 'pending')
                    
                    # Get most recent submission
                    most_recent = submissions[-1] if submissions else {}
                    
                    # Show approval status
                    st.markdown(f"**Current Status:** `{judge_approval.upper()}`")
                    
                    # Approval buttons
                    col_a, col_b, col_c = st.columns([1, 1, 3])
                    with col_a:
                        if st.button("✅ Approve", use_container_width=True, type="primary", key=f"approve_{selected_problem}"):
                            # Convert to int if it's a string
                            problem_id_int = int(selected_problem) if isinstance(selected_problem, str) else selected_problem
                            st.info(f"Approving problem {problem_id_int} for {competitor_name}...")
                            success = data_manager.set_judge_approval(competitor_name, problem_id_int, 'approved')
                            if success:
                                st.success("✅ Solution approved successfully!")
                            else:
                                st.error("❌ Failed to approve solution. Check the terminal/console for detailed error messages.")
                            st.rerun()
                    with col_b:
                        if st.button("❌ Reject", use_container_width=True, type="secondary", key=f"reject_{selected_problem}"):
                            # Convert to int if it's a string
                            problem_id_int = int(selected_problem) if isinstance(selected_problem, str) else selected_problem
                            st.info(f"Rejecting problem {problem_id_int} for {competitor_name}...")
                            success = data_manager.set_judge_approval(competitor_name, problem_id_int, 'rejected')
                            if success:
                                st.warning("❌ Solution rejected")
                            else:
                                st.error("❌ Failed to reject solution. Check the terminal/console for detailed error messages.")
                            st.rerun()
                    
                    # Show submission info
                    if submissions:
                        st.info(f"📝 Showing submission {len(submissions)} of {len(submissions)} (most recent)")
                    
                    # Show code
                    code = most_recent.get('code', 'No code available')
                    st.markdown("**Submitted Code:**")
                    st.code(code, language="python", line_numbers=True)
                    
                    # Show test results
                    st.markdown("**Test Results:**")
                    test_results = most_recent.get('test_results', [])
                    if test_results:
                        for i, result in enumerate(test_results, 1):
                            status_icon = "✅" if result.get('passed') else "❌"
                            with st.expander(f"{status_icon} Test {i} - {'Passed' if result.get('passed') else 'Failed'}"):
                                st.write(f"**Input:** `{result.get('input', 'N/A')}`")
                                st.write(f"**Expected:** `{result.get('expected', 'N/A')}`")
                                st.write(f"**Got:** `{result.get('output', 'N/A')}`")
                    else:
                        st.info("No test results available")
            else:
                st.info("No problems attempted yet")
    else:
        st.info("👈 Select a competitor from the list to view details")

# Footer with last update time
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
