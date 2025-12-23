"""
mper カスタムパーミッションの使い方

スキャンを使わず、パーミッション名を直接指定して
招待URLを生成する方法を示します。
"""

import mper


def main():
    # =====================================================
    # パーミッション名から招待URLを作成
    # =====================================================

    # 必要なパーミッションをリストで指定
    permissions = [
        'send_messages',
        'read_messages',
        'manage_messages',
        'embed_links',
        'attach_files',
        'add_reactions',
    ]

    # パーミッション整数値を計算
    perm_int = mper.calculate_permission_integer(permissions)
    print(f"パーミッション整数値: {perm_int}")

    # 招待URLを作成
    url = mper.create_invite_link(
        client_id="123456789012345678",
        permissions=perm_int,
    )
    print(f"招待URL: {url}")
    print()

    # =====================================================
    # カスタムスコープを指定
    # =====================================================
    url_with_scopes = mper.create_invite_link(
        client_id="123456789012345678",
        permissions=perm_int,
        scopes=['bot', 'applications.commands', 'identify']
    )
    print(f"カスタムスコープ付きURL: {url_with_scopes}")
    print()

    # =====================================================
    # 利用可能なパーミッション一覧を取得
    # =====================================================
    print("=== 利用可能なパーミッション一覧 ===")
    all_perms = mper.get_all_permission_names()
    for perm in sorted(all_perms):
        value = mper.get_permission_value(perm)
        print(f"  {perm}: {value} ({hex(value)})")


if __name__ == "__main__":
    main()
