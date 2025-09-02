"""
Google Drive authentication handler
"""

import os
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .core import SCOPES, DEFAULT_PORT, DriveAuthError


class DriveAuth:
    """Handles Google Drive authentication with clean error handling"""
    
    def __init__(self, credentials_file: str = 'credentials.json', 
                 token_file: str = 'token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
    
    def get_service(self):
        """Get authenticated Google Drive service"""
        if self.service is None:
            self.service = self._authenticate()
        return self.service
    
    def _authenticate(self):
        """Authenticate and return Google Drive service"""
        try:
            creds = self._load_credentials()
            
            if not creds or not creds.valid:
                creds = self._refresh_or_create_credentials(creds)
                self._save_credentials(creds)
            
            return build('drive', 'v3', credentials=creds)
            
        except Exception as e:
            raise DriveAuthError(f"Authentication failed: {e}")
    
    def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file"""
        if not os.path.exists(self.token_file):
            return None
        
        try:
            with open(self.token_file, 'rb') as token:
                return pickle.load(token)
        except Exception as e:
            raise DriveAuthError(f"Failed to load token file: {e}")
    
    def _refresh_or_create_credentials(self, creds: Optional[Credentials]) -> Credentials:
        """Refresh existing credentials or create new ones"""
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return creds
            except Exception as e:
                raise DriveAuthError(f"Failed to refresh credentials: {e}")
        
        return self._create_new_credentials()
    
    def _create_new_credentials(self) -> Credentials:
        """Create new credentials through OAuth flow"""
        if not os.path.exists(self.credentials_file):
            raise DriveAuthError(f"Credentials file '{self.credentials_file}' not found")
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, 
                SCOPES,
                redirect_uri=f'http://localhost:{DEFAULT_PORT}/'
            )
            return flow.run_local_server(port=DEFAULT_PORT, host='localhost')
        except Exception as e:
            raise DriveAuthError(f"OAuth flow failed: {e}")
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file"""
        try:
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            raise DriveAuthError(f"Failed to save credentials: {e}")