"""
mper 基本的な使い方

このサンプルでは、mperをライブラリとしてインポートして
Discord Botの招待URLを生成する方法を示します。
"""

import os

import mper


def main():
    # =====================================================
    # 1. 最も簡単な使い方: generate_invite_url
    # =====================================================
    # Botのディレクトリを指定するだけで、必要なパーミッションを
    # 自動検出して招待URLを生成します（CLIと同じ動作）

    url = mper.generate_invite_url(
        path="./your_bot_directory",  # Botのソースコードがあるディレクトリ
        client_id="123456789012345678"  # BotのクライアントID
    )
    print("=== 生成された招待URL ===")
    print(url)
    print()

    # =====================================================
    # 2. スキャン結果を詳しく確認する
    # =====================================================
    result = mper.scan_directory("./your_bot_directory")

    print("=== スキャン結果 ===")
    print(f"スキャンしたファイル数: {result['files_scanned']}")
    print(f"エラーがあったファイル数: {result['files_with_errors']}")
    print()

    print("=== 検出されたパーミッション ===")
    for perm in sorted(result['invite_link_permissions']):
        print(f"  - {perm}")
    print()

    # パーミッション整数値を計算
    perm_int = mper.calculate_permission_integer(result['invite_link_permissions'])
    print(f"パーミッション整数値: {perm_int}")
    print(f"パーミッション整数値 (16進数): {hex(perm_int)}")
    print()

    # =====================================================
    # 3. 検出された証拠を確認する
    # =====================================================
    print("=== 検出された証拠 ===")
    for perm, evidence_list in result.get('evidence', {}).items():
        print(f"\n{perm}:")
        for ev in evidence_list[:3]:  # 最初の3件だけ表示
            file_path, method_call = ev  # タプルをアンパック
            filename = os.path.basename(file_path)
            print(f"  - {filename}:{method_call.line_number} -> {method_call.call_chain}()")


if __name__ == "__main__":
    main()
