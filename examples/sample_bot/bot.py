"""
mper サンプルBot

このBotはmperの動作確認用のシンプルなdiscord.py Botです。
mperでこのBotをスキャンすると、以下のパーミッションが検出されます：
- send_messages (send, reply)
- manage_messages (purge)
- kick_members (kick)
- ban_members (ban)
"""

import os

import discord
from discord import app_commands
from discord.ext import commands

import mper


class ModerationCog(commands.Cog):
    """モデレーション用のコマンド"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="kick", description="メンバーをキックします")
    @app_commands.describe(member="キックするメンバー", reason="理由")
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "理由なし"
    ):
        """メンバーをキックする"""
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.display_name}をキックしました。")

    @app_commands.command(name="ban", description="メンバーをBANします")
    @app_commands.describe(member="BANするメンバー", reason="理由")
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "理由なし"
    ):
        """メンバーをBANする"""
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.display_name}をBANしました。")

    @app_commands.command(name="purge", description="メッセージを一括削除します")
    @app_commands.describe(count="削除するメッセージ数")
    async def purge(
        self,
        interaction: discord.Interaction,
        count: int = 10
    ):
        """メッセージを一括削除する"""
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=count)
        await interaction.followup.send(f"{len(deleted)}件のメッセージを削除しました。")


class UtilityCog(commands.Cog):
    """ユーティリティコマンド"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Botの応答速度を確認します")
    async def ping(self, interaction: discord.Interaction):
        """Pingを返す"""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! {latency}ms")

    @app_commands.command(name="say", description="メッセージを送信します")
    @app_commands.describe(message="送信するメッセージ")
    async def say(self, interaction: discord.Interaction, message: str):
        """メッセージを送信する"""
        await interaction.response.send_message("送信しました！", ephemeral=True)
        await interaction.channel.send(message)

    @app_commands.command(name="invite", description="このBotの招待URLを生成します")
    async def invite(self, interaction: discord.Interaction):
        """
        mperを使ってBotの招待URLを生成する。

        これがmperの使用例です！
        Botのソースコードをスキャンして、必要なパーミッションを自動検出します。
        """
        await interaction.response.defer(ephemeral=True)

        # mperでBotのディレクトリをスキャン
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        client_id = str(self.bot.user.id)

        # 招待URLを生成
        invite_url = mper.generate_invite_url(bot_dir, client_id=client_id)

        # 検出されたパーミッションも取得
        result = mper.scan_directory(bot_dir)
        perms = sorted(result['invite_link_permissions'])

        # Embedで結果を表示
        embed = discord.Embed(
            title="🔗 Bot招待URL",
            description="mperで自動生成された招待URLです",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="検出されたパーミッション",
            value="\n".join([f"• {p}" for p in perms]) or "なし",
            inline=False
        )
        embed.add_field(
            name="招待URL",
            value=invite_url,
            inline=False
        )

        await interaction.followup.send(embed=embed)


async def setup_bot():
    """Botのセットアップ"""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"{bot.user}としてログインしました")
        await bot.tree.sync()
        print("/invite コマンドでmperを使った招待URL生成を試してみてください！")

    await bot.add_cog(ModerationCog(bot))
    await bot.add_cog(UtilityCog(bot))

    return bot


if __name__ == "__main__":
    import asyncio

    async def main():
        bot = await setup_bot()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("DISCORD_TOKENを設定してください")
            return
        await bot.start(token)

    asyncio.run(main())
