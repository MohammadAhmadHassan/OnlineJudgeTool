# -*- coding: utf-8 -*-
"""
Firebase Configuration
Setup and credentials for Firebase Firestore connection
"""
import os
import json
from pathlib import Path
from typing import Optional

class FirebaseConfig:
    """Firebase configuration manager"""
    
    # Default configuration file name.
    CONFIG_FILE = "firebase_credentials.json"
    _last_source = None
    _last_error = None

    @staticmethod
    def _module_directory() -> Path:
        """Return directory that contains this module."""
        return Path(__file__).resolve().parent

    @staticmethod
    def _normalize_credentials(creds: Optional[dict]) -> Optional[dict]:
        """Normalize credential dict formatting (especially private key newlines)."""
        if not isinstance(creds, dict):
            return None

        normalized = dict(creds)
        private_key = normalized.get("private_key")
        if isinstance(private_key, str) and "\\n" in private_key and "\n" not in private_key:
            normalized["private_key"] = private_key.replace("\\n", "\n")

        return normalized

    @staticmethod
    def _looks_like_service_account(creds: Optional[dict]) -> bool:
        """Check whether credentials include required service-account keys."""
        if not isinstance(creds, dict):
            return False

        required_keys = ["project_id", "private_key", "client_email"]
        for key in required_keys:
            value = creds.get(key)
            if not isinstance(value, str) or not value.strip():
                return False
        return True

    @staticmethod
    def get_candidate_config_paths() -> list:
        """Return candidate credential paths in search order."""
        candidates = []

        env_specific = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        env_google = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        for item in [env_specific, env_google]:
            if item and str(item).strip():
                candidates.append(Path(item).expanduser())

        # Prefer repository-local file (next to this module), then CWD.
        candidates.append(FirebaseConfig._module_directory() / FirebaseConfig.CONFIG_FILE)
        candidates.append(Path.cwd() / FirebaseConfig.CONFIG_FILE)

        # De-duplicate while preserving order.
        deduped = []
        seen = set()
        for path_obj in candidates:
            try:
                key = str(path_obj.resolve()).lower()
            except Exception:
                key = str(path_obj).lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(str(path_obj))

        return deduped

    @staticmethod
    def get_last_source() -> Optional[str]:
        """Return the source used by the latest credential load attempt."""
        return FirebaseConfig._last_source

    @staticmethod
    def get_last_error() -> Optional[str]:
        """Return the latest credential load/validation error."""
        return FirebaseConfig._last_error

    @staticmethod
    def _load_from_streamlit_secrets() -> Optional[dict]:
        """Load credentials from Streamlit secrets when available."""
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "firebase" in st.secrets:
                creds = FirebaseConfig._normalize_credentials(dict(st.secrets["firebase"]))
                if FirebaseConfig._looks_like_service_account(creds):
                    FirebaseConfig._last_source = "streamlit_secrets.firebase"
                    return creds
                FirebaseConfig._last_error = (
                    "Streamlit secrets firebase block is present but missing required keys "
                    "(project_id/private_key/client_email)."
                )
        except Exception as exc:
            # Missing secrets.toml is expected in local runs; don't treat as an error.
            if "No secrets found" not in str(exc):
                FirebaseConfig._last_error = f"Failed reading Streamlit secrets: {exc}"
        return None
    
    @staticmethod
    def load_credentials() -> Optional[dict]:
        """
        Load Firebase credentials from JSON file or Streamlit secrets.
        
        Priority:
        1. Streamlit secrets (for cloud deployment)
        2. Local firebase_credentials.json file
        
        The credentials file should contain your Firebase service account key.
        Download it from: Firebase Console > Project Settings > Service Accounts > Generate New Private Key
        
        Expected format:
        {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "...",
            "private_key": "...",
            "client_email": "...",
            "client_id": "...",
            "auth_uri": "...",
            "token_uri": "...",
            "auth_provider_x509_cert_url": "...",
            "client_x509_cert_url": "..."
        }
        """
        FirebaseConfig._last_source = None
        FirebaseConfig._last_error = None

        # Try Streamlit secrets first (cloud/deployment).
        secrets_creds = FirebaseConfig._load_from_streamlit_secrets()
        if secrets_creds:
            return secrets_creds

        # Fall back to credential files from known paths.
        candidate_paths = FirebaseConfig.get_candidate_config_paths()
        last_file_error = None

        for path_str in candidate_paths:
            path_obj = Path(path_str)
            if not path_obj.exists():
                continue

            try:
                with open(path_obj, "r", encoding="utf-8") as f:
                    creds = FirebaseConfig._normalize_credentials(json.load(f))
                if FirebaseConfig._looks_like_service_account(creds):
                    FirebaseConfig._last_source = str(path_obj)
                    return creds
                last_file_error = (
                    f"Credential file found at {path_obj} but missing required keys "
                    "(project_id/private_key/client_email)."
                )
            except json.JSONDecodeError as exc:
                last_file_error = f"Invalid JSON in {path_obj}: {exc}"
            except Exception as exc:
                last_file_error = f"Failed to read {path_obj}: {exc}"

        if FirebaseConfig._last_error is None:
            if last_file_error:
                FirebaseConfig._last_error = last_file_error
            else:
                FirebaseConfig._last_error = (
                    "No Firebase credential source found. Checked Streamlit secrets and: "
                    + ", ".join(candidate_paths)
                )
        return None
    
    @staticmethod
    def get_database_url() -> str:
        """
        Get Firebase Realtime Database URL (if using Realtime DB instead of Firestore)
        Default uses Firestore, so this is optional.
        """
        creds = FirebaseConfig.load_credentials()
        if creds and 'project_id' in creds:
            return f"https://{creds['project_id']}.firebaseio.com/"
        return ""
    
    @staticmethod
    def is_configured() -> bool:
        """Check if Firebase is properly configured"""
        creds = FirebaseConfig.load_credentials()
        return FirebaseConfig._looks_like_service_account(creds)
    
    @staticmethod
    def create_sample_config():
        """Create a sample configuration file for users to fill in"""
        sample = {
            "_comment": "Replace this with your actual Firebase service account credentials",
            "_instructions": [
                "1. Go to Firebase Console (https://console.firebase.google.com/)",
                "2. Select your project or create a new one",
                "3. Go to Project Settings > Service Accounts",
                "4. Click 'Generate New Private Key'",
                "5. Download the JSON file and replace this file's content with it"
            ],
            "type": "service_account",
            "project_id": "your-project-id-here",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
            "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
        }
        
        default_path = FirebaseConfig._module_directory() / FirebaseConfig.CONFIG_FILE
        if not os.path.exists(default_path):
            with open(default_path, 'w', encoding='utf-8') as f:
                json.dump(sample, f, indent=2)
            return True
        return False
