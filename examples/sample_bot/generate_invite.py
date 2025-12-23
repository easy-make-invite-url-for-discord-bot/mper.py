"""
mperを使ってsample_botの招待URLを生成する

このスクリプトを実行すると、bot.pyを解析して
必要なパーミッションを自動検出し、招待URLを生成します。
"""

import os
import sys

import mper


def main():
    # このスクリプトと同じディレクトリにあるbot.pyを対象にする
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("mper サンプルBot - 招待URL生成")
    print("=" * 60)
    print()

    # クライアントIDを取得（環境変数または引数から）
    client_id = os.getenv("DISCORD_CLIENT_ID")
    if len(sys.argv) > 1:
        client_id = sys.argv[1]

    if not client_id:
        print("使い方: python generate_invite.py <CLIENT_ID>")
        print("または環境変数 DISCORD_CLIENT_ID を設定してください")
        print()
        print("デモとしてダミーIDで実行します...")
        client_id = "123456789012345678"

    print(f"クライアントID: {client_id}")
    print(f"スキャン対象: {script_dir}")
    print()

    # mperでスキャンして招待URLを生成
    url = mper.generate_invite_url(script_dir, client_id=client_id)

    print("=" * 60)
    print("生成された招待URL:")
    print("=" * 60)
    print(url)
    print()

    # 詳細情報も表示
    result = mper.scan_directory(script_dir)
    perm_int = mper.calculate_permission_integer(result['invite_link_permissions'])

    print("=" * 60)
    print("検出されたパーミッション:")
    print("=" * 60)
    for perm in sorted(result['invite_link_permissions']):
        value = mper.get_permission_value(perm)
        print(f"  ✓ {perm} (0x{value:X})")

    print()
    print(f"パーミッション整数値: {perm_int}")
    print(f"パーミッション整数値 (16進数): 0x{perm_int:X}")
    print()

    # 証拠も表示
    print("=" * 60)
    print("検出された証拠 (どのメソッド呼び出しが検出されたか):")
    print("=" * 60)
    for perm, evidence_list in result.get('evidence', {}).items():
        print(f"\n{perm}:")
        for file_path, method_call in evidence_list:
            filename = os.path.basename(file_path)
            print(f"  - {filename}:{method_call.line_number} -> {method_call.call_chain}()")


if __name__ == "__main__":
    main()
