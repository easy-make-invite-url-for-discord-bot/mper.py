"""
mper - Discord Bot Permission Scanner

discord.pyのコードを解析し、必要なパーミッションを検出して招待リンクを生成する。

Example:
    >>> import mper
    >>> url = mper.generate_invite_url("./my_bot", client_id="123456789")
    >>> print(url)
"""

__version__ = "1.1.1"
__author__ = "FreeWiFi7749"

from .mper import (
    create_invite_link,
    format_permissions_report,
    generate_invite_url,
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
    # メタデータ
    "__version__",
    "__author__",
    # パーミッション定数
    "PERMISSIONS",
    "PERMISSION_ALIASES",
    # パーミッションユーティリティ
    "get_permission_value",
    "calculate_permission_integer",
    "get_all_permission_names",
    # スキャン機能
    "scan_file",
    "scan_directory",
    # 招待リンク生成
    "create_invite_link",
    "generate_invite_url",
    "format_permissions_report",
]
