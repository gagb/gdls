#!/usr/bin/env python3
"""
Google Drive ls command - Unix-like ls for Google Drive
"""

import os
import sys
import pickle
import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CACHE_FILE = '.gdrive_cache.json'

class GDriveLs:
    def __init__(self):
        self.service = None
        self.cache = self._load_cache()
        self._authenticate()
    
    def _authenticate(self):
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
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def _load_cache(self) -> Dict:
        """Load path cache from file"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'paths': {}}
    
    def _save_cache(self):
        """Save path cache to file"""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)
    
    def _resolve_path(self, path: str) -> Tuple[str, str]:
        """
        Resolve a path like /folder1/folder2 to a folder ID
        Returns (folder_id, folder_name)
        """
        if path == '/' or path == '':
            return ('root', 'My Drive')
        
        # Check cache first
        if path in self.cache['paths']:
            return self.cache['paths'][path]
        
        # Parse path components
        parts = [p for p in path.strip('/').split('/') if p]
        current_id = 'root'
        current_name = 'My Drive'
        
        for part in parts:
            # Search for folder with this name in current folder
            query = f"'{current_id}' in parents and name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            try:
                results = self.service.files().list(
                    q=query,
                    fields="files(id, name)",
                    pageSize=1
                ).execute()
                
                items = results.get('files', [])
                if not items:
                    raise ValueError(f"Folder '{part}' not found in path '{path}'")
                
                current_id = items[0]['id']
                current_name = items[0]['name']
            except HttpError as e:
                raise ValueError(f"Error resolving path '{path}': {e}")
        
        # Cache the result
        self.cache['paths'][path] = (current_id, current_name)
        self._save_cache()
        
        return (current_id, current_name)
    
    def _format_size(self, size_bytes: Optional[str]) -> str:
        """Format file size in human-readable format"""
        if size_bytes is None:
            return '-'
        
        size = int(size_bytes)
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{size:4d}{unit}"
                return f"{size:4.0f}{unit}"
            size /= 1024.0
        return f"{size:.0f}P"
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date for display"""
        if not date_str:
            return '-'
        
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(date.tzinfo)
            
            # If within last 6 months, show month day time
            # Otherwise show month day year
            diff_days = (now - date).days
            
            if diff_days < 180:
                return date.strftime('%b %d %H:%M')
            else:
                return date.strftime('%b %d  %Y')
        except:
            return date_str[:10] if date_str else '-'
    
    def _get_file_type_char(self, mime_type: str) -> str:
        """Get single character representing file type"""
        if mime_type == 'application/vnd.google-apps.folder':
            return 'd'
        elif 'google-apps' in mime_type:
            return 'g'  # Google Docs/Sheets/etc
        else:
            return '-'  # Regular file
    
    def list_files(self, path: str = '/', 
                   long_format: bool = False,
                   human_readable: bool = False,
                   show_hidden: bool = False,
                   recursive: bool = False,
                   sort_by: str = 'name',
                   reverse_sort: bool = False) -> List[Dict]:
        """
        List files in a Google Drive folder
        
        Args:
            path: Path to list (e.g., '/' or '/Documents')
            long_format: Show detailed information
            human_readable: Show sizes in human-readable format
            show_hidden: Show trashed files
            recursive: List subdirectories recursively
            sort_by: Sort by 'name', 'size', 'date', or 'type'
            reverse_sort: Reverse sort order
        
        Returns:
            List of file/folder information dictionaries
        """
        try:
            folder_id, folder_name = self._resolve_path(path)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return []
        
        # Build query
        query_parts = [f"'{folder_id}' in parents"]
        if not show_hidden:
            query_parts.append("trashed=false")
        query = " and ".join(query_parts)
        
        # Fetch files
        all_items = []
        page_token = None
        
        while True:
            try:
                results = self.service.files().list(
                    q=query,
                    pageSize=1000,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, owners, webViewLink)",
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                all_items.extend(items)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            except HttpError as e:
                print(f"Error listing files: {e}", file=sys.stderr)
                return []
        
        # Sort items
        if sort_by == 'size':
            all_items.sort(key=lambda x: int(x.get('size', '0')), reverse=True)
        elif sort_by == 'date':
            all_items.sort(key=lambda x: x.get('modifiedTime', ''), reverse=True)
        elif sort_by == 'type':
            all_items.sort(key=lambda x: (x.get('mimeType', ''), x.get('name', '')))
        else:  # name
            all_items.sort(key=lambda x: x.get('name', '').lower())
        
        if reverse_sort:
            all_items.reverse()
        
        return all_items
    
    def display_items(self, items: List[Dict], 
                     long_format: bool = False,
                     human_readable: bool = False,
                     path: str = '/'):
        """Display items in requested format"""
        
        if not items:
            return
        
        if long_format:
            # Calculate total size
            total_size = sum(int(item.get('size', '0')) for item in items)
            print(f"total {self._format_size(str(total_size)) if human_readable else total_size}")
            
            # Display each item
            for item in items:
                file_type = self._get_file_type_char(item.get('mimeType', ''))
                size = self._format_size(item.get('size')) if human_readable else item.get('size', '-')
                date = self._format_date(item.get('modifiedTime'))
                name = item['name']
                
                # Add folder indicator
                if file_type == 'd':
                    name = f"\033[34m{name}/\033[0m"  # Blue color for folders
                elif file_type == 'g':
                    name = f"\033[32m{name}\033[0m"  # Green for Google Docs
                
                # Format: type permissions links owner size date name
                print(f"{file_type}rw-r--r-- 1 {item.get('owners', [{}])[0].get('displayName', 'unknown')[:8]:8} {size:>8} {date} {name}")
        else:
            # Simple format - just names
            for item in items:
                name = item['name']
                if item.get('mimeType') == 'application/vnd.google-apps.folder':
                    name = f"\033[34m{name}/\033[0m"
                elif 'google-apps' in item.get('mimeType', ''):
                    name = f"\033[32m{name}\033[0m"
                print(name)
    
    def recursive_list(self, path: str = '/', prefix: str = '', **kwargs):
        """Recursively list directories"""
        items = self.list_files(path, **kwargs)
        
        # Display current directory
        if prefix:
            print(f"\n{prefix}:")
        else:
            print(f"{path}:")
        
        self.display_items(items, **kwargs)
        
        # Find subdirectories and recurse
        folders = [item for item in items 
                  if item.get('mimeType') == 'application/vnd.google-apps.folder']
        
        for folder in folders:
            folder_path = path.rstrip('/') + '/' + folder['name']
            self.recursive_list(folder_path, folder_path, **kwargs)


