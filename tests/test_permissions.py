"""
permissions.py のユニットテスト

パーミッション定数とユーティリティ関数のテスト。
"""

from mper.permissions import (
    PERMISSION_ALIASES,
    PERMISSIONS,
    calculate_permission_integer,
    get_all_permission_names,
    get_permission_value,
    get_permissions_from_method,
    infer_receiver_type,
    resolve_permission_name,
)


class TestPermissionConstants:
    """パーミッション定数のテスト"""

    def test_permissions_not_empty(self):
        """パーミッション辞書が空でないことを確認"""
        assert len(PERMISSIONS) > 0

    def test_common_permissions_exist(self):
        """主要なパーミッションが存在することを確認"""
        expected_permissions = [
            "send_messages",
            "ban_members",
            "kick_members",
            "manage_channels",
            "manage_roles",
            "administrator",
            "view_channel",
            "manage_messages",
        ]
        for perm in expected_permissions:
            assert perm in PERMISSIONS, f"{perm} がPERMISSIONSに存在しない"

    def test_permission_values_are_powers_of_two(self):
        """パーミッション値が2のべき乗であることを確認"""
        for name, value in PERMISSIONS.items():
            assert value > 0, f"{name} の値が0以下"
            assert (value & (value - 1)) == 0, f"{name} の値が2のべき乗でない: {value}"

    def test_permission_values_unique(self):
        """全てのパーミッション値がユニークであることを確認"""
        values = list(PERMISSIONS.values())
        assert len(values) == len(set(values)), "重複するパーミッション値が存在する"


class TestPermissionAliases:
    """パーミッションエイリアスのテスト"""

    def test_aliases_resolve_to_valid_permissions(self):
        """全てのエイリアスが有効なパーミッションに解決されることを確認"""
        for alias, canonical in PERMISSION_ALIASES.items():
            assert canonical in PERMISSIONS, f"エイリアス {alias} の参照先 {canonical} が無効"

    def test_common_aliases(self):
        """一般的なエイリアスが正しくマッピングされていることを確認"""
        assert PERMISSION_ALIASES.get("read_messages") == "view_channel"
        assert PERMISSION_ALIASES.get("manage_emojis") == "manage_guild_expressions"


class TestGetPermissionValue:
    """get_permission_value関数のテスト"""

    def test_valid_permission_name(self):
        """有効なパーミッション名からビット値を取得"""
        value = get_permission_value("send_messages")
        assert value == PERMISSIONS["send_messages"]

    def test_alias_permission_name(self):
        """エイリアス名からビット値を取得"""
        value = get_permission_value("read_messages")
        assert value == PERMISSIONS["view_channel"]

    def test_case_insensitive(self):
        """大文字小文字を区別しないことを確認"""
        assert get_permission_value("SEND_MESSAGES") == get_permission_value("send_messages")
        assert get_permission_value("Send_Messages") == get_permission_value("send_messages")

    def test_invalid_permission_name(self):
        """無効なパーミッション名でNoneを返す"""
        assert get_permission_value("invalid_permission") is None
        assert get_permission_value("") is None


class TestResolvePermissionName:
    """resolve_permission_name関数のテスト"""

    def test_canonical_name(self):
        """正規名はそのまま返される"""
        assert resolve_permission_name("send_messages") == "send_messages"
        assert resolve_permission_name("ban_members") == "ban_members"

    def test_alias_name(self):
        """エイリアスは正規名に解決される"""
        assert resolve_permission_name("read_messages") == "view_channel"
        assert resolve_permission_name("manage_emojis") == "manage_guild_expressions"

    def test_case_insensitive(self):
        """大文字小文字を区別しない"""
        assert resolve_permission_name("SEND_MESSAGES") == "send_messages"

    def test_invalid_name(self):
        """無効な名前はNoneを返す"""
        assert resolve_permission_name("not_a_permission") is None


class TestCalculatePermissionInteger:
    """calculate_permission_integer関数のテスト"""

    def test_empty_set(self):
        """空のセットは0を返す"""
        assert calculate_permission_integer(set()) == 0

    def test_single_permission(self):
        """単一パーミッションの計算"""
        result = calculate_permission_integer({"send_messages"})
        assert result == PERMISSIONS["send_messages"]

    def test_multiple_permissions(self):
        """複数パーミッションのOR結合"""
        perms = {"send_messages", "ban_members", "kick_members"}
        result = calculate_permission_integer(perms)
        expected = (
            PERMISSIONS["send_messages"] | PERMISSIONS["ban_members"] | PERMISSIONS["kick_members"]
        )
        assert result == expected

    def test_with_aliases(self):
        """エイリアスを含む場合も正しく計算"""
        result = calculate_permission_integer({"read_messages"})
        assert result == PERMISSIONS["view_channel"]

    def test_ignores_invalid_permissions(self):
        """無効なパーミッションは無視される"""
        result = calculate_permission_integer({"send_messages", "invalid_perm"})
        assert result == PERMISSIONS["send_messages"]


class TestGetAllPermissionNames:
    """get_all_permission_names関数のテスト"""

    def test_returns_list(self):
        """リストを返すことを確認"""
        names = get_all_permission_names()
        assert isinstance(names, list)

    def test_contains_all_permissions(self):
        """全てのパーミッションを含むことを確認"""
        names = get_all_permission_names()
        assert set(names) == set(PERMISSIONS.keys())


class TestGetPermissionsFromMethod:
    """get_permissions_from_method関数のテスト"""

    def test_known_method_with_receiver(self):
        """既知のメソッド+レシーバーでパーミッションを取得"""
        perms, confidence, desc = get_permissions_from_method("ban", "member")
        assert "ban_members" in perms
        assert confidence == "high"

    def test_known_method_without_receiver(self):
        """レシーバーなしでもパーミッションを取得"""
        perms, confidence, desc = get_permissions_from_method("kick")
        assert "kick_members" in perms

    def test_unknown_method(self):
        """未知のメソッドは空のリストを返す"""
        perms, confidence, desc = get_permissions_from_method("unknown_method")
        assert perms == []
        assert confidence == "none"

    def test_purge_returns_multiple_permissions(self):
        """purgeは複数のパーミッションを返す"""
        perms, confidence, desc = get_permissions_from_method("purge")
        assert "manage_messages" in perms
        assert "read_message_history" in perms


class TestInferReceiverType:
    """infer_receiver_type関数のテスト"""

    def test_member_hints(self):
        """メンバー関連のヒントを認識"""
        assert infer_receiver_type("member") == "member"
        assert infer_receiver_type("author") == "member"
        assert infer_receiver_type("target_user") == "member"

    def test_guild_hints(self):
        """ギルド関連のヒントを認識"""
        assert infer_receiver_type("guild") == "guild"
        assert infer_receiver_type("server") == "guild"

    def test_channel_hints(self):
        """チャンネル関連のヒントを認識"""
        assert infer_receiver_type("channel") == "channel"
        assert infer_receiver_type("text_channel") == "channel"

    def test_unknown_name(self):
        """未知の名前はNoneを返す"""
        assert infer_receiver_type("xyz") is None
        assert infer_receiver_type("") is None
