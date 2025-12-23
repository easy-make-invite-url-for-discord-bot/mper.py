"""
mper CLIのスタイル付き出力

Richライブラリを使用した美しいターミナル出力:
    - カラーテキストとパネル
    - プログレスバーとスピナー
    - スタイル付きテーブル
    - アニメーションフィードバック
"""

import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .permissions import get_permission_value

# パーミッションカテゴリ別の色スキーマ
PERMISSION_COLORS: Dict[str, str] = {
    # Dangerous permissions (red)
    "administrator": "bold red",
    "ban_members": "red",
    "kick_members": "red",
    "manage_guild": "red",
    "manage_roles": "red",
    "manage_channels": "red",
    "manage_webhooks": "red",
    "manage_messages": "red",
    "manage_threads": "red",
    "manage_nicknames": "yellow",
    "manage_events": "yellow",
    "manage_guild_expressions": "yellow",
    "moderate_members": "red",
    "move_members": "yellow",
    "mute_members": "yellow",
    "deafen_members": "yellow",
    "view_audit_log": "yellow",
    # Medium permissions (yellow)
    "send_messages": "green",
    "send_messages_in_threads": "green",
    "embed_links": "green",
    "attach_files": "green",
    "add_reactions": "green",
    "use_external_emojis": "green",
    "use_external_stickers": "green",
    "read_message_history": "green",
    "view_channel": "green",
    "connect": "green",
    "speak": "green",
    "stream": "green",
    "use_vad": "green",
    "create_instant_invite": "green",
    "change_nickname": "green",
    "use_application_commands": "green",
    # Default
    "default": "white",
}

# 信頼度別の色スキーマ
CONFIDENCE_COLORS: Dict[str, str] = {
    "high": "green",
    "medium": "yellow",
    "low": "red",
    "none": "dim",
}


