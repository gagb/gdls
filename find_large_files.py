import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

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

def format_size(size_bytes):
    if size_bytes is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def find_large_files(min_size_mb=10):
    try:
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)
        
        all_files = []
        page_token = None
        total_size = 0
        
        print(f"Fetching all files from Google Drive (this may take a while)...")
        
        while True:
            results = service.files().list(
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, parents, webViewLink)",
                pageToken=page_token,
                q="trashed=false"
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                size = item.get('size')
                if size:
                    size = int(size)
                    total_size += size
                    item['size_int'] = size
                    all_files.append(item)
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
            print(f"  Fetched {len(all_files)} files so far...")
        
        print(f"\n{'='*100}")
        print(f"GOOGLE DRIVE STORAGE ANALYSIS")
        print(f"{'='*100}")
        print(f"Total files with size info: {len(all_files)}")
        print(f"Total storage used: {format_size(total_size)}")
        print(f"{'='*100}\n")
        
        # Sort by size (largest first)
        all_files.sort(key=lambda x: x['size_int'], reverse=True)
        
        # Filter by minimum size
        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = [f for f in all_files if f['size_int'] >= min_size_bytes]
        
        print(f"FILES LARGER THAN {min_size_mb} MB (sorted by size):")
        print(f"{'='*100}")
        print(f"{'Size':<15} {'Modified':<20} {'Type':<30} {'Name':<50}")
        print(f"{'-'*115}")
        
        cumulative_size = 0
        for i, item in enumerate(large_files[:100], 1):
            size = item['size_int']
            cumulative_size += size
            name = item['name'][:47] + '...' if len(item['name']) > 50 else item['name']
            mime = item.get('mimeType', 'Unknown')[:27] + '...' if len(item.get('mimeType', 'Unknown')) > 30 else item.get('mimeType', 'Unknown')
            modified = item.get('modifiedTime', 'Unknown')[:19] if item.get('modifiedTime') else 'Unknown'
            
            print(f"{format_size(size):<15} {modified:<20} {mime:<30} {name:<50}")
            
            if i % 10 == 0:
                print(f"  --> Cumulative size of top {i} files: {format_size(cumulative_size)}")
                print()
        
        print(f"\n{'='*100}")
        print(f"STORAGE BREAKDOWN BY FILE TYPE:")
        print(f"{'='*100}")
        
        # Group by mime type
        type_sizes = {}
        type_counts = {}
        for item in all_files:
            mime = item.get('mimeType', 'Unknown')
            size = item['size_int']
            
            # Simplify mime types
            if 'video' in mime:
                simple_type = 'Videos'
            elif 'image' in mime:
                simple_type = 'Images'
            elif 'pdf' in mime:
                simple_type = 'PDFs'
            elif 'google-apps' in mime:
                simple_type = 'Google Docs/Sheets/Slides'
            elif 'zip' in mime or 'compressed' in mime:
                simple_type = 'Archives (ZIP, etc.)'
            elif 'audio' in mime:
                simple_type = 'Audio'
            else:
                simple_type = mime.split('/')[-1] if '/' in mime else mime
            
            type_sizes[simple_type] = type_sizes.get(simple_type, 0) + size
            type_counts[simple_type] = type_counts.get(simple_type, 0) + 1
        
        # Sort by total size
        sorted_types = sorted(type_sizes.items(), key=lambda x: x[1], reverse=True)
        
        for file_type, total_size in sorted_types[:15]:
            count = type_counts[file_type]
            avg_size = total_size / count if count > 0 else 0
            percentage = (total_size / total_size) * 100 if total_size > 0 else 0
            print(f"{file_type:<30} {format_size(total_size):<15} ({count} files, avg: {format_size(avg_size)})")
        
        print(f"\n{'='*100}")
        print(f"TOP 20 LARGEST FILES:")
        print(f"{'='*100}")
        
        for i, item in enumerate(all_files[:20], 1):
            size = item['size_int']
            print(f"{i:2}. {format_size(size):<12} - {item['name']}")
            if item.get('webViewLink'):
                print(f"    Link: {item['webViewLink']}")
    
    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    find_large_files(min_size_mb=50)  # Show files larger than 50MB