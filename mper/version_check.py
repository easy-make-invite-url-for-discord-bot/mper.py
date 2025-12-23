"""
バージョンチェック機能

PyPIから最新バージョンを取得し、現在のバージョンと比較する。
CLI実行時にアップデート通知を表示するために使用。
"""

import json
import urllib.request
from typing import Optional, Tuple

from . import __version__

# PyPI APIエンドポイント
PYPI_URL = "https://pypi.org/pypi/mper/json"

# タイムアウト（秒）- CLIの応答性を損なわないように短く設定
REQUEST_TIMEOUT = 3


def parse_version(version: str) -> Tuple[int, ...]:
    """
    バージョン文字列をタプルに変換する。

    Args:
        version: バージョン文字列 (例: "1.2.3")

    Returns:
        バージョンのタプル (例: (1, 2, 3))
    """
    try:
        return tuple(int(x) for x in version.split("."))
    except ValueError:
        return (0,)


def get_latest_version() -> Optional[str]:
    """
    PyPIから最新バージョンを取得する。

    Returns:
        最新バージョンの文字列、取得失敗時はNone
    """
    try:
        req = urllib.request.Request(
            PYPI_URL,
            headers={"Accept": "application/json", "User-Agent": f"mper/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("info", {}).get("version")
    except Exception:
        # ネットワークエラー、タイムアウト等は無視
        return None


def check_for_updates() -> Optional[Tuple[str, str]]:
    """
    新しいバージョンがあるかチェックする。

    Returns:
        新しいバージョンがある場合: (現在のバージョン, 最新バージョン) のタプル
        最新版の場合またはチェック失敗時: None
    """
    latest = get_latest_version()
    if latest is None:
        return None

    current = __version__
    if parse_version(latest) > parse_version(current):
        return (current, latest)

    return None
