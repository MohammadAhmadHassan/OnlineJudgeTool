"""
Admin Panel - Problem Management
Upload and manage problems in Firebase
"""
import streamlit as st
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_manager import create_data_manager

st.set_page_config(
    page_title="Problem Management",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Problem Management Dashboard")

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()
backend_type = data_manager.get_backend_type() if hasattr(data_manager, "get_backend_type") else "unknown"

# Admin password
admin_password = st.secrets.get("ADMIN_PASSWORD", "admin123")

if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.markdown("## 🔒 Admin Login")
    password = st.text_input("Enter admin password:", type="password")
    
    if st.button("Login"):
        if password == admin_password:
            st.session_state.admin_authenticated = True
            st.success("✅ Authenticated!")
            st.rerun()
        else:
            st.error("❌ Invalid password")
else:
    # Admin is authenticated
    tab1, tab2, tab3 = st.tabs(["📤 Upload Problems", "📋 View Problems", "🗑️ Delete Problems"])
    
    with tab1:
        st.markdown("### 📤 Upload Problems to Firebase")
        st.caption(f"Backend: `{backend_type}`")
        
        st.info("💡 Upload JSON file with structure like `{'session1': [...]}` or `{'FinalCompetion': [...]}`")
        
        # Level selector
        upload_level = st.selectbox(
            "Select Level",
            options=[1, 2, 3, 4, 5],
            index=0,
            help="Choose the level for these problems. Different levels will be stored separately."
        )
        
        uploaded_file = st.file_uploader("Choose a JSON file", type=['json'])
        
        if uploaded_file is not None:
            try:
                # Read JSON
                problems_data = json.load(uploaded_file)
                
                st.success(f"✅ File loaded successfully!")
                
                # Show preview
                st.markdown("**Preview:**")
                if isinstance(problems_data, dict):
                    detected_levels = set()
                    for collection_key, problems_list in problems_data.items():
                        if isinstance(problems_list, list):
                            num_problems = len(problems_list)
                            st.write(f"- {collection_key}: {num_problems} problems")
                            for problem in problems_list:
                                if isinstance(problem, dict):
                                    level_value = problem.get("level")
                                    if isinstance(level_value, int):
                                        detected_levels.add(level_value)

                    if detected_levels:
                        st.caption("Detected levels in file: " + ", ".join(str(v) for v in sorted(detected_levels)))
                        if len(detected_levels) == 1:
                            detected_level = next(iter(detected_levels))
                            if detected_level != upload_level:
                                st.warning(
                                    f"Selected upload level is {upload_level}, but file problems are level {detected_level}. "
                                    "This mismatch can cause problems not to appear in competitor view."
                                )
                
                # Upload button
                if st.button("🚀 Upload to Firebase", type="primary"):
                    with st.spinner("Uploading..."):
                        try:
                            success = False
                            uploaded_collections = []
                            failed_collections = []

                            # Normalize dictionary uploads into per-collection list uploads.
                            # This is backward compatible with older backends that only
                            # accept session* keys in dict mode.
                            if isinstance(problems_data, dict):
                                collections = {
                                    key: value for key, value in problems_data.items()
                                    if isinstance(value, list)
                                }

                                if not collections:
                                    st.error("❌ No valid problem lists found in the uploaded JSON.")
                                else:
                                    for collection_name, problems_list in collections.items():
                                        ok = data_manager.upload_problems(
                                            problems_data=problems_list,
                                            session_name=collection_name,
                                            level=upload_level
                                        )
                                        if ok:
                                            uploaded_collections.append(collection_name)
                                        else:
                                            failed_collections.append(collection_name)
                                    success = len(failed_collections) == 0

                            # Also allow direct list JSON upload (single collection).
                            elif isinstance(problems_data, list):
                                default_collection = "session1"
                                success = data_manager.upload_problems(
                                    problems_data=problems_data,
                                    session_name=default_collection,
                                    level=upload_level
                                )
                                if success:
                                    uploaded_collections.append(default_collection)
                                else:
                                    failed_collections.append(default_collection)
                            else:
                                st.error("❌ Invalid JSON format. Expected an object or an array.")

                            if success:
                                st.success(f"🎉 Level {upload_level} problems uploaded successfully!")
                                st.info("Uploaded collections: " + ", ".join(uploaded_collections))
                                st.info(
                                    f"Documents created with names like: "
                                    f"level{upload_level}_session1 or level{upload_level}_FinalCompetion."
                                )
                            elif failed_collections:
                                st.error("❌ Failed to upload these collections: " + ", ".join(failed_collections))
                                st.caption("Tip: verify Firebase credentials and that backend is `firebase`.")
                        except Exception as e:
                            st.error(f"❌ Upload error: {e}")
            
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON file: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        st.markdown("---")
        st.markdown("### 📝 Manual Input")
        
        manual_level = st.selectbox(
            "Select Level (Manual)",
            options=[1, 2, 3, 4, 5],
            index=0,
            key="manual_level",
            help="Choose the level for these problems. Different levels will be stored separately."
        )
        
        session_name = st.text_input("Session name (e.g., session1, session2)")
        problems_json = st.text_area("Paste problems JSON (array of problem objects)", height=300)
        
        if st.button("Upload Manual Input"):
            if session_name and problems_json:
                try:
                    problems_list = json.loads(problems_json)
                    success = data_manager.upload_problems(problems_list, session_name, manual_level)
                    
                    if success:
                        st.success(f"✅ Uploaded {len(problems_list)} problems to level{manual_level}_{session_name}")
                    else:
                        st.error("❌ Upload failed")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")
            else:
                st.warning("⚠️ Please provide both session name and problems JSON")
    
    with tab2:
        st.markdown("### 📋 Current Problems in Firebase")
        
        col1, col2 = st.columns(2)
        with col1:
            view_week = st.number_input("Filter by Week (0 = all)", min_value=0, value=0)
        with col2:
            view_level = st.number_input("Filter by Level (0 = all)", min_value=0, value=0)
        
        if st.button("🔍 Load Problems"):
            week_filter = view_week if view_week > 0 else None
            level_filter = view_level if view_level > 0 else None
            
            problems = data_manager.get_problems(week=week_filter, level=level_filter)
            
            if problems:
                st.success(f"Found {len(problems)} problems")
                
                for problem_id, problem in sorted(problems.items()):
                    with st.expander(f"Problem {problem_id}: {problem.get('title', 'Untitled')}"):
                        st.write(f"**Level:** {problem.get('level', 'N/A')}")
                        st.write(f"**Difficulty:** {problem.get('difficulty', 'N/A')}")
                        st.write(f"**Description:** {problem.get('description', 'N/A')}")
                        st.write(f"**Test Cases:** {len(problem.get('test_cases', []))}")
                        
                        if st.checkbox("Show full JSON", key=f"show_{problem_id}"):
                            st.json(problem)
            else:
                st.info("No problems found with the specified filters")
    
    with tab3:
        st.markdown("### 🗑️ Delete Problems")
        st.warning("⚠️ **Warning:** This action cannot be undone!")
        
        delete_session = st.text_input("Session to delete from (e.g., session1)")
        delete_problem_id = st.number_input("Problem ID to delete", min_value=1, value=1)
        
        if st.button("🗑️ Delete Problem", type="secondary"):
            if delete_session:
                confirm = st.checkbox(f"I confirm deletion of Problem {delete_problem_id} from {delete_session}")
                
                if confirm:
                    success = data_manager.delete_problem(delete_session, delete_problem_id)
                    
                    if success:
                        st.success(f"✅ Problem {delete_problem_id} deleted from {delete_session}")
                    else:
                        st.error("❌ Deletion failed")
            else:
                st.warning("Please specify the session name")
    
    # Logout
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
