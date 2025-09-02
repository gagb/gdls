"""
Core data structures and constants for gdls
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


# Constants
CACHE_TTL_SECONDS = 60 * 60  # 1 hour
API_PAGE_SIZE = 1000
DEFAULT_PORT = 8080
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CACHE_FILE = '.gdrive_cache.json'


# Custom Exceptions
class DriveError(Exception):
    """Base exception for Drive operations"""
    pass


class DriveAuthError(DriveError):
    """Authentication failed"""
    pass


class DrivePathNotFoundError(DriveError):
    """Path not found in Drive"""
    pass


class DriveCacheError(DriveError):
    """Cache operation failed"""
    pass


@dataclass
class ListOptions:
    """Configuration for file listing operations"""
    long_format: bool = False
    human_readable: bool = False
    show_hidden: bool = False
    recursive: bool = False
    sort_by: str = 'name'  # name, size, date, type
    reverse_sort: bool = False
    show_size: bool = False
    owned_only: bool = False
    show_ownership: bool = False
    
    def __post_init__(self):
        """Validate options after initialization"""
        valid_sorts = ['name', 'size', 'date', 'type']
        if self.sort_by not in valid_sorts:
            raise ValueError(f"Invalid sort_by: {self.sort_by}. Must be one of: {valid_sorts}")
    

@dataclass
class DriveItem:
    """Represents a file or folder in Google Drive"""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    modified_time: Optional[datetime] = None
    created_time: Optional[datetime] = None
    owners: Optional[List[dict]] = None
    owned_by_me: bool = True
    shared: bool = False
    web_view_link: Optional[str] = None
    calculated_size: Optional[int] = None
    
    def __post_init__(self):
        """Validate item after initialization"""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("DriveItem id must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("DriveItem name must be a non-empty string")
        if not isinstance(self.mime_type, str):
            raise ValueError("DriveItem mime_type must be a string")
    
    @property
    def is_folder(self) -> bool:
        return self.mime_type == 'application/vnd.google-apps.folder'
    
    @property
    def is_google_doc(self) -> bool:
        return 'google-apps' in self.mime_type
    
    @property
    def display_size(self) -> int:
        """Size to use for display (calculated size for folders, regular size for files)"""
        return self.calculated_size or self.size or 0


@dataclass 
class PathInfo:
    """Information about a resolved path"""
    id: str
    name: str
    path: str
    
    def __post_init__(self):
        """Validate path info after initialization"""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("PathInfo id must be a non-empty string")
        if not self.name or not isinstance(self.name, str):
            raise ValueError("PathInfo name must be a non-empty string") 
        if not isinstance(self.path, str):
            raise ValueError("PathInfo path must be a string")