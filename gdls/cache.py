"""
Caching system for Google Drive operations
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

from .core import CACHE_FILE, CACHE_TTL_SECONDS, DriveCacheError, PathInfo


class DriveCache:
    """Handles caching for Google Drive operations"""
    
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self._cache_data = self._load_cache()
    
    def get_path(self, path: str) -> Optional[PathInfo]:
        """Get cached path information"""
        if 'paths' not in self._cache_data:
            return None
            
        cached = self._cache_data['paths'].get(path)
        if not cached:
            return None
            
        return PathInfo(
            id=cached['id'],
            name=cached['name'], 
            path=path
        )
    
    def set_path(self, path: str, path_info: PathInfo):
        """Cache path information"""
        if 'paths' not in self._cache_data:
            self._cache_data['paths'] = {}
            
        self._cache_data['paths'][path] = {
            'id': path_info.id,
            'name': path_info.name,
            'timestamp': datetime.now().timestamp()
        }
        self._save_cache()
    
    def get_folder_size(self, folder_id: str) -> Optional[int]:
        """Get cached folder size"""
        if 'folder_sizes' not in self._cache_data:
            return None
            
        cache_key = f"size_{folder_id}"
        cached = self._cache_data['folder_sizes'].get(cache_key)
        
        if not cached:
            return None
            
        # Check if cache is still valid
        age = datetime.now().timestamp() - cached.get('timestamp', 0)
        if age > CACHE_TTL_SECONDS:
            return None
            
        return cached.get('size')
    
    def set_folder_size(self, folder_id: str, size: int):
        """Cache folder size"""
        if 'folder_sizes' not in self._cache_data:
            self._cache_data['folder_sizes'] = {}
            
        cache_key = f"size_{folder_id}"
        self._cache_data['folder_sizes'][cache_key] = {
            'size': size,
            'timestamp': datetime.now().timestamp()
        }
        self._save_cache()
    
    def clear(self):
        """Clear all cache data"""
        self._cache_data = {'paths': {}, 'folder_sizes': {}}
        self._save_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from file"""
        if not os.path.exists(self.cache_file):
            return {'paths': {}, 'folder_sizes': {}}
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                # Ensure required keys exist
                if 'paths' not in data:
                    data['paths'] = {}
                if 'folder_sizes' not in data:
                    data['folder_sizes'] = {}
                return data
        except (json.JSONDecodeError, IOError) as e:
            # If cache is corrupted, start fresh
            return {'paths': {}, 'folder_sizes': {}}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache_data, f)
        except IOError as e:
            raise DriveCacheError(f"Failed to save cache: {e}")