class StyledOutput:
    """
    Richを使用したスタイル付きCLI出力を処理するクラス。

    Attributes:
        plain: プレーンテキストモード
        no_color: 色なしモード
        console: Rich Consoleインスタンス
    """

    def __init__(self, no_color: bool = False, plain: bool = False):
        """
        Initialize styled output.

        Args:
            no_color: Disable colors but keep formatting
            plain: Use completely plain text output (no Rich)
        """
        self.plain = plain
        self.no_color = no_color

        # Auto-detect if we should use plain mode
        if not sys.stdout.isatty():
            self.plain = True

        if not self.plain:
            self.console = Console(
                force_terminal=True,
                no_color=no_color,
                highlight=False,
                color_system="auto" if not no_color else None,
            )
        else:
            self.console = None

    def print_banner(self) -> None:
        """バナーを表示する。"""
        if self.plain:
            print("=" * 50)
            print("  mper - Discord Bot Permission Scanner")
            print("=" * 50)
            print()
            return

        banner_text = Text()
        banner_text.append("  mper", style="bold cyan")
        banner_text.append(" - Discord Bot Permission Scanner", style="white")

        self.console.print(
            Panel(
                banner_text,
                box=box.ROUNDED,
                border_style="cyan",
                padding=(0, 2),
            )
        )
        self.console.print()

    def create_progress(self) -> Optional[Progress]:
        """スキャン用のプログレスバーを作成する。"""
        if self.plain:
            return None

        return Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[current_file]}"),
            console=self.console,
            transient=True,
        )

    def print_scanning_start(self, directory: str) -> None:
        """スキャン開始メッセージを表示する。"""
        if self.plain:
            print(f"Scanning: {directory}")
            return

        self.console.print(f"[bold blue]Scanning:[/] {directory}")

    def print_scanning_file(self, file_path: str) -> None:
        """現在スキャン中のファイルを表示する。"""
        if self.plain:
            print(f"  Scanning: {file_path}")
            return

        self.console.print(f"  [dim]Scanning:[/] {file_path}")

    def print_scan_complete(self, files_scanned: int, files_with_errors: int) -> None:
        """スキャン完了サマリーを表示する。"""
        if self.plain:
            print(f"\nScanned {files_scanned} files ({files_with_errors} with errors)")
            return

        status = "green" if files_with_errors == 0 else "yellow"
        self.console.print()
        self.console.print(
            f"[{status}]Scanned {files_scanned} files[/] "
            f"[dim]({files_with_errors} with errors)[/]"
        )

    def print_permissions_table(
        self,
        evidence: Dict[str, List[Tuple[str, Any]]],
        title: str = "Detected Permissions",
        subtitle: str = "from method calls - PRIMARY",
    ) -> None:
        """パーミッションを証拠付きのスタイル付きテーブルで表示する。"""
        if self.plain:
            print(f"\n{title} ({subtitle})")
            print("-" * 50)
            for perm in sorted(evidence.keys()):
                value = get_permission_value(perm)
                calls = evidence[perm]
                print(f"  {perm} (0x{value:X}) - {len(calls)} call(s)")
                for file_path, call in calls[:3]:  # Show max 3 examples
                    import os

                    rel_path = os.path.basename(file_path)
                    print(f"    {rel_path}:{call.line_number} -> {call.call_chain}()")
                if len(calls) > 3:
                    print(f"    ... and {len(calls) - 3} more")
            print()
            return

        table = Table(
            title=f"[bold]{title}[/]\n[dim]{subtitle}[/]",
            box=box.ROUNDED,
            border_style="blue",
            header_style="bold cyan",
            show_lines=True,
        )

        table.add_column("Permission", style="bold")
        table.add_column("Hex", justify="right", style="dim")
        table.add_column("Evidence", justify="center")
        table.add_column("Source", style="dim")

        for perm in sorted(evidence.keys()):
            value = get_permission_value(perm)
            calls = evidence[perm]
            color = PERMISSION_COLORS.get(perm, PERMISSION_COLORS["default"])

            # Get first source as example
            if calls:
                import os

                file_path, call = calls[0]
                rel_path = os.path.basename(file_path)
                source = f"{rel_path}:{call.line_number}"
            else:
                source = "-"

            table.add_row(
                Text(perm, style=color),
                f"0x{value:X}",
                f"{len(calls)} call(s)",
                source,
            )

        self.console.print()
        self.console.print(table)

    def print_permissions_list(
        self,
        permissions: Set[str],
        title: str,
        subtitle: str = "",
        style: str = "blue",
    ) -> None:
        """パーミッションのシンプルなリストを表示する。"""
        if not permissions:
            return

        if self.plain:
            print(f"\n{title}")
            if subtitle:
                print(f"  ({subtitle})")
            for perm in sorted(permissions):
                value = get_permission_value(perm)
                print(f"  {perm} (0x{value:X})")
            print()
            return

        content = []
        for perm in sorted(permissions):
            value = get_permission_value(perm)
            color = PERMISSION_COLORS.get(perm, PERMISSION_COLORS["default"])
            content.append(f"[{color}]{perm}[/] [dim](0x{value:X})[/]")

        panel_content = "\n".join(content)
        if subtitle:
            panel_content = f"[dim]{subtitle}[/]\n\n" + panel_content

        self.console.print()
        self.console.print(
            Panel(
                panel_content,
                title=f"[bold]{title}[/]",
                box=box.ROUNDED,
                border_style=style,
                padding=(1, 2),
            )
        )

    def print_warnings(self, warnings: List[str], max_show: int = 5) -> None:
        """警告パネルを表示する。"""
        if not warnings:
            return

        if self.plain:
            print("\nWarnings:")
            for warning in warnings[:max_show]:
                print(f"  - {warning}")
            if len(warnings) > max_show:
                print(f"  ... and {len(warnings) - max_show} more")
            print()
            return

        content = []
        for warning in warnings[:max_show]:
            content.append(f"[yellow]![/] {warning}")
        if len(warnings) > max_show:
            content.append(f"[dim]... and {len(warnings) - max_show} more[/]")

        self.console.print()
        self.console.print(
            Panel(
                "\n".join(content),
                title="[bold yellow]Warnings[/]",
                box=box.ROUNDED,
                border_style="yellow",
                padding=(1, 2),
            )
        )

    def print_invite_link(
        self,
        invite_link: str,
        permissions: Set[str],
        total_int: int,
        output_file: str,
    ) -> None:
        """招待リンクパネルを表示する。"""
        if self.plain:
            print("\n" + "=" * 50)
            print("INVITE LINK")
            print("=" * 50)
            print(f"Permissions: {', '.join(sorted(permissions)) if permissions else 'None'}")
            print(f"Integer: {total_int}")
            print(f"Hex: 0x{total_int:X}")
            print()
            print(invite_link)
            print()
            print(f"Saved to: {output_file}")
            print()
            return

        # Build content
        perm_list = ", ".join(sorted(permissions)) if permissions else "None"
        content = Text()
        content.append("Permissions: ", style="dim")
        content.append(f"{len(permissions)}", style="bold cyan")
        content.append(f" ({perm_list[:50]}{'...' if len(perm_list) > 50 else ''})\n", style="dim")
        content.append("Integer: ", style="dim")
        content.append(f"{total_int}\n", style="bold")
        content.append("Hex: ", style="dim")
        content.append(f"0x{total_int:X}\n\n", style="bold")
        content.append(invite_link, style="bold green underline")
        content.append("\n\n", style="")
        content.append("Saved to: ", style="dim")
        content.append(output_file, style="cyan")

        self.console.print()
        self.console.print(
            Panel(
                content,
                title="[bold green]Invite Link[/]",
                box=box.DOUBLE,
                border_style="green",
                padding=(1, 2),
            )
        )
        self.console.print()

    def print_summary(
        self,
        inferred_count: int,
        bot_count: int,
        user_count: int,
        total_int: int,
    ) -> None:
        """検出されたパーミッションのサマリーを表示する。"""
        if self.plain:
            print("\nSummary:")
            print(f"  Method-based (PRIMARY): {inferred_count} permissions")
            print(f"  @bot_has_permissions: {bot_count} permissions")
            print(f"  @has_permissions (user): {user_count} permissions")
            print(f"  Total for invite: {total_int}")
            return

        table = Table(
            title="[bold]Permission Summary[/]",
            box=box.SIMPLE,
            show_header=False,
            padding=(0, 2),
        )

        table.add_column("Source", style="dim")
        table.add_column("Count", justify="right", style="bold")
        table.add_column("Note", style="dim")

        table.add_row(
            "Method-based",
            str(inferred_count),
            "[green]PRIMARY - for invite[/]",
        )
        table.add_row(
            "@bot_has_permissions",
            str(bot_count),
            "[blue]SUPPLEMENTARY[/]",
        )
        table.add_row(
            "@has_permissions",
            str(user_count),
            "[yellow]User requirements only[/]",
        )

        self.console.print()
        self.console.print(table)

    def print_error(self, message: str) -> None:
        """エラーメッセージを表示する。"""
        if self.plain:
            print(f"Error: {message}", file=sys.stderr)
            return

        self.console.print(f"[bold red]Error:[/] {message}", style="red")

    def print_success(self, message: str) -> None:
        """成功メッセージを表示する。"""
        if self.plain:
            print(message)
            return

        self.console.print(f"[bold green]{message}[/]")

    def check_version_with_spinner(self) -> Optional[Tuple[str, str]]:
        """
        スピナーアニメーション付きでバージョンチェックを実行する。

        Returns:
            更新がある場合: (現在のバージョン, 最新バージョン) のタプル
            最新版またはチェック失敗時: None
        """
        from .version_check import check_for_updates

        if self.plain:
            return check_for_updates()

        from rich.live import Live
        from rich.spinner import Spinner

        spinner = Spinner("dots", text="[dim]アップデートを確認中...[/]", style="cyan")

        with Live(spinner, console=self.console, transient=True, refresh_per_second=10):
            return check_for_updates()

    def print_update_notice(self, current_version: str, latest_version: str) -> None:
        """
        新しいバージョンがリリースされている場合の通知を表示する。

        Args:
            current_version: 現在のバージョン
            latest_version: 最新バージョン
        """
        if self.plain:
            print()
            print("=" * 50)
            print("  新しいバージョンがリリースされています!")
            print(f"  現在: v{current_version} → 最新: v{latest_version}")
            print("  更新: pip install --upgrade mper")
            print("=" * 50)
            print()
            return

        from rich.align import Align

        content = (
            "[bold yellow]✨ 新しいバージョンがリリースされています! ✨[/]\n\n"
            f"[dim]現在:[/] [bold red]v{current_version}[/]"
            f"  [bold white]→[/]  "
            f"[dim]最新:[/] [bold green]v{latest_version}[/]\n\n"
            "[dim]更新コマンド:[/]\n"
            "[bold cyan underline]  pip install --upgrade mper[/]"
        )

        self.console.print()
        self.console.print(
            Panel(
                Align.center(content),
                title="[bold yellow]📦 Update Available[/]",
                subtitle="[dim]https://pypi.org/project/mper/[/]",
                box=box.DOUBLE,
                border_style="yellow",
                padding=(1, 2),
            )
        )
