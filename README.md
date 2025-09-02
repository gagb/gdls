# gdls - Google Drive ls Command

A Unix-like `ls` command for Google Drive. Browse your Google Drive from the terminal just like your local filesystem!

## Features

- 🗂️ **Unix-like interface** - Works just like the `ls` command you know and love
- 📁 **Navigate directories** - Use paths like `/` or `/Documents/Projects`
- 🎨 **Color-coded output** - Folders in blue, Google Docs in green
- 📊 **Multiple display modes** - Long format (`-l`), human-readable sizes (`-H`)
- 🔄 **Sorting options** - Sort by name, size, date, or type
- 🔍 **Recursive listing** - Explore entire directory trees with `-R`
- ⚡ **Path caching** - Fast repeated operations

## Installation

### Quick Install with uv

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install gdls
git clone https://github.com/gagb/google-drive-api-tools.git
cd google-drive-api-tools
uv pip install -e .
```

### Setup Google Drive API

1. **Enable Google Drive API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Create credentials (OAuth 2.0 Client ID - Web application type)
   - Add `http://localhost:8080/` to Authorized redirect URIs
   - Download the credentials as `credentials.json`

2. **Place credentials:**
   ```bash
   # Put credentials.json in the project directory
   cp ~/Downloads/credentials.json .
   ```

3. **First run (authentication):**
   ```bash
   gdls /
   # This will open a browser for authentication
   # After authorization, a token will be saved for future use
   ```

## Usage

### Basic Commands

```bash
# List root directory
gdls /

# List specific folder
gdls /Documents

# List with details (long format)
gdls -l /

# Human-readable sizes with long format
gdls -lH /

# Sort by size (largest first)
gdls --sort=size /

# Recursive listing
gdls -R /Photos

# Show hidden (trashed) files
gdls -a /
```

### Command Options

| Option | Description |
|--------|-------------|
| `-l, --long` | Use long listing format (shows size, date, owner) |
| `-H, --human-readable` | Print sizes in human readable format (1K, 234M, 2G) |
| `-a, --all` | Show all files including trashed |
| `-R, --recursive` | List subdirectories recursively |
| `-r, --reverse` | Reverse order while sorting |
| `-s, --size` | Calculate actual folder sizes (accurate but slower) |
| `--sort TYPE` | Sort by: name, size, date, or type |
| `--no-cache` | Clear cache before running |

### Examples

```bash
# Find large files in your Drive
gdls -lH --sort=size /

# Find folders taking up the most space (accurate but slower)
gdls -lHs --sort=size /

# Explore a project folder
gdls -lH /Projects/2024

# See everything in Documents recursively
gdls -R /Documents

# Check recently modified files
gdls -l --sort=date /
```

## Additional Tools

This package also includes:

- **`find_large_files.py`** - Find and analyze large files taking up space
- **`list_drive_files.py`** - Simple file lister

Run them with:
```bash
uv run python find_large_files.py
uv run python list_drive_files.py
```

## File Type Indicators

- 📁 **Blue text with /** - Folders
- 📄 **Green text** - Google Docs/Sheets/Slides
- 📎 **White text** - Regular files

## Troubleshooting

### Authentication Issues

If you see "Access blocked" error:
1. Make sure you've added yourself as a test user in Google Cloud Console
2. Go to APIs & Services → OAuth consent screen → Test users
3. Add your email address

### Performance

- First run in each directory may be slower as it builds the cache
- Subsequent runs use cached folder IDs for faster navigation
- Use `--no-cache` if you see stale data

## Requirements

- Python 3.8+
- Google Drive API enabled
- OAuth 2.0 credentials

## License

MIT