# Firebase Security Guide

## ⚠️ IMPORTANT: Keeping Your Credentials Safe

Your `firebase_credentials.json` file contains sensitive information that should **NEVER** be committed to GitHub.

---

## ✅ What's Already Protected

Your `.gitignore` file already includes:
```
firebase_credentials.json
.streamlit/secrets.toml
```

This prevents these files from being committed.

---

## 🔧 Setup Instructions

### For Local Development

1. **Get your Firebase credentials:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project → Settings (⚙️) → Service Accounts
   - Click "Generate New Private Key"
   - Download the JSON file

2. **Add to your project:**
   - Rename the file to `firebase_credentials.json`
   - Place it in the project root (same folder as `streamlit_app.py`)
   - **DO NOT commit this file!**

3. **Use the template for documentation:**
   - `firebase_credentials.template.json` is safe to commit
   - It shows the structure without real credentials

### For Streamlit Cloud Deployment

**Do NOT upload `firebase_credentials.json` to GitHub!**

Instead, use Streamlit Cloud Secrets:

1. Deploy your app to Streamlit Cloud
2. Go to app settings → **Secrets**
3. Add your credentials in TOML format:

```toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour\nPrivate\nKey\nHere\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"
```

**Important:** Keep the `\n` characters in the private_key - they represent line breaks!

---

## 🛡️ Before Pushing to GitHub

**Always run these checks:**

```bash
# 1. Check what files will be committed
git status

# 2. Verify firebase_credentials.json is NOT listed
# If you see it, STOP! Don't commit!

# 3. Double-check .gitignore
cat .gitignore | grep firebase_credentials.json

# 4. Review your changes
git diff

# 5. Safe to push
git push
```

---

## 🆘 If You Accidentally Committed Credentials

### Before pushing:
```bash
# Remove from staging
git reset HEAD firebase_credentials.json

# Remove from last commit
git commit --amend
```

### After pushing (URGENT):

1. **Immediately** go to Firebase Console
2. Delete the compromised service account key
3. Generate a new key
4. Consider making the repo private or deleting it
5. Contact GitHub support to remove from cache

---

## 📚 Additional Resources

- [Streamlit Secrets Documentation](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Firebase Security Best Practices](https://firebase.google.com/docs/rules/get-started)
- See `DEPLOYMENT.md` for full deployment instructions
