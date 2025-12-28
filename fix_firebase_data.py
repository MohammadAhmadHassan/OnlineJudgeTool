"""
Quick script to fix existing Firebase data by adding missing judge_approval fields
Run this once to update your existing data structure
"""

from data_manager import create_data_manager

def main():
    print("=" * 60)
    print("Firebase Data Fix Utility")
    print("=" * 60)
    print()
    
    # Create data manager
    dm = create_data_manager()
    
    print(f"Backend type: {dm.get_backend_type()}")
    print()
    
    if dm.get_backend_type() == 'firebase':
        print("Checking for missing judge_approval fields...")
        print()
        
        # Run the fix
        count = dm.backend.fix_missing_judge_approval_fields()
        
        print()
        print("=" * 60)
        print(f"COMPLETE: Fixed {count} problems")
        print("=" * 60)
        print()
        print("You can now use the judge approval system!")
        print("Restart your Streamlit app to see the changes.")
    else:
        print("This script only works with Firebase backend.")
        print("Your current backend is:", dm.get_backend_type())

if __name__ == "__main__":
    main()
