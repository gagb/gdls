"""
Google Drive file exploration and operations
"""

from datetime import datetime
from typing import List

from googleapiclient.errors import HttpError

from .core import API_PAGE_SIZE, DriveError, DriveItem, ListOptions


class DriveExplorer:
    """Handles file listing and size calculations"""
    
    def __init__(self, service, cache):
        self.service = service
        self.cache = cache
    
    def list_files(self, folder_id: str, options: ListOptions) -> List[DriveItem]:
        """
        List files in a folder with the given options
        
        Args:
            folder_id: Google Drive folder ID to list
            options: Configuration for the listing operation
            
        Returns:
            List of DriveItem objects
        """
        if not isinstance(folder_id, str) or not folder_id:
            raise ValueError("folder_id must be a non-empty string")
        if not isinstance(options, ListOptions):
            raise ValueError("options must be a ListOptions instance")
        items = self._fetch_items(folder_id, options)
        
        if options.owned_only:
            items = [item for item in items if item.owned_by_me]
        
        if options.show_size:
            self._calculate_folder_sizes(items)
        
        return self._sort_items(items, options)
    
    def calculate_folder_size(self, folder_id: str) -> int:
        """Calculate total size of all files in a folder recursively"""
        if not isinstance(folder_id, str) or not folder_id:
            raise ValueError("folder_id must be a non-empty string")
        # Check cache first
        cached_size = self.cache.get_folder_size(folder_id)
        if cached_size is not None:
            return cached_size
        
        total_size = self._recursive_folder_size(folder_id, set())
        
        # Cache the result
        self.cache.set_folder_size(folder_id, total_size)
        
        return total_size
    
    def _fetch_items(self, folder_id: str, options: ListOptions) -> List[DriveItem]:
        """Fetch items from Google Drive API"""
        query_parts = [f"'{folder_id}' in parents"]
        
        if not options.show_hidden:
            query_parts.append("trashed=false")
        
        query = " and ".join(query_parts)
        
        all_items = []
        page_token = None
        
        while True:
            try:
                results = self.service.files().list(
                    q=query,
                    pageSize=API_PAGE_SIZE,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, owners, webViewLink, ownedByMe, shared)",
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                all_items.extend(self._convert_to_drive_items(items))
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as e:
                raise DriveError(f"Failed to list files: {e}")
        
        return all_items
    
    def _convert_to_drive_items(self, api_items: List[dict]) -> List[DriveItem]:
        """Convert API response items to DriveItem objects"""
        drive_items = []
        
        for item in api_items:
            drive_item = DriveItem(
                id=item['id'],
                name=item['name'],
                mime_type=item.get('mimeType', ''),
                size=int(item['size']) if item.get('size') else None,
                modified_time=self._parse_datetime(item.get('modifiedTime')),
                created_time=self._parse_datetime(item.get('createdTime')),
                owners=item.get('owners', []),
                owned_by_me=item.get('ownedByMe', True),
                shared=item.get('shared', False),
                web_view_link=item.get('webViewLink')
            )
            drive_items.append(drive_item)
        
        return drive_items
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string from API"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _calculate_folder_sizes(self, items: List[DriveItem]):
        """Calculate sizes for all folders in the list"""
        for item in items:
            if item.is_folder:
                if item.owned_by_me:
                    item.calculated_size = self.calculate_folder_size(item.id)
                else:
                    # Shared folders don't count against quota
                    item.calculated_size = 0
    
    def _recursive_folder_size(self, folder_id: str, visited: set) -> int:
        """Recursively calculate folder size, avoiding infinite loops"""
        if folder_id in visited:
            return 0
        
        visited.add(folder_id)
        total_size = 0
        page_token = None
        
        while True:
            try:
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    pageSize=API_PAGE_SIZE,
                    fields="nextPageToken, files(id, mimeType, size)",
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    if 'size' in item:
                        total_size += int(item['size'])
                    elif item.get('mimeType') == 'application/vnd.google-apps.folder':
                        total_size += self._recursive_folder_size(item['id'], visited.copy())
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError:
                break
        
        return total_size
    
    def _sort_items(self, items: List[DriveItem], options: ListOptions) -> List[DriveItem]:
        """Sort items according to options"""
        if options.sort_by == 'size':
            items.sort(key=lambda x: x.display_size, reverse=True)
        elif options.sort_by == 'date':
            items.sort(key=lambda x: x.modified_time or datetime.min, reverse=True)
        elif options.sort_by == 'type':
            items.sort(key=lambda x: (x.mime_type, x.name.lower()))
        else:  # name
            items.sort(key=lambda x: x.name.lower())
        
        if options.reverse_sort:
            items.reverse()
        
        return items