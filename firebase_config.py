# -*- coding: utf-8 -*-
"""
Firebase Configuration
Setup and credentials for Firebase Firestore connection
"""
import os
import json
from typing import Optional

class FirebaseConfig:
    """Firebase configuration manager"""
    
    # Default configuration file path
    CONFIG_FILE = "firebase_credentials.json"
    
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
        # Try to load from Streamlit secrets first (for deployment)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                # Convert Streamlit secrets to dict
                return dict(st.secrets['firebase'])
        except:
            pass
        
        # Fall back to local file
        if not os.path.exists(FirebaseConfig.CONFIG_FILE):
            return None
        
        try:
            with open(FirebaseConfig.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
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
        return creds is not None and 'project_id' in creds
    
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
        
        if not os.path.exists(FirebaseConfig.CONFIG_FILE):
            with open(FirebaseConfig.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(sample, f, indent=2)
            return True
        return False