def main():
    parser = argparse.ArgumentParser(
        description='List Google Drive files and folders (Unix ls-like interface)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # List root directory
  %(prog)s /Documents           # List Documents folder
  %(prog)s -lH /                # Long format with human-readable sizes
  %(prog)s -R /Photos           # Recursive listing
  %(prog)s --sort=size /        # Sort by file size
        """
    )
    
    parser.add_argument('path', nargs='?', default='/',
                       help='Path to list (default: /)')
    parser.add_argument('-l', '--long', action='store_true',
                       help='Use long listing format')
    parser.add_argument('-H', '--human-readable', action='store_true',
                       help='Print sizes in human readable format (e.g., 1K, 234M, 2G)')
    parser.add_argument('-a', '--all', action='store_true',
                       help='Show all files including trashed')
    parser.add_argument('-R', '--recursive', action='store_true',
                       help='List subdirectories recursively')
    parser.add_argument('-r', '--reverse', action='store_true',
                       help='Reverse order while sorting')
    parser.add_argument('--sort', choices=['name', 'size', 'date', 'type'],
                       default='name',
                       help='Sort by attribute (default: name)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Clear cache before running')
    
    args = parser.parse_args()
    
    # Clear cache if requested
    if args.no_cache and os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    
    # Create GDrive ls instance
    try:
        gdrive = GDriveLs()
    except Exception as e:
        print(f"Error initializing Google Drive connection: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Perform listing
    if args.recursive:
        gdrive.recursive_list(
            args.path,
            long_format=args.long,
            human_readable=args.human_readable,
            show_hidden=args.all,
            sort_by=args.sort,
            reverse_sort=args.reverse
        )
    else:
        items = gdrive.list_files(
            args.path,
            long_format=args.long,
            human_readable=args.human_readable,
            show_hidden=args.all,
            sort_by=args.sort,
            reverse_sort=args.reverse
        )
        
        if items:
            gdrive.display_items(
                items,
                long_format=args.long,
                human_readable=args.human_readable,
                path=args.path
            )
        else:
            print(f"No files found in {args.path}")


if __name__ == '__main__':
    main()