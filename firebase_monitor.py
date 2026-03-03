# -*- coding: utf-8 -*-
"""
Firebase Monitor
Helper functions for monitoring Firebase connection health in Streamlit
"""
import streamlit as st
from datetime import datetime


def show_connection_status(data_manager, location="sidebar"):
    """
    Display connection status in Streamlit
    
    Args:
        data_manager: The DataManager instance
        location: "sidebar" or "main" - where to display the status
    """
    try:
        if not hasattr(data_manager, 'backend'):
            return
        
        backend = data_manager.backend
        
        # Only show for Firebase backend
        if not hasattr(backend, 'get_health_status'):
            return
        
        health = backend.get_health_status()
        
        # Choose where to display
        display = st.sidebar if location == "sidebar" else st
        
        with display.expander("🔧 System Status", expanded=False):
            # Connection status
            if health.get('connection_healthy'):
                st.success("🟢 Connected")
            else:
                st.error("🔴 Connection Issues")
            
            # Detailed info
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Cache Entries", health.get('cache_entries', 0))
                st.metric("Max Retries", health.get('max_retries', 3))
            
            with col2:
                st.metric("Timeout (s)", health.get('timeout_setting', 10))
                if health.get('seconds_since_check'):
                    st.metric("Last Check", f"{health.get('seconds_since_check', 0):.1f}s ago")
            
            # Cache stats
            if hasattr(backend, 'get_cache_stats'):
                cache_stats = backend.get_cache_stats()
                if cache_stats.get('total_entries', 0) > 0:
                    st.caption(f"**Cache Status:** {cache_stats['total_entries']} entries")
            
            # Current time
            st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
            
    except Exception as e:
        st.sidebar.error(f"⚠️ Monitor error: {str(e)[:50]}")


def show_error_recovery(error_message=None):
    """
    Display error recovery options
    
    Args:
        error_message: Optional error message to display
    """
    st.error("🚨 Connection Error Detected")
    
    if error_message:
        with st.expander("Error Details"):
            st.code(error_message)
    
    st.info("The system will automatically retry the operation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Retry Now", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("🏠 Go to Home"):
            st.session_state.clear()
            st.rerun()


def add_health_indicator():
    """
    Add a simple health indicator to the sidebar
    """
    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        st.sidebar.caption(f"🟢 Active | {current_time}")
    except:
        st.sidebar.caption("⚠️ Status Unknown")


def show_performance_metrics(data_manager):
    """
    Display performance metrics for debugging
    """
    try:
        if not hasattr(data_manager, 'backend'):
            return
        
        backend = data_manager.backend
        
        if not hasattr(backend, 'get_cache_stats'):
            return
        
        with st.expander("📊 Performance Metrics"):
            cache_stats = backend.get_cache_stats()
            
            st.write("**Cache Status:**")
            st.json({
                "total_entries": cache_stats.get('total_entries', 0),
                "entries": cache_stats.get('entries', {})
            })
            
            if hasattr(backend, 'get_health_status'):
                health = backend.get_health_status()
                st.write("**Connection Health:**")
                st.json(health)
    
    except Exception as e:
        st.error(f"Could not load performance metrics: {e}")
