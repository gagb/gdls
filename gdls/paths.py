"""
Google Drive path resolution
"""

from googleapiclient.errors import HttpError

from .core import DrivePathNotFoundError, PathInfo


class PathResolver:
    """Resolves Google Drive paths to folder IDs"""
    
    def __init__(self, service, cache):
        self.service = service
        self.cache = cache
    
    def resolve(self, path: str) -> PathInfo:
        """
        Resolve a path like /folder1/folder2 to folder information
        
        Args:
            path: Path to resolve (e.g., '/' or '/Documents')
            
        Returns:
            PathInfo with id, name, and path
            
        Raises:
            DrivePathNotFoundError: If path doesn't exist
        """
        if not isinstance(path, str):
            raise ValueError("Path must be a string")
        if not path:
            path = '/'
        if not path or path == '/':
            return PathInfo(id='root', name='My Drive', path='/')
        
        # Check cache first
        cached = self.cache.get_path(path)
        if cached:
            return cached
        
        # Parse and resolve path components
        path_info = self._resolve_path_components(path)
        
        # Cache the result
        self.cache.set_path(path, path_info)
        
        return path_info
    
    def _resolve_path_components(self, path: str) -> PathInfo:
        """Resolve path by walking through each component"""
        parts = [p for p in path.strip('/').split('/') if p]
        current_id = 'root'
        current_name = 'My Drive'
        
        for part in parts:
            try:
                current_id, current_name = self._find_folder_in_parent(current_id, part)
            except DrivePathNotFoundError:
                raise DrivePathNotFoundError(f"Folder '{part}' not found in path '{path}'")
        
        return PathInfo(id=current_id, name=current_name, path=path)
    
    def _find_folder_in_parent(self, parent_id: str, folder_name: str) -> tuple[str, str]:
        """Find a folder by name within a parent folder"""
        query = (
            f"'{parent_id}' in parents and "
            f"name='{folder_name}' and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )
        
        try:
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=1
            ).execute()
            
            items = results.get('files', [])
            if not items:
                raise DrivePathNotFoundError(f"Folder '{folder_name}' not found")
            
            return items[0]['id'], items[0]['name']
            
        except HttpError as e:
            raise DrivePathNotFoundError(f"Error accessing folder '{folder_name}': {e}")