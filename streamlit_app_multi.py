"""
Deployment Configuration
Set environment variable DASHBOARD_MODE to control which dashboard to show:
- DASHBOARD_MODE=competitor (default) - Show only competitor interface
- DASHBOARD_MODE=judge - Show only judge dashboard  
- DASHBOARD_MODE=spectator - Show only spectator view
- DASHBOARD_MODE=all - Show all dashboards with navigation (current behavior)
"""
import streamlit as st
import os

# Get dashboard mode from environment variable
DASHBOARD_MODE = os.environ.get('DASHBOARD_MODE', 'all').lower()

# Configure page based on mode
if DASHBOARD_MODE == 'competitor':
    st.set_page_config(
        page_title="Competitor Interface",
        page_icon="👨‍💻",
        layout="wide"
    )
    
    st.markdown('<h1 style="text-align: center;">👨‍💻 Competitor Interface</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigate directly to competitor page
    st.switch_page("pages/1_👨‍💻_Competitor.py")

elif DASHBOARD_MODE == 'judge':
    st.set_page_config(
        page_title="Judge Dashboard",
        page_icon="👨‍⚖️",
        layout="wide"
    )
    
    st.markdown('<h1 style="text-align: center;">👨‍⚖️ Judge Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigate directly to judge page
    st.switch_page("pages/2_👨‍⚖️_Judge.py")

elif DASHBOARD_MODE == 'spectator':
    st.set_page_config(
        page_title="Spectator View",
        page_icon="📊",
        layout="wide"
    )
    
    st.markdown('<h1 style="text-align: center;">📊 Live Leaderboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigate directly to spectator page
    st.switch_page("pages/3_📊_Spectator.py")

else:  # all or any other value
    # Show the original landing page with all options
    st.set_page_config(
        page_title="Competition Platform",
        page_icon="🏆",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-title {
            font-size: 3.5rem;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .subtitle {
            text-align: center;
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 3rem;
        }
        .role-card {
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            height: 100%;
        }
        .role-card:hover {
            border-color: #667eea;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
            transform: translateY(-5px);
        }
        .role-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .role-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">🏆 Programming Competition Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Choose your role to get started</p>', unsafe_allow_html=True)
    
    # Role selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">👨‍💻</div>
            <div class="role-title">Competitor</div>
            <p>Solve problems and compete for the top spot!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Enter as Competitor", key="competitor", use_container_width=True, type="primary"):
            st.switch_page("pages/1_👨‍💻_Competitor.py")
    
    with col2:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">👨‍⚖️</div>
            <div class="role-title">Judge</div>
            <p>Monitor and review competitor submissions</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Enter as Judge", key="judge", use_container_width=True, type="primary"):
            st.switch_page("pages/2_👨‍⚖️_Judge.py")
    
    with col3:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">📊</div>
            <div class="role-title">Spectator</div>
            <p>Watch the competition live with real-time updates</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("View Leaderboard", key="spectator", use_container_width=True, type="primary"):
            st.switch_page("pages/3_📊_Spectator.py")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>💡 <strong>Tip:</strong> Each role provides a different view of the competition</p>
    </div>
    """, unsafe_allow_html=True)
