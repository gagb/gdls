import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
            # Use fixed port 8080 to match redirect URI
            creds = flow.run_local_server(port=8080, host='localhost')
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def list_files():
    try:
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print('No files found.')
            return
        
        print(f'\nFound {len(items)} files:\n')
        print(f'{"Name":<50} {"Type":<30} {"Modified":<20}')
        print('-' * 100)
        
        for item in items:
            name = item['name'][:47] + '...' if len(item['name']) > 50 else item['name']
            mime = item.get('mimeType', 'Unknown')[:27] + '...' if len(item.get('mimeType', 'Unknown')) > 30 else item.get('mimeType', 'Unknown')
            modified = item.get('modifiedTime', 'Unknown')[:19]
            
            print(f'{name:<50} {mime:<30} {modified:<20}')
    
    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    list_files()