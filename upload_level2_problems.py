"""
Upload Level 2 Problems to Firebase
This script uploads level 2 problems with level-specific document naming
"""
import json
from data_manager import create_data_manager

def upload_level2_problems():
    """Upload Level 2 problems to Firebase"""
    
    # Initialize data manager (will use Firebase if configured)
    data_manager = create_data_manager()
    
    # Check backend type
    if data_manager.get_backend_type() != 'firebase':
        print("[ERROR] This script requires Firebase to be configured")
        print("Create 'firebase_credentials.json' with your service account key")
        return False
    
    # Load Level 2 problems from JSON file
    # You'll need to create Level2_AllProblems_Fixed.json with the same structure
    json_file = 'Level2_AllProblems_Fixed.json'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            problems_data = json.load(f)
        
        print(f"[INFO] Loaded problems from {json_file}")
        print(f"[INFO] Sessions found: {list(problems_data.keys())}")
        
        # Upload to Firebase with level=2
        success = data_manager.upload_problems(
            problems_data=problems_data,
            level=2  # This will create level2_session1, level2_session2, etc.
        )
        
        if success:
            print("[SUCCESS] Level 2 problems uploaded successfully!")
            print("[INFO] Documents created with names like: level2_session1, level2_session2, etc.")
        else:
            print("[ERROR] Failed to upload Level 2 problems")
            
        return success
        
    except FileNotFoundError:
        print(f"[ERROR] File not found: {json_file}")
        print(f"[INFO] Please create {json_file} with your Level 2 problems")
        print("[INFO] Use the same structure as Level1_AllProblems_Fixed.json")
        return False
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    upload_level2_problems()
