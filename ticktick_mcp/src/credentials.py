"""
Persistent credential storage for TickTick MCP Server.

Stores tokens in a platform-appropriate location:
- macOS/Linux: ~/.config/ticktick-mcp/credentials.json
- Windows: %APPDATA%/ticktick-mcp/credentials.json
"""

import os
import json
import stat
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_config_dir() -> Path:
    """Get the platform-appropriate config directory."""
    if os.name == 'nt':  # Windows
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        config_dir = Path(base) / 'ticktick-mcp'
    else:  # macOS/Linux
        xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        config_dir = Path(xdg_config) / 'ticktick-mcp'

    return config_dir


def get_credentials_path() -> Path:
    """Get the path to the credentials file."""
    return get_config_dir() / 'credentials.json'


def load_credentials() -> Dict[str, Any]:
    """
    Load credentials from persistent storage.

    Returns:
        Dictionary with access_token, refresh_token, etc.
        Empty dict if no credentials found.
    """
    creds_path = get_credentials_path()

    if not creds_path.exists():
        return {}

    try:
        with open(creds_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load credentials: {e}")
        return {}


def save_credentials(credentials: Dict[str, Any]) -> None:
    """
    Save credentials to persistent storage with secure permissions.

    Args:
        credentials: Dictionary with access_token, refresh_token, etc.
    """
    config_dir = get_config_dir()
    creds_path = get_credentials_path()

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write credentials
    with open(creds_path, 'w') as f:
        json.dump(credentials, f, indent=2)

    # Set secure permissions (owner read/write only)
    if os.name != 'nt':  # Unix-like systems
        os.chmod(creds_path, stat.S_IRUSR | stat.S_IWUSR)

    logger.info(f"Credentials saved to {creds_path}")


def clear_credentials() -> None:
    """Remove stored credentials."""
    creds_path = get_credentials_path()

    if creds_path.exists():
        creds_path.unlink()
        logger.info("Credentials cleared")


def get_access_token() -> Optional[str]:
    """Get the stored access token."""
    creds = load_credentials()
    return creds.get('access_token')


def get_refresh_token() -> Optional[str]:
    """Get the stored refresh token."""
    creds = load_credentials()
    return creds.get('refresh_token')
