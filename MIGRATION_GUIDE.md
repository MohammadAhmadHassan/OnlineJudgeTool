# Migration Guide: JSON to Firebase

## Overview
This guide helps you migrate from local JSON storage to Firebase Firestore for multi-device support.

---

## Why Migrate?

### Local JSON (Before)
❌ Single device only  
❌ No real-time sync  
❌ Manual data sharing needed  
✅ Works offline  
✅ No setup required  

### Firebase Firestore (After)
✅ Multiple devices simultaneously  
✅ Real-time synchronization  
✅ Cloud-based (access from anywhere)  
✅ Automatic backups  
❌ Requires internet  
❌ Initial setup needed  

---

## Migration Steps

### Option 1: Fresh Start (Recommended)
Simply configure Firebase (see `FIREBASE_SETUP.md`) and start a new competition.

### Option 2: Migrate Existing Data

If you have existing competition data in `competition_data.json` that you want to keep:

1. **Backup your current data:**
   ```powershell
   copy competition_data.json competition_data_backup.json
   ```

2. **Setup Firebase** (follow `FIREBASE_SETUP.md`)

3. **Run the migration script:**
   ```powershell
   python migrate_to_firebase.py
   ```

4. **Verify migration:**
   - Open Firebase Console
   - Check Firestore Database
   - Verify all competitors and submissions are present

---

## Migration Script

Create `migrate_to_firebase.py`:

```python
# -*- coding: utf-8 -*-
"""
Migrate competition data from JSON to Firebase
"""
import json
from firebase_data_manager import FirebaseDataManager

def migrate():
    """Migrate data from JSON to Firebase"""
    print("Starting migration...")
    
    # Load JSON data
    try:
        with open('competition_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: competition_data.json not found")
        return
    
    # Initialize Firebase
    try:
        firebase = FirebaseDataManager()
    except Exception as e:
        print(f"Error connecting to Firebase: {e}")
        return
    
    # Migrate competition metadata
    print("Migrating competition metadata...")
    if data.get('competition_started'):
        firebase.start_competition()
    
    # Migrate competitors
    competitors = data.get('competitors', {})
    print(f"Migrating {len(competitors)} competitors...")
    
    for name, competitor_data in competitors.items():
        print(f"  → Migrating {name}...")
        
        # Register competitor
        firebase.register_competitor(name)
        
        # Update competitor data directly in Firestore
        doc_ref = firebase.competitors_ref.document(name)
        doc_ref.set(competitor_data)
    
    print("✓ Migration complete!")
    print(f"  - Migrated {len(competitors)} competitors")
    
    # Verify
    print("\nVerifying migration...")
    leaderboard = firebase.get_leaderboard()
    print(f"✓ Leaderboard has {len(leaderboard)} entries")
    
    print("\nMigration successful! You can now use Firebase.")
    print("Original data is preserved in competition_data.json")

if __name__ == "__main__":
    migrate()
```

---

## Switching Between Backends

The system automatically chooses the backend:

### To use Firebase:
1. Place `firebase_credentials.json` in the project folder
2. Run the application
3. Console shows: `"✓ Connected to Firebase Firestore"`

### To use Local JSON:
1. Remove or rename `firebase_credentials.json`
2. Run the application
3. Console shows: `"ℹ Using local JSON storage"`

---

## Data Synchronization

### How it works:
1. **Competitor Interface** writes to database when:
   - Competitor registers
   - Switches problems
   - Submits solution

2. **Judge Dashboard** reads from database:
   - Every 10 seconds (auto-refresh)
   - Or manually via Refresh button

3. **Spectator Dashboard** reads from database:
   - Every 10 seconds (auto-refresh)
   - Or manually via Refresh button

### Multi-Device Scenario:
```
Device 1 (Competitor A) → Firebase → Device 2 (Judge)
                                   ↘ Device 3 (Spectator)
                                   ↘ Device 4 (Competitor B)
```

All devices see updates within ~1-2 seconds!

---

## Troubleshooting Migration

### "Module 'firebase_admin' not found"
```powershell
pip install firebase-admin
```

### "Permission denied" during migration
- Check Firebase security rules
- Ensure `firebase_credentials.json` has write permissions

### "Migration shows 0 competitors"
- Verify `competition_data.json` exists and has data
- Check JSON file format

### Data not appearing in Firebase Console
- Wait 5-10 seconds for sync
- Refresh the Firestore page
- Check project ID matches credentials file

---

## Rollback to JSON

If you need to go back to local JSON:

1. **Stop all running applications**

2. **Remove Firebase credentials:**
   ```powershell
   move firebase_credentials.json firebase_credentials.json.backup
   ```

3. **Restart application**
   - System will use `competition_data.json` automatically

4. **Restore JSON data** (if needed):
   ```powershell
   copy competition_data_backup.json competition_data.json
   ```

---

## Best Practices

### During Migration:
1. ✅ Backup `competition_data.json` first
2. ✅ Test with sample data before migrating real competition
3. ✅ Verify migration in Firebase Console
4. ✅ Keep original JSON file as backup

### After Migration:
1. ✅ Close all competitor/judge/spectator windows
2. ✅ Restart from launcher to ensure Firebase connection
3. ✅ Test with one competitor before starting full competition
4. ✅ Monitor Firebase Console for successful writes

### During Competition:
1. ✅ Keep Firebase Console open to monitor
2. ✅ Have backup internet connection ready
3. ✅ Keep original JSON file as emergency fallback
4. ✅ Test all devices can connect before starting

---

## Performance Comparison

| Metric | JSON (Local) | Firebase |
|--------|-------------|----------|
| Write Speed | Instant | ~100-200ms |
| Read Speed | Instant | ~50-100ms |
| Multi-Device | No | Yes |
| Concurrent Users | 1 | Unlimited |
| Data Loss Risk | High (single file) | Low (cloud backup) |
| Network Required | No | Yes |

---

## FAQ

**Q: Can I run multiple competitions on the same Firebase project?**  
A: Yes, but you'll need to modify the code to use different collection names or create multiple Firebase projects.

**Q: What happens if internet drops during competition?**  
A: Writes will fail. Consider having a backup internet connection or fallback to JSON mode.

**Q: Can I use both JSON and Firebase simultaneously?**  
A: No, the system uses one backend at a time based on whether credentials exist.

**Q: How much does Firebase cost for a competition?**  
A: Free for typical competitions (within free tier limits).

**Q: Can competitors work offline?**  
A: No with Firebase. Use JSON mode for offline competitions.

---

## Support

- For Firebase setup issues: See `FIREBASE_SETUP.md`
- For application issues: See `README.md`
- For performance optimization: See `PERFORMANCE_OPTIMIZATIONS.md`

---

**Ready to migrate? Start with `FIREBASE_SETUP.md`!** 🚀
