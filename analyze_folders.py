#!/usr/bin/env python3
"""
Analyze Google Drive folder sizes by calculating total size of all files within
"""

import os
import pickle
from collections import defaultdict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Authenticate with Google Drive API"""
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
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_all_files(service):
    """Get all files from Google Drive with their folder hierarchy"""
    print("Fetching all files from Google Drive (this may take a while)...")
    
    all_files = []
    page_token = None
    
    while True:
        try:
            results = service.files().list(
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType, size, parents)",
                q="trashed=false",
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            all_files.extend(items)
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
            if len(all_files) % 1000 == 0:
                print(f"  Fetched {len(all_files)} files so far...")
                
        except HttpError as e:
            print(f"Error fetching files: {e}")
            break
    
    print(f"Total files fetched: {len(all_files)}")
    return all_files

def build_folder_tree(files):
    """Build a tree structure of folders and calculate sizes"""
    # Create dictionaries for quick lookups
    file_by_id = {f['id']: f for f in files}
    children_by_parent = defaultdict(list)
    
    # Build parent-child relationships
    for file in files:
        if 'parents' in file:
            for parent_id in file['parents']:
                children_by_parent[parent_id].append(file['id'])
    
    # Identify root-level items (parent is 'root' or no parent)
    root_items = []
    for file in files:
        if 'parents' not in file or not file['parents']:
            root_items.append(file)
        elif 'root' in file['parents']:
            root_items.append(file)
    
    return file_by_id, children_by_parent, root_items

def calculate_folder_size(folder_id, file_by_id, children_by_parent, visited=None):
    """Recursively calculate the total size of a folder"""
    if visited is None:
        visited = set()
    
    # Avoid infinite loops
    if folder_id in visited:
        return 0
    visited.add(folder_id)
    
    total_size = 0
    
    # Get all children of this folder
    for child_id in children_by_parent.get(folder_id, []):
        if child_id not in file_by_id:
            continue
            
        child = file_by_id[child_id]
        
        # If it's a file, add its size
        if 'size' in child:
            total_size += int(child['size'])
        
        # If it's a folder, recursively calculate its size
        if child.get('mimeType') == 'application/vnd.google-apps.folder':
            total_size += calculate_folder_size(child_id, file_by_id, children_by_parent, visited.copy())
    
    return total_size

def analyze_root_folders():
    """Analyze and display root folder sizes"""
    try:
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)
        
        # Get all files
        all_files = get_all_files(service)
        
        # Build folder tree
        file_by_id, children_by_parent, root_items = build_folder_tree(all_files)
        
        print("\nAnalyzing folder sizes...")
        
        # Calculate sizes for root folders
        folder_sizes = []
        
        for item in root_items:
            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                print(f"  Calculating size for: {item['name']}")
                size = calculate_folder_size(item['id'], file_by_id, children_by_parent)
                folder_sizes.append({
                    'name': item['name'],
                    'size': size,
                    'id': item['id']
                })
        
        # Also calculate size of files directly in root
        root_files_size = 0
        root_files_count = 0
        for item in root_items:
            if 'size' in item:  # It's a file, not a folder
                root_files_size += int(item['size'])
                root_files_count += 1
        
        # Sort folders by size
        folder_sizes.sort(key=lambda x: x['size'], reverse=True)
        
        # Display results
        print("\n" + "="*80)
        print("ROOT FOLDER SIZES (Sorted by Size)")
        print("="*80)
        
        total_size = root_files_size
        
        for i, folder in enumerate(folder_sizes[:30], 1):  # Show top 30
            size_str = format_size(folder['size'])
            total_size += folder['size']
            print(f"{i:2}. {size_str:>10} - {folder['name']}")
        
        if root_files_count > 0:
            print(f"\n    {format_size(root_files_size):>10} - Files directly in root ({root_files_count} files)")
        
        print("\n" + "-"*80)
        print(f"Total size in root folders and files: {format_size(total_size)}")
        print("="*80)
        
        # Show top 5 in detail
        print("\nTOP 5 LARGEST FOLDERS:")
        print("="*80)
        for i, folder in enumerate(folder_sizes[:5], 1):
            print(f"{i}. {folder['name']}")
            print(f"   Size: {format_size(folder['size'])}")
            print(f"   ID: {folder['id']}")
            print()
        
    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    analyze_root_folders()