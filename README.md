# Google Drive API File Lister

This project lists files from your Google Drive using the Google Drive API v3.

## Setup

1. **Enable Google Drive API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials as `credentials.json`

2. **Install uv (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

4. **Place credentials:**
   - Put the downloaded `credentials.json` file in this directory

5. **Run the script:**
   ```bash
   uv run python list_drive_files.py
   ```

   On first run, it will open a browser for authentication. After authorization, a `token.pickle` file will be created for future use.

## Files

- `list_drive_files.py` - Main script to list Google Drive files
- `pyproject.toml` - Project configuration and dependencies for uv
- `requirements.txt` - Legacy Python dependencies (kept for compatibility)
- `credentials.json` - OAuth2 credentials (you need to add this)
- `token.pickle` - Saved authentication token (created after first run)