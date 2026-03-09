# -*- coding: utf-8 -*-
"""
Diagnostic Helper for Streamlit App
Add this to your pages to help identify loading issues
"""
import streamlit as st
from datetime import datetime
import time


def show_loading_status():
    """
    Show real-time loading status - add this to the top of your pages
    to see what's taking so long
    """
    status_placeholder = st.empty()
    
    with status_placeholder.container():
        st.info("🔄 Loading app...")
        start_time = time.time()
        
        # Check 1: Session state
        with st.spinner("Checking session state..."):
            time.sleep(0.1)
            st.success(f"✅ Session state OK ({len(st.session_state)} items)")
        
        # Check 2: Data manager
        with st.spinner("Initializing data manager..."):
            try:
                if 'data_manager' not in st.session_state:
                    from data_manager import DataManager
                    st.session_state.data_manager = DataManager()
                st.success("✅ Data manager OK")
            except Exception as e:
                st.error(f"❌ Data manager failed: {e}")
                return False
        
        # Check 3: Firebase connection
        with st.spinner("Checking Firebase connection..."):
            try:
                data_manager = st.session_state.data_manager
                if hasattr(data_manager, 'backend'):
                    health = data_manager.backend.get_health_status()
                    if health.get('initialized'):
                        st.success(f"✅ Firebase connected")
                    else:
                        st.warning("⚠️ Firebase not initialized yet")
            except Exception as e:
                st.warning(f"⚠️ Firebase check: {e}")
        
        elapsed = time.time() - start_time
        st.success(f"✅ App ready in {elapsed:.2f}s")
        time.sleep(1)
    
    # Clear the status
    status_placeholder.empty()
    return True


def show_user_diagnostics():
    """
    Show diagnostic information for troubleshooting
    Add this to sidebar for users experiencing issues
    """
    with st.sidebar.expander("🔍 Diagnostics", expanded=False):
        st.caption("If app is loading slowly, share this info:")
        
        # User info
        st.write("**User Info:**")
        st.text(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        st.text(f"Session items: {len(st.session_state)}")
        
        # Data manager status
        if 'data_manager' in st.session_state:
            try:
                dm = st.session_state.data_manager
                if hasattr(dm, 'backend') and hasattr(dm.backend, 'get_health_status'):
                    health = dm.backend.get_health_status()
                    st.write("**Firebase Status:**")
                    st.json({
                        "initialized": health.get('initialized'),
                        "healthy": health.get('connection_healthy'),
                        "cache_entries": health.get('cache_entries', 0)
                    })
                else:
                    st.warning("Backend status unavailable")
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")
        else:
            st.warning("Data manager not initialized")
        
        # Copy diagnostics
        if st.button("📋 Copy Diagnostics"):
            st.code(f"""
App Load Time: {datetime.now().isoformat()}
Session State: {len(st.session_state)} items
""")


def add_performance_warning(threshold_seconds=5):
    """
    Warn if page takes too long to load
    Wrap your page content with this
    """
    if 'page_load_start' not in st.session_state:
        st.session_state.page_load_start = time.time()
    
    elapsed = time.time() - st.session_state.page_load_start
    
    if elapsed > threshold_seconds:
        st.warning(f"⚠️ Page loaded slowly ({elapsed:.1f}s). If this persists, try refreshing or check your connection.")
        
        with st.expander("Troubleshooting Tips"):
            st.markdown("""
            **Slow loading? Try these:**
            1. Refresh the page (Ctrl+R or Cmd+R)
            2. Clear browser cache
            3. Check your internet connection
            4. Try a different browser
            5. Contact support if issue persists
            """)


def measure_operation(operation_name):
    """
    Decorator to measure operation time
    Usage:
        @measure_operation("Loading competitors")
        def load_data():
            # your code
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            with st.spinner(f"{operation_name}..."):
                result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            if elapsed > 2:  # Warn if over 2 seconds
                st.warning(f"⚠️ {operation_name} took {elapsed:.2f}s")
            
            return result
        return wrapper
    return decorator


# ============================================
# USAGE EXAMPLES
# ============================================

"""
Example 1: Add to top of ANY page for debugging

```python
from diagnostic_helper import show_loading_status

st.set_page_config(page_title="My Page")

# This will show what's loading
show_loading_status()

# Your normal page code here
st.title("My Page")
```

Example 2: Add diagnostics panel for users

```python
from diagnostic_helper import show_user_diagnostics

# In your sidebar
show_user_diagnostics()
```

Example 3: Measure slow operations

```python
from diagnostic_helper import measure_operation

@measure_operation("Loading leaderboard")
def load_leaderboard():
    return data_manager.get_leaderboard()

leaderboard = load_leaderboard()
```

Example 4: Warn about slow pages

```python
from diagnostic_helper import add_performance_warning

# At the top of your page
add_performance_warning(threshold_seconds=3)
```
"""
