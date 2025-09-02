#!/usr/bin/env python3
"""
Google Drive ls command - Unix-like ls for Google Drive
"""

import argparse
import sys

from .auth import DriveAuth
from .cache import DriveCache
from .core import DriveError, ListOptions
from .display import DisplayFormatter
from .explorer import DriveExplorer
from .paths import PathResolver


class GDriveCLI:
    """Clean CLI interface for Google Drive listing"""
    
    def __init__(self):
        self.auth = DriveAuth()
        self.cache = DriveCache()
        self.service = None
        self.path_resolver = None
        self.explorer = None
        self.formatter = None
    
    def initialize(self):
        """Initialize all components"""
        try:
            self.service = self.auth.get_service()
            self.path_resolver = PathResolver(self.service, self.cache)
            self.explorer = DriveExplorer(self.service, self.cache)
            self.formatter = DisplayFormatter()
        except Exception as e:
            raise DriveError(f"Failed to initialize: {e}")
    
    def list_directory(self, path: str, options: ListOptions):
        """List directory with given options"""
        try:
            path_info = self.path_resolver.resolve(path)
            items = self.explorer.list_files(path_info.id, options)
            self.formatter.format_items(items, options)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='List Google Drive files and folders (Unix ls-like interface)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # List root directory
  %(prog)s /Documents           # List Documents folder  
  %(prog)s -lH /                # Long format with human-readable sizes
  %(prog)s --sort=size /        # Sort by file size
        """
    )
    
    parser.add_argument('path', nargs='?', default='/',
                       help='Path to list (default: /)')
    parser.add_argument('-l', '--long', action='store_true',
                       help='Use long listing format')
    parser.add_argument('-H', '--human-readable', action='store_true',
                       help='Print sizes in human readable format')
    parser.add_argument('-a', '--all', action='store_true',
                       help='Show all files including trashed')
    parser.add_argument('-r', '--reverse', action='store_true',
                       help='Reverse order while sorting')
    parser.add_argument('--sort', choices=['name', 'size', 'date', 'type'],
                       default='name',
                       help='Sort by attribute (default: name)')
    parser.add_argument('-s', '--size', action='store_true',
                       help='Calculate and show actual folder sizes')
    parser.add_argument('-o', '--owned', action='store_true',
                       help='Show only files/folders owned by you')
    parser.add_argument('-O', '--ownership', action='store_true',
                       help='Show detailed ownership information')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear cache before running')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize CLI
    cli = GDriveCLI()
    
    try:
        if args.clear_cache:
            cli.cache.clear()
        
        cli.initialize()
        
        # Create options from arguments
        options = ListOptions(
            long_format=args.long,
            human_readable=args.human_readable,
            show_hidden=args.all,
            sort_by=args.sort,
            reverse_sort=args.reverse,
            show_size=args.size,
            owned_only=args.owned,
            show_ownership=args.ownership
        )
        
        cli.list_directory(args.path, options)
        
    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()