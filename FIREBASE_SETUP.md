# Firebase Setup Guide

## Overview
The competition system now supports **Firebase Firestore** for multi-device synchronization. This allows competitors, judges, and spectators to use the system on different devices with real-time data synchronization.

## What is Firebase?
Firebase is Google's cloud platform that provides a NoSQL database (Firestore) with real-time synchronization. It's free for small-scale usage and perfect for competition systems.

---

## Setup Instructions

### Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or select an existing project
3. Enter a project name (e.g., "Python-Competition")
4. Disable Google Analytics (optional for this use case)
5. Click **"Create project"**

### Step 2: Enable Firestore Database

1. In the Firebase Console, go to **"Build" > "Firestore Database"**
2. Click **"Create database"**
3. Choose **"Start in production mode"** (we'll set rules later)
4. Select a database location (choose closest to your region)
5. Click **"Enable"**

### Step 3: Set Security Rules (Important!)

1. In Firestore, go to the **"Rules"** tab
2. Replace the default rules with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write to all authenticated users
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

⚠️ **Note**: This allows public access. For production, implement proper authentication!

3. Click **"Publish"**

### Step 4: Generate Service Account Credentials

1. In Firebase Console, click the **⚙️ gear icon** > **"Project settings"**
2. Go to the **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Click **"Generate key"** in the confirmation dialog
5. A JSON file will be downloaded - **keep this secure!**

### Step 5: Configure Your Application

1. Rename the downloaded JSON file to: `firebase_credentials.json`
2. Move it to the project folder: `c:\Users\VOIS\Downloads\problemSolvingTool\`
3. The file should be in the same directory as `launcher.py`

**File structure should look like:**
```
problemSolvingTool/
├── firebase_credentials.json  ← Your credentials file here
├── launcher.py
├── competitor_interface.py
├── judge_dashboard.py
├── spectator_dashboard.py
├── firebase_config.py
├── firebase_data_manager.py
├── data_manager.py
└── ...
```

### Step 6: Install Firebase SDK

Open PowerShell in the project folder and run:

```powershell
pip install firebase-admin
```

Or install all dependencies:

```powershell
pip install -r requirements.txt
```

### Step 7: Test the Connection

1. Run the launcher:
   ```powershell
   python launcher.py
   ```

2. Check the console output:
   - ✅ If you see: `"✓ Connected to Firebase Firestore"` → Success!
   - ⚠️ If you see: `"ℹ Firebase not configured, using local JSON storage"` → Check steps 5-6

---

## Verification

To verify Firebase is working:

1. Launch the **Competitor** interface
2. Register a competitor
3. Open Firebase Console > Firestore Database
4. You should see a new collection called `competitors` with your data

---

## Troubleshooting

### Error: "Firebase credentials not found"
**Solution**: Make sure `firebase_credentials.json` is in the correct folder and properly named.

### Error: "Permission denied"
**Solution**: Check Firestore security rules (Step 3). Make sure you set them to allow read/write.

### Error: "Module 'firebase_admin' not found"
**Solution**: Install Firebase SDK:
```powershell
pip install firebase-admin
```

### Connection Slow or Timing Out
**Solution**: 
- Check your internet connection
- Verify Firestore region is accessible
- Try restarting the application

### Data Not Syncing Between Devices
**Solution**:
- Ensure all devices use the same `firebase_credentials.json` file
- Check that all devices have internet access
- Verify Firestore rules allow read/write

---

## Firestore Data Structure

The competition system uses the following Firestore structure:

```
📁 competitors/
  └─ 📄 [competitor_name]/
      ├── name: string
      ├── joined_at: string (ISO datetime)
      ├── current_problem: number
      ├── last_activity: string (ISO datetime)
      └── problems: map
          └── [problem_id]: map
              ├── submissions: array
              └── best_result: map

📁 competition/
  └─ 📄 metadata/
      ├── competition_started: boolean
      ├── start_time: string (ISO datetime)
      └── problems_loaded: array

📁 problems/
  └─ (Optional - for storing problem definitions)
```

---

## Fallback Mode (Local JSON)

If Firebase is not configured, the system automatically falls back to local JSON storage:
- File: `competition_data.json`
- Works offline
- Single device only (no synchronization)

To switch back to local mode, simply remove or rename `firebase_credentials.json`.

---

## Security Best Practices

### For Testing/Development:
✅ Use the open rules shown in Step 3

### For Production Competitions:
1. **Enable Firebase Authentication**
   - Add email/password or anonymous auth
   - Update security rules to require authentication

2. **Restrict Write Access**
   ```
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /competitors/{competitorId} {
         allow read: if true;
         allow write: if request.auth != null;
       }
       match /competition/{document} {
         allow read: if true;
         allow write: if request.auth.token.admin == true;
       }
     }
   }
   ```

3. **Use Environment Variables**
   - Don't commit `firebase_credentials.json` to version control
   - Add it to `.gitignore`

---

## Cost Considerations

**Firebase Free Tier (Spark Plan):**
- 1 GB storage
- 50,000 reads/day
- 20,000 writes/day
- 20,000 deletes/day

This is **more than enough** for typical competitions with:
- Up to 50 competitors
- 10 problems
- Running for several hours

**Estimate for a 3-hour competition:**
- ~5,000 reads (leaderboard refreshes)
- ~500 writes (submissions)
- **Total cost: $0** (within free tier)

---

## Additional Features with Firebase

### Real-Time Updates (Future Enhancement)
Firebase supports real-time listeners. You can add this to auto-refresh dashboards:

```python
# Example: Auto-update leaderboard
def on_snapshot(snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED' or change.type.name == 'MODIFIED':
            self.refresh_data()

# Add listener
data_manager.add_listener(on_snapshot)
```

### Multi-Region Support
- Deploy from anywhere
- Competitors can join from different locations
- Cloud-based = no port forwarding needed

---

## Support

For Firebase-specific issues:
- [Firebase Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Support](https://firebase.google.com/support)

For application issues:
- Check `TROUBLESHOOTING.md`
- Review console output for error messages
- Ensure all dependencies are installed

---

## Quick Start Checklist

- [ ] Create Firebase project
- [ ] Enable Firestore Database
- [ ] Set security rules to allow read/write
- [ ] Generate service account key
- [ ] Save as `firebase_credentials.json` in project folder
- [ ] Install Firebase SDK: `pip install firebase-admin`
- [ ] Run `python launcher.py`
- [ ] Verify: "✓ Connected to Firebase Firestore" appears

---

**That's it!** Your competition system is now configured for multi-device use with real-time synchronization. 🎉
