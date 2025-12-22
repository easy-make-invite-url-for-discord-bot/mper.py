# mper.py

Discord bot permission scanner - Analyzes discord.py code to detect required permissions and generate invite links.

discord.pyボットのコードを解析し、必要な権限を検出して招待リンクを生成するツールです。

## Features / 機能

- **Method-based detection (PRIMARY)**: Detects discord.py method calls (`.ban()`, `.kick()`, `.send()`, etc.) and infers required BOT permissions
- **Evidence tracking**: Shows which method calls at which lines require which permissions
- **All 49 Discord permissions**: Supports all Discord API permissions (as of 2025-12-22)
- **Context-aware detection**: Handles `member.edit(nick=...)`, `member.edit(mute=...)`, etc.
- **Decorator support**: `@bot_has_permissions` (supplementary), `@has_permissions` (user requirements only)

## Installation / インストール方法

```sh
pip install mper
```

## Usage / 使い方

```sh
mper /path/to/bot/directory CLIENT_ID
```

### Examples / 例

```sh
# Basic usage
mper /home/user/my_discord_bot 123456789012345678

# With detailed report
mper /home/user/my_discord_bot 123456789012345678 --report

# Verbose output
mper /home/user/my_discord_bot 123456789012345678 --verbose

# Exclude directories
mper /home/user/my_discord_bot 123456789012345678 --exclude tests docs

# Custom OAuth2 scopes
mper /home/user/my_discord_bot 123456789012345678 --scope bot --scope applications.commands
```

### CLI Options / オプション

| Option | Description |
|--------|-------------|
| `--report` | Print detailed permissions report with evidence |
| `--verbose`, `-v` | Show detailed output during scanning |
| `--no-inferred` | Only use declared permissions (from decorators) |
| `--exclude` | Additional directories to exclude |
| `--scope` | OAuth2 scopes for invite link (default: bot, applications.commands) |
| `--output`, `-o` | Output file for invite link (default: bot_invite_url.txt) |

### Output Example / 出力例

```
======================================================================
DETECTED PERMISSIONS (from method calls - PRIMARY)
----------------------------------------------------------------------

ban_members (0x4):
  bot.py:15 -> member.ban()
    [high] Ban a member from the guild

manage_messages (0x2000):
  bot.py:25 -> channel.purge()
    [high] Bulk delete messages

======================================================================
INVITE LINK PERMISSIONS
======================================================================
Source: method-based detection + @bot_has_permissions

  Permissions: ban_members, manage_messages, send_messages
  Integer: 10246
  Hex: 0x2806
```

## How It Works / 仕組み

1. **Method-based detection (PRIMARY)**: Scans Python AST for discord.py method calls and maps them to required permissions
2. **`@bot_has_permissions` (SUPPLEMENTARY)**: Explicit bot permission declarations are added to invite link
3. **`@has_permissions` (REFERENCE ONLY)**: User permission requirements are shown in report but NOT included in invite link

## Supported Permissions / 対応権限

All 49 Discord permissions are supported (bits 0-46, 49-50). See [Discord API Documentation](https://discord.com/developers/docs/topics/permissions) for details.

## License / ライセンス

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

このツールはMITライセンスのもとで公開されています。複製、編集、再公開は基本的に全て許可されています。

## Issues / 質問や不具合の報告

Please create issues with appropriate tags:
- `bug` - Bug reports / バグ報告
- `enhancement` - Feature requests / 要望
- `question` - Questions / 質問

## Credits / クレジット

- Developer: [@FreeWiFi7749](https://github.com/FreeWiFi7749)
