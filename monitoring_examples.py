# Example: How to add monitoring to your Streamlit pages

"""
Add these lines to your Streamlit pages to enable connection monitoring
"""

# ============================================
# Option 1: Simple Health Indicator (Minimal)
# ============================================
# Add to the top of any page after imports:

from firebase_monitor import add_health_indicator

# In your main code:
add_health_indicator()

# ============================================
# Option 2: Full Connection Status (Recommended)
# ============================================
# Add to your competitor/judge/spectator pages:

from firebase_monitor import show_connection_status
import streamlit as st

# Get or create data_manager
if 'data_manager' not in st.session_state:
    from data_manager import DataManager
    st.session_state.data_manager = DataManager()

# Show status in sidebar
show_connection_status(st.session_state.data_manager, location="sidebar")

# ============================================
# Option 3: Debug Panel for Admins/Judges
# ============================================
# Add to Judge dashboard:

from firebase_monitor import show_performance_metrics

# At the bottom of judge page:
with st.sidebar:
    if st.checkbox("🔧 Show Debug Info", key="debug_panel"):
        show_performance_metrics(st.session_state.data_manager)

# ============================================
# Option 4: Error Recovery UI
# ============================================
# Wrap your main code in try-except:

from firebase_monitor import show_error_recovery

try:
    # Your main app code here
    pass
except Exception as e:
    show_error_recovery(str(e))

# ============================================
# Full Example for Competitor Page
# ============================================

import streamlit as st
from data_manager import DataManager
from firebase_monitor import show_connection_status, add_health_indicator, show_error_recovery

st.set_page_config(page_title="Competitor", page_icon="👨‍💻")

# Initialize data manager
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

data_manager = st.session_state.data_manager

# Add health indicator
add_health_indicator()

# Add connection status (optional, for debugging)
# Comment out in production if you don't want users to see it
# show_connection_status(data_manager, location="sidebar")

try:
    # Your competitor page code here
    st.title("Competitor Dashboard")
    
    # Your existing code...
    
except Exception as e:
    # Show user-friendly error recovery options
    show_error_recovery(str(e))

# ============================================
# Full Example for Judge Page
# ============================================

import streamlit as st
from data_manager import DataManager
from firebase_monitor import show_connection_status, show_performance_metrics

st.set_page_config(page_title="Judge", page_icon="👨‍⚖️")

# Initialize
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

data_manager = st.session_state.data_manager

# Show connection status in sidebar
show_connection_status(data_manager, location="sidebar")

# Admin debug panel
with st.sidebar:
    with st.expander("🔧 System Diagnostics"):
        if st.button("Refresh Status"):
            st.rerun()
        show_performance_metrics(data_manager)

try:
    # Your judge dashboard code here
    st.title("Judge Dashboard")
    
    # Your existing code...
    
except Exception as e:
    st.error(f"❌ Error: {e}")
    if st.button("🔄 Retry"):
        st.rerun()
