# Discord Permission Flags
# Based on Discord API Documentation (2025-12-22)
# https://discord.com/developers/docs/topics/permissions

# All permissions with their bit values
PERMISSIONS = {
    # General Permissions
    "create_instant_invite": 1 << 0,
    "kick_members": 1 << 1,
    "ban_members": 1 << 2,
    "administrator": 1 << 3,
    "manage_channels": 1 << 4,
    "manage_guild": 1 << 5,
    "add_reactions": 1 << 6,
    "view_audit_log": 1 << 7,
    "priority_speaker": 1 << 8,
    "stream": 1 << 9,
    "view_channel": 1 << 10,
    "send_messages": 1 << 11,
    "send_tts_messages": 1 << 12,
    "manage_messages": 1 << 13,
    "embed_links": 1 << 14,
    "attach_files": 1 << 15,
    "read_message_history": 1 << 16,
    "mention_everyone": 1 << 17,
    "use_external_emojis": 1 << 18,
    "view_guild_insights": 1 << 19,
    "connect": 1 << 20,
    "speak": 1 << 21,
    "mute_members": 1 << 22,
    "deafen_members": 1 << 23,
    "move_members": 1 << 24,
    "use_vad": 1 << 25,
    "change_nickname": 1 << 26,
    "manage_nicknames": 1 << 27,
    "manage_roles": 1 << 28,
    "manage_webhooks": 1 << 29,
    "manage_guild_expressions": 1 << 30,
    "use_application_commands": 1 << 31,
    "request_to_speak": 1 << 32,
    "manage_events": 1 << 33,
    "manage_threads": 1 << 34,
    "create_public_threads": 1 << 35,
    "create_private_threads": 1 << 36,
    "use_external_stickers": 1 << 37,
    "send_messages_in_threads": 1 << 38,
    "use_embedded_activities": 1 << 39,
    "moderate_members": 1 << 40,
    "view_creator_monetization_analytics": 1 << 41,
    "use_soundboard": 1 << 42,
    "create_guild_expressions": 1 << 43,
    "create_events": 1 << 44,
    "use_external_sounds": 1 << 45,
    "send_voice_messages": 1 << 46,
    # Bits 47, 48 are reserved/unused
    "send_polls": 1 << 49,
    "use_external_apps": 1 << 50,
}

# Aliases for backward compatibility and common variations
PERMISSION_ALIASES = {
    # Old names -> canonical names
    "read_messages": "view_channel",
    "send_message": "send_messages",
    "external_emojis": "use_external_emojis",
    "external_stickers": "use_external_stickers",
    "manage_emojis": "manage_guild_expressions",
    "manage_emojis_and_stickers": "manage_guild_expressions",
    "manage_permissions": "manage_roles",
    "use_voice_activity": "use_vad",
    "go_live": "stream",
    "timeout_members": "moderate_members",
    "use_slash_commands": "use_application_commands",
}

# discord.py method names -> required permissions (heuristic mapping)
# These are best-effort guesses based on common usage patterns
METHOD_TO_PERMISSIONS = {
    # Member actions
    "ban": ["ban_members"],
    "unban": ["ban_members"],
    "kick": ["kick_members"],
    "timeout": ["moderate_members"],
    "edit": [],  # Context-dependent, handled separately
    
    # Message actions
    "send": ["send_messages"],
    "delete": [],  # Could be manage_messages for others' messages
    "purge": ["manage_messages", "read_message_history"],
    "pin": ["manage_messages"],
    "unpin": ["manage_messages"],
    "publish": ["send_messages", "manage_messages"],
    
    # Reaction actions
    "add_reaction": ["add_reactions"],
    "clear_reactions": ["manage_messages"],
    "remove_reaction": [],  # Own reactions don't need permission
    
    # Channel actions
    "create_text_channel": ["manage_channels"],
    "create_voice_channel": ["manage_channels"],
    "create_category": ["manage_channels"],
    "create_stage_channel": ["manage_channels"],
    "create_forum": ["manage_channels"],
    "delete_channel": ["manage_channels"],
    
    # Role actions
    "create_role": ["manage_roles"],
    "delete_role": ["manage_roles"],
    "add_roles": ["manage_roles"],
    "remove_roles": ["manage_roles"],
    
    # Webhook actions
    "create_webhook": ["manage_webhooks"],
    "delete_webhook": ["manage_webhooks"],
    "webhooks": ["manage_webhooks"],
    
    # Thread actions
    "create_thread": ["create_public_threads"],
    "archive": ["manage_threads"],
    "unarchive": ["manage_threads"],
    "join_thread": ["send_messages_in_threads"],
    
    # Voice actions
    "move_to": ["move_members"],
    "disconnect": ["move_members"],
    
    # Invite actions
    "create_invite": ["create_instant_invite"],
    "invites": ["manage_guild"],
    
    # Guild actions
    "fetch_audit_logs": ["view_audit_log"],
    "audit_logs": ["view_audit_log"],
    
    # Emoji/Sticker actions
    "create_custom_emoji": ["manage_guild_expressions"],
    "delete_emoji": ["manage_guild_expressions"],
    "create_sticker": ["manage_guild_expressions"],
    "delete_sticker": ["manage_guild_expressions"],
    
    # Event actions
    "create_scheduled_event": ["manage_events"],
    "delete_scheduled_event": ["manage_events"],
}

# Decorator names that indicate permission requirements (user-side)
PERMISSION_DECORATORS = [
    "has_permissions",
    "has_guild_permissions",
]

# Decorator names that indicate bot permission requirements
BOT_PERMISSION_DECORATORS = [
    "bot_has_permissions",
    "bot_has_guild_permissions",
]

# app_commands permission decorators (user-side)
APP_COMMAND_PERMISSION_DECORATORS = [
    "has_permissions",
]

# app_commands bot permission decorators
APP_COMMAND_BOT_PERMISSION_DECORATORS = [
    "bot_has_permissions",
]

# Decorators that can contain nested permission checks
WRAPPER_DECORATORS = [
    "check_any",
    "check",
]

# Permission object class names that may contain permission keywords
PERMISSION_CLASSES = [
    "Permissions",
    "PermissionOverwrite",
]

# Attribute names that indicate permission access
PERMISSION_ATTRIBUTES = [
    "guild_permissions",
    "permissions",
    "app_permissions",
    "resolved_permissions",
]


def get_permission_value(name: str) -> int | None:
    """Get the permission bit value for a given permission name."""
    name_lower = name.lower()
    
    # Check canonical names first
    if name_lower in PERMISSIONS:
        return PERMISSIONS[name_lower]
    
    # Check aliases
    if name_lower in PERMISSION_ALIASES:
        canonical = PERMISSION_ALIASES[name_lower]
        return PERMISSIONS.get(canonical)
    
    return None


def get_permissions_from_method(method_name: str) -> list[str]:
    """Get likely required permissions for a discord.py method call."""
    return METHOD_TO_PERMISSIONS.get(method_name, [])


def calculate_permission_integer(permission_names: set[str]) -> int:
    """Calculate the combined permission integer from a set of permission names."""
    total = 0
    for name in permission_names:
        value = get_permission_value(name)
        if value is not None:
            total |= value
    return total


def get_all_permission_names() -> list[str]:
    """Get all canonical permission names."""
    return list(PERMISSIONS.keys())


# Legacy compatibility - keep the old 'permissions' dict name
# but point to the new PERMISSIONS
permissions = PERMISSIONS
