"""
統合テスト

実際のボットコードをスキャンするエンドツーエンドテスト。
"""

import os

import pytest

from mper import generate_invite_url, scan_directory, scan_file


class TestRealBotScanning:
    """実際のボットコードスキャンの統合テスト"""

    def test_scan_sample_bot_directory(self):
        """examples/sample_botディレクトリのスキャン"""
        sample_bot_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples", "sample_bot"
        )

        if not os.path.exists(sample_bot_path):
            pytest.skip("sample_botディレクトリが存在しない")

        result = scan_directory(sample_bot_path)

        assert result is not None
        assert result["files_scanned"] > 0
        assert "invite_link_permissions" in result

    def test_scan_examples_directory(self):
        """examplesディレクトリ全体のスキャン"""
        examples_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")

        if not os.path.exists(examples_path):
            pytest.skip("examplesディレクトリが存在しない")

        result = scan_directory(examples_path)

        assert result is not None
        assert result["files_scanned"] > 0


class TestEndToEnd:
    """エンドツーエンドテスト"""

    def test_full_workflow_with_temp_project(self, temp_bot_directory, sample_bot_code):
        """一時プロジェクトを使った完全なワークフロー"""
        tmpdir, create_file = temp_bot_directory

        # ボットファイル作成
        create_file("bot.py", sample_bot_code)
        create_file(
            "cogs/moderation.py",
            """
async def timeout_member(member):
    await member.timeout(duration=60)
""",
        )

        # スキャン実行
        result = scan_directory(tmpdir)

        assert result is not None
        assert result["files_scanned"] == 2

        # 期待されるパーミッションの確認
        all_perms = result.get("inferred_permissions", set()) | result.get("bot_permissions", set())
        assert "ban_members" in all_perms
        assert "kick_members" in all_perms

    def test_generate_invite_url_full_workflow(self, temp_bot_directory, sample_bot_code):
        """招待URL生成の完全なワークフロー"""
        tmpdir, create_file = temp_bot_directory
        create_file("bot.py", sample_bot_code)

        client_id = "123456789012345678"
        url = generate_invite_url(tmpdir, client_id=client_id)

        assert url is not None
        assert "discord.com" in url
        assert client_id in url
        # パーミッションが含まれていることを確認
        assert "permissions=" in url


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_python_file(self, temp_python_file):
        """空のPythonファイル"""
        path = temp_python_file("")
        result = scan_file(path)

        assert result is not None
        assert len(result.get("inferred_permissions", set())) == 0

    def test_python_file_with_only_comments(self, temp_python_file):
        """コメントのみのPythonファイル"""
        path = temp_python_file('''
# This is a comment
# Another comment
"""
Docstring
"""
''')
        result = scan_file(path)

        assert result is not None
        assert len(result.get("inferred_permissions", set())) == 0

    def test_non_discord_python_file(self, temp_python_file):
        """Discord関連でないPythonファイル"""
        path = temp_python_file("""
def hello():
    print("Hello, World!")

class Calculator:
    def add(self, a, b):
        return a + b
""")
        result = scan_file(path)

        assert result is not None
        # Discord関連のパーミッションは検出されないはず
        assert len(result.get("inferred_permissions", set())) == 0

    def test_nested_directory_structure(self, temp_bot_directory):
        """ネストされたディレクトリ構造"""
        tmpdir, create_file = temp_bot_directory

        create_file("main.py", "# Main file")
        create_file(
            "cogs/admin/ban.py",
            """
async def ban_user(member):
    await member.ban()
""",
        )
        create_file(
            "cogs/admin/kick.py",
            """
async def kick_user(member):
    await member.kick()
""",
        )
        create_file(
            "utils/helpers.py",
            """
def format_message(text):
    return text.upper()
""",
        )

        result = scan_directory(tmpdir)

        assert result is not None
        assert result["files_scanned"] == 4
        perms = result.get("inferred_permissions", set())
        assert "ban_members" in perms
        assert "kick_members" in perms


class TestPermissionDetectionAccuracy:
    """パーミッション検出精度のテスト"""

    def test_detect_all_common_permissions(self, temp_python_file):
        """一般的なパーミッション検出の確認"""
        code = """
async def all_operations(guild, channel, member, message):
    # Ban/Kick
    await member.ban()
    await member.kick()

    # Timeout
    await member.timeout(duration=60)

    # Roles
    await member.add_roles(role)
    await guild.create_role(name="test")

    # Channels
    await guild.create_text_channel("test")
    await channel.purge(limit=10)

    # Messages
    await message.pin()
    await message.clear_reactions()

    # Webhooks
    await channel.create_webhook(name="test")

    # Audit
    async for entry in guild.audit_logs():
        pass
"""
        path = temp_python_file(code)
        result = scan_file(path)

        perms = result.get("inferred_permissions", set())

        # 主要なパーミッションが検出されることを確認
        expected = [
            "ban_members",
            "kick_members",
            "moderate_members",
            "manage_roles",
            "manage_channels",
            "manage_messages",
            "manage_webhooks",
            "view_audit_log",
        ]

        for perm in expected:
            assert perm in perms, f"{perm} が検出されなかった"

    def test_decorator_permissions_separate_from_method(self, temp_python_file):
        """デコレータとメソッドからのパーミッションが分離されること"""
        code = """
from discord.ext import commands

@commands.bot_has_permissions(administrator=True)
@commands.has_permissions(manage_guild=True)
async def admin_only(ctx):
    await ctx.send("Admin command")
"""
        path = temp_python_file(code)
        result = scan_file(path)

        # bot_has_permissions -> bot_permissions
        assert "administrator" in result.get("bot_permissions", set())

        # has_permissions -> user_permissions (NOT for invite link)
        assert "manage_guild" in result.get("user_permissions", set())
