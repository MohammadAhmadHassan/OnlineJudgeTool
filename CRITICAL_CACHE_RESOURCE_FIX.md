# CRITICAL FIX: Remove @st.cache_resource from pages

## Root Cause Found!

The issue is in your Streamlit pages (e.g., `pages/1_👨‍💻_Competitor.py`):

```python
@st.cache_resource  # <-- THIS IS THE PROBLEM!
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()
```

**What's happening:**
1. `@st.cache_resource` creates a **global lock** across ALL users
2. When one user initializes Firebase slowly, ALL other users wait
3. This causes the infinite loading for "some users"

## THE FIX (Apply to ALL pages)

### Find this pattern in your pages:

**In these files:**
- `pages/1_👨‍💻_Competitor.py`
- `pages/2_👨‍⚖️_Judge.py`
- `pages/3_📊_Spectator.py`
- `streamlit_app.py` (if applicable)

**Change FROM:**
```python
@st.cache_resource
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()
```

**Change TO:**
```python
# Initialize data manager per session (not globally cached)
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = create_data_manager()

data_manager = st.session_state.data_manager
```

## Why This Works

### Before (BAD):
- `@st.cache_resource` = ONE data_manager for ALL users
- First user initializes → BLOCKS all other users
- Slow Firebase init → Everyone waits

### After (GOOD):
- Session state = ONE data_manager PER user
- Each user initializes independently
- Slow user doesn't affect others
- Background thread per user (non-blocking)

## Quick Apply

Run this in your terminal to find all occurrences:

```bash
# Find files using @st.cache_resource with data_manager
grep -r "@st.cache_resource" pages/
grep -r "get_data_manager" pages/
```

## Manual Fix for Each Page

### 1. Competitor Page (`pages/1_👨‍💻_Competitor.py`)

**Find (around line 106-110):**
```python
@st.cache_resource
def get_data_manager():
    return create_data_manager()

data_manager = get_data_manager()
```

**Replace with:**
```python
# Initialize data manager per session
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = create_data_manager()

data_manager = st.session_state.data_manager
```

### 2. Judge Page (`pages/2_👨‍⚖️_Judge.py`)

Same change as above.

### 3. Spectator Page (`pages/3_📊_Spectator.py`)

Same change as above.

### 4. Main App (`streamlit_app.py`)

If it exists there, same change.

## Test After Fix

1. Deploy changes
   ```bash
   git add pages/
   git commit -m "CRITICAL: Remove @st.cache_resource bottleneck"
   git push origin main
   ```

2. Open app in 5 different browser tabs simultaneously
3. All should load within 5-10 seconds
4. No more "some users" having issues

## Why @st.cache_resource Was There

It was probably added to:
- "Improve performance" (actually made it worse)
- "Reuse connection" (but Firebase is already a singleton)
- "Save memory" (but causes blocking)

**The Firebase connection is ALREADY shared via singleton pattern in `FirebaseDataManager`**, so caching at the Streamlit level just adds unnecessary locking.

## Expected Results

### Before:
- ❌ Random users get infinite loading
- ❌ First user slows down everyone
- ❌ Unpredictable behavior

### After:
- ✅ Each user loads independently
- ✅ Fast users don't wait for slow users
- ✅ Consistent experience for everyone

## Verification

After deploying, check Streamlit logs. You should see:
```
[Firebase] Starting background initialization... (multiple times - one per user)
[Firebase] ✅ Connection ready
```

Each user session initializes their own DataManager wrapper, but they all share the SAME Firebase singleton connection (which is correct and non-blocking).

---

**Priority:** CRITICAL  
**Effort:** 2 minutes per file  
**Impact:** Fixes "some users" infinite loading issue  
**Risk:** Very low (easy to revert)
