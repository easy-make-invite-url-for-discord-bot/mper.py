"""
mper - Discord bot permission scanner

Analyzes discord.py code to detect required permissions and generate invite links.
"""

__version__ = "1.0.0"

from .mper import (
    create_invite_link,
    format_permissions_report,
    scan_directory,
    scan_file,
)
from .permissions import (
    PERMISSION_ALIASES,
    PERMISSIONS,
    calculate_permission_integer,
    get_all_permission_names,
    get_permission_value,
)

__all__ = [
    "__version__",
    "PERMISSIONS",
    "PERMISSION_ALIASES",
    "get_permission_value",
    "calculate_permission_integer",
    "get_all_permission_names",
    "scan_file",
    "scan_directory",
    "create_invite_link",
    "format_permissions_report",
]
