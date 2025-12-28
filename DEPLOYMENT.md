# Deployment Guide - Separate Dashboards

## Overview
This guide explains how to deploy each dashboard (Competitor, Judge, Spectator) as separate apps on Streamlit Cloud.

## Option 1: Deploy to Three Separate Streamlit Cloud Apps (Recommended)

### Setup

1. **Create 3 separate GitHub repositories** (or use branches):
   - `competition-competitor` - For competitors only
   - `competition-judge` - For judges only
   - `competition-spectator` - For spectators only

2. **Or use the same repo with different entry points** (easier):
   - Deploy 3 separate Streamlit Cloud apps from the same repository
   - Each app uses a different main file

### Deployment Steps

#### Deploy Competitor App
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Repository: Your competition repo
4. Branch: main
5. **Main file path**: `streamlit_app_multi.py`
6. **Advanced settings** → Environment variables:
   - Add variable: `DASHBOARD_MODE` = `competitor`
7. App URL: Choose something like `competition-competitor`
8. Click "Deploy"

#### Deploy Judge App
1. Click "New app" again
2. Same repository
3. Branch: main
4. **Main file path**: `streamlit_app_multi.py`
5. **Advanced settings** → Environment variables:
   - Add variable: `DASHBOARD_MODE` = `judge`
6. App URL: Choose something like `competition-judge`
7. Click "Deploy"

#### Deploy Spectator App
1. Click "New app" again
2. Same repository
3. Branch: main
4. **Main file path**: `streamlit_app_multi.py`
5. **Advanced settings** → Environment variables:
   - Add variable: `DASHBOARD_MODE` = `spectator`
6. App URL: Choose something like `competition-spectator`
7. Click "Deploy"

### Result
You'll have three separate URLs:
- `https://competition-competitor.streamlit.app` - Competitor-only interface
- `https://competition-judge.streamlit.app` - Judge-only dashboard
- `https://competition-spectator.streamlit.app` - Spectator-only view

## Option 2: Use URL Parameters (Single Deployment)

If you prefer a single deployment with URL-based routing:

1. Rename `streamlit_app_multi.py` to `streamlit_app.py` (replace the current one)
2. Deploy once to Streamlit Cloud
3. Share different URLs with query parameters:
   - Competitors: `https://yourapp.streamlit.app/?mode=competitor`
   - Judges: `https://yourapp.streamlit.app/?mode=judge`
   - Spectators: `https://yourapp.streamlit.app/?mode=spectator`

**Note:** This option requires modifying the app to read URL parameters.

## Option 3: Password Protection (Add to any option above)

To add an extra layer of security, add password protection:

```python
# At the top of each page
import streamlit as st
import os

# Get password from environment variable
COMPETITOR_PASSWORD = os.environ.get('COMPETITOR_PASSWORD', '')
JUDGE_PASSWORD = os.environ.get('JUDGE_PASSWORD', '')

# For competitor page
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter access code:", type="password")
    if st.button("Submit"):
        if password == COMPETITOR_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid access code")
    st.stop()
```

Then set the passwords in Streamlit Cloud environment variables.

## Firebase Configuration for All Deployments

### Important: All three apps need Firebase credentials

1. In Streamlit Cloud, go to **Advanced settings** for each app
2. Add your Firebase credentials as **Secrets**:

```toml
# .streamlit/secrets.toml format
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-client-email"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
```

3. Update `firebase_config.py` to read from Streamlit secrets if available

## Recommended Approach

**For maximum security and separation:**
1. Use **Option 1** (three separate deployments with environment variables)
2. Add **password protection** (Option 3)
3. Share specific URLs only with the appropriate users:
   - Competitors get only the competitor URL + password
   - Judges get only the judge URL + password
   - Spectators get only the spectator URL (no password needed)

## Testing Locally

Test each mode locally before deploying:

```bash
# Test competitor mode
set DASHBOARD_MODE=competitor
streamlit run streamlit_app_multi.py

# Test judge mode
set DASHBOARD_MODE=judge
streamlit run streamlit_app_multi.py

# Test spectator mode
set DASHBOARD_MODE=spectator
streamlit run streamlit_app_multi.py

# Test all modes (default)
set DASHBOARD_MODE=all
streamlit run streamlit_app_multi.py
```

On Linux/Mac, use `export` instead of `set`.

## Next Steps

1. Choose your deployment option
2. Update Firebase configuration to use Streamlit secrets
3. Deploy to Streamlit Cloud
4. Test each deployment
5. Share URLs with appropriate users
