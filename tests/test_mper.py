"""
mper.py のユニットテスト

スキャン機能と招待リンク生成のテスト。
"""

import os
import tempfile

from mper import (
    __version__,
    create_invite_link,
    generate_invite_url,
    scan_directory,
    scan_file,
)
from mper.mper import (
    DEFAULT_EXCLUDE_DIRS,
    MethodCall,
    PermissionVisitor,
    calculate_permissions,
    format_permissions_report,
)


class TestVersion:
    """バージョン情報のテスト"""

    def test_version_exists(self):
        """バージョンが定義されていることを確認"""
        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_version_format(self):
        """バージョンがセマンティックバージョニング形式であることを確認"""
        parts = __version__.split(".")
        assert len(parts) >= 2, "バージョンは最低でもメジャー.マイナーの形式が必要"


class TestMethodCall:
    """MethodCallデータクラスのテスト"""

    def test_basic_creation(self):
        """基本的なインスタンス生成"""
        call = MethodCall(
            method_name="ban",
            receiver_hint="member",
            line_number=10,
            permissions=["ban_members"],
            confidence="high",
            description="Ban a member",
        )
        assert call.method_name == "ban"
        assert call.receiver_hint == "member"
        assert call.line_number == 10

    def test_call_chain_property(self):
        """call_chainプロパティのテスト"""
        call = MethodCall(
            method_name="ban",
            receiver_hint="member",
            line_number=10,
            permissions=["ban_members"],
            confidence="high",
            description="Ban a member",
        )
        assert call.call_chain == "member.ban"

    def test_call_chain_without_receiver(self):
        """レシーバーなしのcall_chain"""
        call = MethodCall(
            method_name="ban",
            receiver_hint=None,
            line_number=10,
            permissions=["ban_members"],
            confidence="high",
            description="Ban a member",
        )
        assert call.call_chain == "ban"


class TestPermissionVisitor:
    """PermissionVisitorのテスト"""

    def test_detect_ban_method(self):
        """banメソッドの検出"""
        code = """
async def ban_user(member):
    await member.ban()
"""
        import ast

        tree = ast.parse(code)
        visitor = PermissionVisitor("test.py")
        visitor.visit(tree)

        assert len(visitor.method_calls) > 0
        ban_calls = [c for c in visitor.method_calls if c.method_name == "ban"]
        assert len(ban_calls) > 0

    def test_detect_kick_method(self):
        """kickメソッドの検出"""
        code = """
async def kick_user(member):
    await member.kick()
"""
        import ast

        tree = ast.parse(code)
        visitor = PermissionVisitor("test.py")
        visitor.visit(tree)

        kick_calls = [c for c in visitor.method_calls if c.method_name == "kick"]
        assert len(kick_calls) > 0

    def test_detect_bot_has_permissions_decorator(self):
        """@bot_has_permissionsデコレータの検出"""
        code = """
from discord.ext import commands

@commands.bot_has_permissions(manage_messages=True)
async def clear(ctx):
    pass
"""
        import ast

        tree = ast.parse(code)
        visitor = PermissionVisitor("test.py")
        visitor.visit(tree)

        assert "manage_messages" in visitor.bot_permissions

    def test_detect_has_permissions_decorator(self):
        """@has_permissionsデコレータの検出（ユーザーパーミッション）"""
        code = """
from discord.ext import commands

@commands.has_permissions(administrator=True)
async def admin_cmd(ctx):
    pass
"""
        import ast

        tree = ast.parse(code)
        visitor = PermissionVisitor("test.py")
        visitor.visit(tree)

        assert "administrator" in visitor.user_permissions


class TestScanFile:
    """scan_file関数のテスト"""

    def test_scan_valid_python_file(self):
        """有効なPythonファイルのスキャン"""
        code = """
async def test_ban(member):
    await member.ban()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            try:
                result = scan_file(f.name)
                assert result is not None
                assert "inferred_permissions" in result
            finally:
                os.unlink(f.name)

    def test_scan_nonexistent_file(self):
        """存在しないファイルのスキャン"""
        result = scan_file("/nonexistent/path/file.py")
        # エラーはwarningsに含まれる
        assert result is not None
        assert len(result.get("warnings", [])) > 0

    def test_scan_syntax_error_file(self):
        """構文エラーのあるファイルのスキャン"""
        code = """
