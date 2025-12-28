"""
Streamlit Competition Platform - Main Entry Point
Multi-page application for competitors, judges, and spectators
"""
import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Competition Platform",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Main landing page
st.markdown('<h1 class="main-header">🏆 Competition Platform</h1>', unsafe_allow_html=True)
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 👨‍💻 Competitor Interface")
    st.write("Register and solve programming problems")
    if st.button("Enter as Competitor", key="competitor"):
        st.switch_page("pages/1_👨‍💻_Competitor.py")

with col2:
    st.markdown("### 👨‍⚖️ Judge Dashboard")
    st.write("Monitor and review submissions")
    if st.button("Enter as Judge", key="judge"):
        st.switch_page("pages/2_👨‍⚖️_Judge.py")

with col3:
    st.markdown("### 📊 Spectator View")
    st.write("View live leaderboard")
    if st.button("View Leaderboard", key="spectator"):
        st.switch_page("pages/3_📊_Spectator.py")

st.markdown("---")
st.info("💡 **Tip:** Use the sidebar to navigate between different views once you've selected a role.")
