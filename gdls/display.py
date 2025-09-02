"""
Display formatting for Google Drive listings
"""

from typing import List

from .core import DriveItem, ListOptions


class DisplayFormatter:
    """Handles formatting and display of drive items"""
    
    def format_items(self, items: List[DriveItem], options: ListOptions):
        """Format and display items according to options"""
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        if not isinstance(options, ListOptions):
            raise ValueError("options must be a ListOptions instance")
        if not items:
            return
        
        if options.long_format:
            self._display_long_format(items, options)
        else:
            self._display_simple_format(items)
    
    def _display_long_format(self, items: List[DriveItem], options: ListOptions):
        """Display items in long format (ls -l style)"""
        # Calculate and display total size
        total_size = sum(item.display_size for item in items)
        size_display = self._format_size(total_size) if options.human_readable else str(total_size)
        print(f"total {size_display}")
        
        # Display each item
        for item in items:
            file_type = self._get_file_type_char(item.mime_type)
            size = self._format_size(item.display_size) if options.human_readable else str(item.display_size or 0)
            date = self._format_date(item.modified_time)
            name = self._format_name(item)
            
            # Get owner info
            owner_name = self._get_owner_name(item, options.show_ownership)
            
            print(f"{file_type}rw-r--r-- 1 {owner_name:8} {size:>8} {date} {name}")
    
    def _display_simple_format(self, items: List[DriveItem]):
        """Display items in simple format (just names)"""
        for item in items:
            name = self._format_name(item)
            print(name)
    
    def _format_name(self, item: DriveItem) -> str:
        """Format item name with color coding and indicators"""
        name = item.name
        
        # Add folder indicator and color
        if item.is_folder:
            name = f"\033[34m{name}/\033[0m"  # Blue
        elif item.is_google_doc:
            name = f"\033[32m{name}\033[0m"  # Green
        
        # Add sharing indicator
        if not item.owned_by_me and item.shared:
            name = f"\033[93m{name} [shared]\033[0m"  # Yellow
        
        return name
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes is None or size_bytes == 0:
            return "0B"
        
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{size_bytes:4d}{unit}"
                return f"{size_bytes:4.0f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.0f}P"
    
    def _format_date(self, date_obj) -> str:
        """Format date for display (ls-like format)"""
        if not date_obj:
            return '-' * 12
        
        now = date_obj.now(date_obj.tzinfo) if date_obj.tzinfo else date_obj.now()
        diff_days = (now - date_obj).days
        
        if diff_days < 180:
            return date_obj.strftime('%b %d %H:%M')
        else:
            return date_obj.strftime('%b %d  %Y')
    
    def _get_file_type_char(self, mime_type: str) -> str:
        """Get single character representing file type"""
        if mime_type == 'application/vnd.google-apps.folder':
            return 'd'
        elif 'google-apps' in mime_type:
            return 'g'
        else:
            return '-'
    
    def _get_owner_name(self, item: DriveItem, show_ownership: bool) -> str:
        """Get owner name for display"""
        if not item.owners:
            return 'unknown'
        
        owner_name = item.owners[0].get('displayName', 'unknown')
        return owner_name[:8]  # Truncate to 8 chars like ls