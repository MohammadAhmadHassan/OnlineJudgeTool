"""
Upload Problems to Firebase
This script uploads problem data from JSON files to Firebase Firestore
"""
import json
import os
from data_manager import create_data_manager

def upload_problems_from_file(file_path, data_manager):
    """Upload problems from a JSON file to Firebase"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            problems_data = json.load(f)
        
        print(f"\n[INFO] Loading problems from: {file_path}")
        print(f"[INFO] Data structure: {list(problems_data.keys())}")
        
        # Upload to Firebase
        success = data_manager.upload_problems(problems_data)
        
        if success:
            print(f"[SUCCESS] ✅ Problems uploaded successfully from {os.path.basename(file_path)}")
        else:
            print(f"[ERROR] ❌ Failed to upload problems from {os.path.basename(file_path)}")
        
        return success
    except Exception as e:
        print(f"[ERROR] Failed to read file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to upload all problems"""
    print("=" * 60)
    print("🚀 FIREBASE PROBLEM UPLOADER")
    print("=" * 60)
    
    # Initialize data manager
    print("\n[INFO] Connecting to Firebase...")
    data_manager = create_data_manager()
    print("[SUCCESS] ✅ Connected to Firebase")
    
    # Get the problems directory
    problems_dir = os.path.join(os.path.dirname(__file__), 'problems')
    
    # Upload from problems directory
    if os.path.exists(problems_dir):
        print(f"\n[INFO] Scanning problems directory: {problems_dir}")
        json_files = [f for f in os.listdir(problems_dir) if f.endswith('.json')]
        print(f"[INFO] Found {len(json_files)} JSON files")
        
        for filename in json_files:
            file_path = os.path.join(problems_dir, filename)
            upload_problems_from_file(file_path, data_manager)
    
    # Upload from Level1_AllProblems.json if it exists
    level1_path = os.path.join(os.path.dirname(__file__), 'Level1_AllProblems.json')
    if os.path.exists(level1_path):
        upload_problems_from_file(level1_path, data_manager)
    
    print("\n" + "=" * 60)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 60)
    print("\n💡 You can now remove local problem JSON files if desired.")
    print("   The app will read problems from Firebase.")

if __name__ == "__main__":
    main()
