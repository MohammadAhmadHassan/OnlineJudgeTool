# -*- coding: utf-8 -*-
"""
Migrate competition data from JSON to Firebase
Run this script to transfer existing competition data to Firebase Firestore
"""
import json
import sys
from firebase_data_manager import FirebaseDataManager


def migrate():
    """Migrate data from JSON to Firebase"""
    print("=" * 60)
    print("  MIGRATION: JSON → Firebase Firestore")
    print("=" * 60)
    print()
    
    # Load JSON data
    print("📂 Loading competition_data.json...")
    try:
        with open('competition_data.json', 'r') as f:
            data = json.load(f)
        print(f"   ✓ Loaded {len(data.get('competitors', {}))} competitors")
    except FileNotFoundError:
        print("   ✗ Error: competition_data.json not found")
        print("   → Make sure the file exists in the current directory")
        return False
    except json.JSONDecodeError as e:
        print(f"   ✗ Error: Invalid JSON format - {e}")
        return False
    
    # Initialize Firebase
    print("\n🔥 Connecting to Firebase Firestore...")
    try:
        firebase = FirebaseDataManager()
        print("   ✓ Connected successfully")
    except Exception as e:
        print(f"   ✗ Error connecting to Firebase: {e}")
        print("\n   Troubleshooting:")
        print("   1. Ensure firebase_credentials.json exists")
        print("   2. Install Firebase SDK: pip install firebase-admin")
        print("   3. Check your internet connection")
        return False
    
    # Confirm migration
    print("\n⚠️  WARNING: This will overwrite existing Firebase data!")
    confirm = input("   Continue? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("   → Migration cancelled")
        return False
    
    # Migrate competition metadata
    print("\n📋 Migrating competition metadata...")
    try:
        if data.get('competition_started'):
            firebase.competition_ref.document('metadata').set({
                'competition_started': data.get('competition_started', False),
                'start_time': data.get('start_time'),
                'problems_loaded': data.get('problems_loaded', [])
            })
            print("   ✓ Competition metadata migrated")
        else:
            print("   → Competition not started yet")
    except Exception as e:
        print(f"   ✗ Error migrating metadata: {e}")
    
    # Migrate competitors
    competitors = data.get('competitors', {})
    print(f"\n👥 Migrating {len(competitors)} competitors...")
    
    migrated_count = 0
    failed_count = 0
    
    for name, competitor_data in competitors.items():
        try:
            print(f"   → {name}...", end=' ')
            
            # Write directly to Firestore
            doc_ref = firebase.competitors_ref.document(name)
            doc_ref.set(competitor_data)
            
            migrated_count += 1
            print("✓")
            
        except Exception as e:
            failed_count += 1
            print(f"✗ ({e})")
    
    # Summary
    print("\n" + "=" * 60)
    print("  MIGRATION SUMMARY")
    print("=" * 60)
    print(f"  ✓ Successfully migrated: {migrated_count} competitors")
    if failed_count > 0:
        print(f"  ✗ Failed to migrate: {failed_count} competitors")
    print()
    
    # Verify migration
    print("🔍 Verifying migration...")
    try:
        leaderboard = firebase.get_leaderboard()
        all_competitors = firebase.get_all_competitors()
        
        print(f"   ✓ Leaderboard entries: {len(leaderboard)}")
        print(f"   ✓ Total competitors: {len(all_competitors)}")
        
        if len(all_competitors) == len(competitors):
            print("   ✓ All competitors verified!")
        else:
            print(f"   ⚠ Mismatch: Expected {len(competitors)}, found {len(all_competitors)}")
        
    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
    
    print("\n" + "=" * 60)
    print("  MIGRATION COMPLETE! 🎉")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Open Firebase Console to verify data")
    print("  2. Run 'python launcher.py' to test")
    print("  3. Original data preserved in competition_data.json")
    print()
    
    return True


if __name__ == "__main__":
    print()
    success = migrate()
    print()
    sys.exit(0 if success else 1)
