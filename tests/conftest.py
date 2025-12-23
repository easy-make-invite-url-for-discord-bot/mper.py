"""
pytest共通設定とフィクスチャ
"""

import os
import tempfile

import pytest


@pytest.fixture
def temp_python_file():
    """
    一時的なPythonファイルを作成するフィクスチャ。

    Yields:
        作成されたファイルのパス（使用後に自動削除）
    """

    def _create_file(content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        f.write(content)
        f.flush()
        f.close()
        return f.name

    created_files = []

    def factory(content: str) -> str:
        path = _create_file(content)
        created_files.append(path)
        return path

    yield factory

    # クリーンアップ
    for path in created_files:
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture
def temp_bot_directory():
    """
    一時的なボットプロジェクトディレクトリを作成するフィクスチャ。

    Yields:
        ディレクトリパスとファイル作成関数のタプル
    """
    with tempfile.TemporaryDirectory() as tmpdir:

        def create_file(filename: str, content: str) -> str:
            filepath = os.path.join(tmpdir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
            return filepath

        yield tmpdir, create_file


@pytest.fixture
def sample_bot_code():
    """
    サンプルのボットコードを提供するフィクスチャ。
    """
    return '''
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.command()
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(ban_members=True, kick_members=True)
async def moderation(ctx, member: discord.Member):
    """モデレーションコマンド"""
    await member.ban(reason="テスト")
    await member.kick(reason="テスト")

@bot.command()
async def purge(ctx, limit: int):
    """メッセージ削除コマンド"""
    await ctx.channel.purge(limit=limit)

@bot.command()
async def create_role(ctx, name: str):
    """ロール作成コマンド"""
    await ctx.guild.create_role(name=name)

bot.run("TOKEN")
'''


@pytest.fixture
def minimal_bot_code():
    """
    最小限のボットコードを提供するフィクスチャ。
    """
    return """
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

bot.run("TOKEN")
"""
