#!/usr/bin/env python3
"""Check ownership of folders"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES,
                redirect_uri='http://localhost:8080/')
            creds = flow.run_local_server(port=8080, host='localhost')
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def check_folder(service, folder_name):
    """Check folder details including ownership"""
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name, owners, shared, ownedByMe, sharingUser, permissions)",
        pageSize=10
    ).execute()
    
    items = results.get('files', [])
    
    for item in items:
        print(f"\nFolder: {item['name']}")
        print(f"  ID: {item['id']}")
        print(f"  Owned by me: {item.get('ownedByMe', False)}")
        print(f"  Shared: {item.get('shared', False)}")
        
        if 'owners' in item:
            for owner in item['owners']:
                print(f"  Owner: {owner.get('displayName', 'Unknown')} ({owner.get('emailAddress', 'Unknown')})")
        
        if 'sharingUser' in item:
            user = item['sharingUser']
            print(f"  Shared by: {user.get('displayName', 'Unknown')} ({user.get('emailAddress', 'Unknown')})")

try:
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    # Check the big folders
    folders = ["Wedding 2024", "2024 Kimberly & Bryan Wedding Reception", "Eric BBQ", "Perseid 2023", "Gagan Photo Shoot"]
    
    for folder in folders:
        check_folder(service, folder)
        
except Exception as e:
    print(f"Error: {e}")
