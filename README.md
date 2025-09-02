# gdls

**Unix `ls` for Google Drive.**

Browse your Google Drive from the terminal just like your local filesystem.

## Install

```bash
# Get it
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/gagb/google-drive-api-tools.git
cd google-drive-api-tools
uv pip install -e .

# Set up Google Drive API
# 1. Go to console.cloud.google.com
# 2. Enable Drive API + create OAuth credentials  
# 3. Download as credentials.json
# 4. Run: gdls /
```

## Use

```bash
gdls /                    # List root
gdls /Documents           # List folder  
gdls -l /                 # Details
gdls -lH /                # Human sizes
gdls --sort=size /        # By size
gdls -s /                 # Calculate folder sizes
gdls -o /                 # Your files only
```

## Options

```
-l, --long               Details (size, date, owner)
-H, --human-readable     1K, 234M, 2G instead of bytes  
-s, --size               Calculate actual folder sizes
-o, --owned              Your files only (excludes shared)
--sort TYPE              name, size, date, type
--clear-cache            Fresh start
```

## Why

Managing Google Drive storage is painful. You pay for 100GB but use 1TB because you can't see what's taking space.

`gdls` shows you exactly what counts against your quota. Shared folders don't count. Your duplicates do.

Find your largest files:
```bash
gdls -lHso --sort=size /
```

Clean up efficiently.

## Architecture

Six focused classes. No parameter explosion. Clean errors. Full validation.

```
core.py      # Data structures and constants
auth.py      # Google Drive authentication  
cache.py     # Path and folder size caching
paths.py     # Unix path → Drive folder ID
explorer.py  # File listing and calculations  
display.py   # Formatting and output
cli.py       # Command interface
```

## Requirements

Python 3.8+. Google Drive API access.

That's it.