"""
Spectator View - Streamlit Version
Live leaderboard and competition statistics
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import create_data_manager

# Page configuration
st.set_page_config(
    page_title="Spectator View",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .podium-container {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        gap: 2rem;
        margin: 2rem 0;
    }
    .podium-place {
        text-align: center;
        padding: 2rem 1.5rem;
        border-radius: 15px;
        min-width: 150px;
        color: white;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .first-place {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        order: 2;
        margin-bottom: 0;
    }
    .second-place {
        background: linear-gradient(135deg, #C0C0C0 0%, #808080 100%);
        order: 1;
        margin-bottom: 2rem;
    }
    .third-place {
        background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%);
        order: 3;
        margin-bottom: 4rem;
    }
    .podium-rank {
        font-size: 3rem;
        font-weight: 900;
        margin: 0;
    }
    .podium-name {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .podium-score {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    .stat-card-spectator {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .leaderboard-table {
        width: 100%;
        border-collapse: collapse;
    }
    .leaderboard-table th {
        background: #2c3e50;
        color: white;
        padding: 1rem;
        text-align: left;
        font-weight: 700;
    }
    .leaderboard-table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #ecf0f1;
    }
    .leaderboard-table tr:hover {
        background: #f8f9fa;
    }
    .rank-badge {
        display: inline-block;
        width: 30px;
        height: 30px;
        line-height: 30px;
        border-radius: 50%;
        background: #3498db;
        color: white;
        font-weight: 700;
        text-align: center;
    }
    .rank-1 { background: #FFD700; color: #000; }
    .rank-2 { background: #C0C0C0; color: #000; }
    .rank-3 { background: #CD7F32; color: #fff; }
</style>
""", unsafe_allow_html=True)

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()

# Auto-refresh
if 'last_refresh_spectator' not in st.session_state:
    st.session_state.last_refresh_spectator = datetime.now()

# Check if 3 seconds have passed
import time
current_time = time.time()
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = current_time

if current_time - st.session_state.last_refresh_time > 3:
    st.session_state.last_refresh_time = current_time
    st.rerun()

# Header
st.markdown("# 📊 Live Leaderboard")
st.markdown("Real-time competition standings")
st.markdown("---")

# Get leaderboard data
leaderboard = data_manager.get_leaderboard()
competitors = data_manager.get_all_competitors()

# Statistics
total_competitors = len(competitors)
total_problems_solved = sum(entry.get('problems_solved', 0) for entry in leaderboard)
total_submissions = sum(
    len(comp.get('problems', {}).get(pid, {}).get('submissions', []))
    for comp in competitors.values()
    for pid in comp.get('problems', {})
)

# Stats row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card-spectator">
        <div style="font-size: 2.5rem; font-weight: 700;">{total_competitors}</div>
        <div style="font-size: 1rem;">Competitors</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card-spectator" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
        <div style="font-size: 2.5rem; font-weight: 700;">{total_problems_solved}</div>
        <div style="font-size: 1rem;">Problems Solved</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card-spectator" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div style="font-size: 2.5rem; font-weight: 700;">{total_submissions}</div>
        <div style="font-size: 1rem;">Total Submissions</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    active_count = sum(1 for c in competitors.values() if c.get('current_problem'))
    st.markdown(f"""
    <div class="stat-card-spectator" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <div style="font-size: 2.5rem; font-weight: 700;">{active_count}</div>
        <div style="font-size: 1rem;">Active Now</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Podium for top 3
if len(leaderboard) >= 3:
    st.markdown("## 🏆 Top 3 Champions")
    
    top3 = leaderboard[:3]
    
    # Calculate approval scores
    for entry in top3:
        approved = entry.get('approved_problems', 0)
        rejected = entry.get('rejected_problems', 0)
        approval_score = approved - rejected
        if approval_score > 0:
            entry['approval_display'] = f"+{approval_score}"
        elif approval_score < 0:
            entry['approval_display'] = f"{approval_score}"
        else:
            entry['approval_display'] = "0"
    
    # Create podium using Streamlit columns
    col_second, col_first, col_third = st.columns([1, 1, 1])
    
    # Second Place (Left)
    with col_second:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #C0C0C0 0%, #808080 100%); 
                    padding: 2rem 1.5rem; border-radius: 15px; text-align: center; 
                    color: white; box-shadow: 0 8px 16px rgba(0,0,0,0.2); margin-top: 2rem;">
            <div style="font-size: 3rem; font-weight: 900; margin: 0;">🥈</div>
            <div style="font-size: 1.3rem; font-weight: 700; margin: 0.5rem 0;">{top3[1]['name']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Approval: {top3[1]['approval_display']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Solved: {top3[1]['problems_solved']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Tests: {top3[1]['total_tests_passed']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # First Place (Center)
    with col_first:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                    padding: 2rem 1.5rem; border-radius: 15px; text-align: center; 
                    color: white; box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
            <div style="font-size: 3rem; font-weight: 900; margin: 0;">🥇</div>
            <div style="font-size: 1.3rem; font-weight: 700; margin: 0.5rem 0;">{top3[0]['name']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Approval: {top3[0]['approval_display']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Solved: {top3[0]['problems_solved']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Tests: {top3[0]['total_tests_passed']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Third Place (Right)
    with col_third:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%); 
                    padding: 2rem 1.5rem; border-radius: 15px; text-align: center; 
                    color: white; box-shadow: 0 8px 16px rgba(0,0,0,0.2); margin-top: 4rem;">
            <div style="font-size: 3rem; font-weight: 900; margin: 0;">🥉</div>
            <div style="font-size: 1.3rem; font-weight: 700; margin: 0.5rem 0;">{top3[2]['name']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Approval: {top3[2]['approval_display']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Solved: {top3[2]['problems_solved']}</div>
            <div style="font-size: 1.1rem; opacity: 0.95;">Tests: {top3[2]['total_tests_passed']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)

# Full leaderboard table
st.markdown("## 📋 Full Rankings")

if leaderboard:
    # Prepare data for display
    leaderboard_data = []
    for rank, entry in enumerate(leaderboard, 1):
        approved = entry.get('approved_problems', 0)
        rejected = entry.get('rejected_problems', 0)
        approval_score = approved - rejected
        
        if approval_score > 0:
            approval_display = f"+{approval_score}"
        elif approval_score < 0:
            approval_display = f"{approval_score}"
        else:
            approval_display = "0"
        
        leaderboard_data.append({
            'Rank': rank,
            'Name': entry['name'],
            'Approval Score': approval_display,
            'Approved': approved,
            'Rejected': rejected,
            'Solved': entry['problems_solved'],
            'Tests Passed': entry['total_tests_passed']
        })
    
    # Create DataFrame
    df = pd.DataFrame(leaderboard_data)
    
    # Style the dataframe
    def highlight_top3(row):
        if row['Rank'] == 1:
            return ['background-color: #FFD70030'] * len(row)
        elif row['Rank'] == 2:
            return ['background-color: #C0C0C030'] * len(row)
        elif row['Rank'] == 3:
            return ['background-color: #CD7F3230'] * len(row)
        return [''] * len(row)
    
    styled_df = df.style.apply(highlight_top3, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=500
    )
else:
    st.info("No competitors have registered yet. Leaderboard will appear when competition starts!")

# Footer
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"🔄 Auto-refreshing every 3 seconds | Last update: {datetime.now().strftime('%H:%M:%S')}")
with col2:
    if st.button("🔄 Refresh Now", type="secondary"):
        st.rerun()