def broken(
    # 閉じ括弧がない
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()

            try:
                result = scan_file(f.name)
                # エラーがあっても結果は返される（警告情報付き）
                assert result is not None
                assert len(result.get("warnings", [])) > 0
            finally:
                os.unlink(f.name)


class TestScanDirectory:
    """scan_directory関数のテスト"""

    def test_scan_empty_directory(self):
        """空のディレクトリのスキャン"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_directory(tmpdir)
            assert result is not None
            assert result["files_scanned"] == 0

    def test_scan_directory_with_python_files(self):
        """Pythonファイルを含むディレクトリのスキャン"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # テスト用ファイル作成
            filepath = os.path.join(tmpdir, "bot.py")
            with open(filepath, "w") as f:
                f.write("""
async def ban_cmd(member):
    await member.ban()
""")

            result = scan_directory(tmpdir)
            assert result is not None
            assert result["files_scanned"] >= 1
            assert "ban_members" in result.get("inferred_permissions", set())

    def test_scan_excludes_default_dirs(self):
        """デフォルトの除外ディレクトリがスキップされることを確認"""
        assert ".venv" in DEFAULT_EXCLUDE_DIRS
        assert "__pycache__" in DEFAULT_EXCLUDE_DIRS
        assert ".git" in DEFAULT_EXCLUDE_DIRS


class TestCreateInviteLink:
    """create_invite_link関数のテスト"""

    def test_basic_invite_link(self):
        """基本的な招待リンクの生成"""
        client_id = "123456789012345678"
        permissions = 8  # administrator

        url = create_invite_link(client_id, permissions)

        assert "discord.com" in url
        assert client_id in url
        assert "permissions=8" in url

    def test_invite_link_with_scopes(self):
        """スコープ付き招待リンク"""
        client_id = "123456789012345678"
        permissions = 0
        scopes = ["bot", "applications.commands"]

        url = create_invite_link(client_id, permissions, scopes)

        assert "bot" in url
        assert "applications.commands" in url

    def test_invite_link_zero_permissions(self):
        """パーミッションなしの招待リンク"""
        url = create_invite_link("123456789012345678", 0)
        assert "permissions=0" in url


class TestGenerateInviteUrl:
    """generate_invite_url関数のテスト"""

    def test_generate_from_directory(self):
        """ディレクトリから招待URLを生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # テスト用ファイル作成
            filepath = os.path.join(tmpdir, "bot.py")
            with open(filepath, "w") as f:
                f.write("""
async def kick_cmd(member):
    await member.kick()
""")

            url = generate_invite_url(tmpdir, client_id="123456789012345678")

            assert url is not None
            assert "discord.com" in url
            assert "123456789012345678" in url


class TestCalculatePermissions:
    """calculate_permissions関数のテスト"""

    def test_empty_set(self):
        """空のセットは0を返す"""
        assert calculate_permissions(set()) == 0

    def test_single_permission(self):
        """単一パーミッションの計算"""
        result = calculate_permissions({"administrator"})
        assert result == (1 << 3)  # administrator bit

    def test_multiple_permissions(self):
        """複数パーミッションの計算"""
        result = calculate_permissions({"ban_members", "kick_members"})
        expected = (1 << 2) | (1 << 1)  # ban_members | kick_members
        assert result == expected


class TestFormatPermissionsReport:
    """format_permissions_report関数のテスト"""

    def test_basic_report(self):
        """基本的なレポート生成"""
        result = {
            "files_scanned": 5,
            "files_with_errors": 0,
            "inferred_permissions": {"ban_members", "kick_members"},
            "bot_permissions": set(),
            "user_permissions": set(),
            "invite_link_permissions": {"ban_members", "kick_members"},
            "warnings": [],
        }

        report = format_permissions_report(result)

        assert "Discord Bot Permission Scan Report" in report
        assert "Files scanned: 5" in report
        assert "ban_members" in report

    def test_report_with_warnings(self):
        """警告付きレポート"""
        result = {
            "files_scanned": 1,
            "files_with_errors": 1,
            "inferred_permissions": set(),
            "bot_permissions": set(),
            "user_permissions": set(),
            "invite_link_permissions": set(),
            "warnings": ["テスト警告"],
        }

        report = format_permissions_report(result)

        assert "WARNINGS" in report
        assert "テスト警告" in report
