# Discord Permission Flags
# Based on Discord API Documentation (2025-12-22)
# https://discord.com/developers/docs/topics/permissions

from typing import Dict, List, Optional, Set, Tuple

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

# =============================================================================
# METHOD-TO-PERMISSION MAPPINGS (PRIMARY DETECTION SOURCE)
# =============================================================================
# These mappings are based on discord.py 2.6.4 documentation and Discord API.
# Format: "receiver.method" or "method" -> (permissions, confidence, notes)
# Confidence: "high" = documented requirement, "medium" = likely, "low" = context-dependent

# High-confidence mappings with receiver context
# Format: "receiver.method" -> (permissions_list, confidence, description)
METHOD_PERMISSION_RULES: Dict[str, Tuple[List[str], str, str]] = {
    # Member operations (high confidence - documented)
    "member.ban": (["ban_members"], "high", "Ban a member from the guild"),
    "member.unban": (["ban_members"], "high", "Unban a member from the guild"),
    "guild.ban": (["ban_members"], "high", "Ban a user from the guild"),
    "guild.unban": (["ban_members"], "high", "Unban a user from the guild"),
    "member.kick": (["kick_members"], "high", "Kick a member from the guild"),
    "guild.kick": (["kick_members"], "high", "Kick a user from the guild"),
    "member.timeout": (["moderate_members"], "high", "Timeout a member"),

    # Role operations (high confidence - documented)
    "member.add_roles": (["manage_roles"], "high", "Add roles to a member"),
    "member.remove_roles": (["manage_roles"], "high", "Remove roles from a member"),
    "guild.create_role": (["manage_roles"], "high", "Create a new role"),
    "role.delete": (["manage_roles"], "high", "Delete a role"),
    "role.edit": (["manage_roles"], "high", "Edit a role"),

    # Channel operations (high confidence - documented)
    "guild.create_text_channel": (["manage_channels"], "high", "Create a text channel"),
    "guild.create_voice_channel": (["manage_channels"], "high", "Create a voice channel"),
    "guild.create_category": (["manage_channels"], "high", "Create a category"),
    "guild.create_stage_channel": (["manage_channels"], "high", "Create a stage channel"),
    "guild.create_forum": (["manage_channels"], "high", "Create a forum channel"),
    "channel.delete": (["manage_channels"], "high", "Delete a channel"),
    "channel.edit": (["manage_channels"], "medium", "Edit channel settings"),
    "channel.clone": (["manage_channels"], "high", "Clone a channel"),
    "channel.set_permissions": (["manage_roles"], "high", "Set channel permission overwrites"),

    # Message operations (high confidence - documented)
    "channel.purge": (["manage_messages", "read_message_history"], "high", "Bulk delete messages"),
    "message.pin": (["manage_messages"], "high", "Pin a message"),
    "message.unpin": (["manage_messages"], "high", "Unpin a message"),
    "message.clear_reactions": (["manage_messages"], "high", "Clear all reactions"),
    "message.publish": (["send_messages", "manage_messages"], "high", "Publish announcement message"),

    # Webhook operations (high confidence - documented)
    "channel.create_webhook": (["manage_webhooks"], "high", "Create a webhook"),
    "channel.webhooks": (["manage_webhooks"], "high", "List channel webhooks"),
    "guild.webhooks": (["manage_webhooks"], "high", "List guild webhooks"),
    "webhook.delete": (["manage_webhooks"], "high", "Delete a webhook"),
    "webhook.edit": (["manage_webhooks"], "high", "Edit a webhook"),

    # Thread operations (high confidence - documented)
    "channel.create_thread": (["create_public_threads"], "high", "Create a public thread"),
    "thread.delete": (["manage_threads"], "high", "Delete a thread"),
    "thread.edit": (["manage_threads"], "medium", "Edit thread settings"),
    "thread.archive": (["manage_threads"], "high", "Archive a thread"),
    "thread.unarchive": (["manage_threads"], "high", "Unarchive a thread"),

    # Voice operations (high confidence - documented)
    "member.move_to": (["move_members"], "high", "Move member to voice channel"),

    # Invite operations (high confidence - documented)
    "channel.create_invite": (["create_instant_invite"], "high", "Create an invite"),
    "guild.invites": (["manage_guild"], "high", "List guild invites"),
    "guild.vanity_invite": (["manage_guild"], "high", "Get vanity invite"),

    # Audit log operations (high confidence - documented)
    "guild.audit_logs": (["view_audit_log"], "high", "View audit logs"),
    "guild.fetch_audit_logs": (["view_audit_log"], "high", "Fetch audit logs"),

    # Emoji/Sticker operations (high confidence - documented)
    "guild.create_custom_emoji": (["manage_guild_expressions"], "high", "Create custom emoji"),
    "guild.delete_emoji": (["manage_guild_expressions"], "high", "Delete custom emoji"),
    "emoji.delete": (["manage_guild_expressions"], "high", "Delete custom emoji"),
    "emoji.edit": (["manage_guild_expressions"], "high", "Edit custom emoji"),
    "guild.create_sticker": (["manage_guild_expressions"], "high", "Create sticker"),
    "sticker.delete": (["manage_guild_expressions"], "high", "Delete sticker"),
    "sticker.edit": (["manage_guild_expressions"], "high", "Edit sticker"),

    # Event operations (high confidence - documented)
    "guild.create_scheduled_event": (["manage_events"], "high", "Create scheduled event"),
    "scheduledevent.delete": (["manage_events"], "high", "Delete scheduled event"),
    "scheduledevent.edit": (["manage_events"], "high", "Edit scheduled event"),

    # Guild operations (high confidence - documented)
    "guild.edit": (["manage_guild"], "high", "Edit guild settings"),
    "guild.create_template": (["manage_guild"], "high", "Create guild template"),
    "guild.prune_members": (["kick_members"], "high", "Prune inactive members"),
    "guild.fetch_ban": (["ban_members"], "high", "Fetch ban info"),
    "guild.bans": (["ban_members"], "high", "List guild bans"),
}

# Simple method name mappings (used when chain detection fails)
# Format: "method" -> (permissions_list, confidence, description)
SIMPLE_METHOD_PERMISSIONS: Dict[str, Tuple[List[str], str, str]] = {
    # High confidence even without receiver context
    "ban": (["ban_members"], "high", "Ban operation"),
    "unban": (["ban_members"], "high", "Unban operation"),
    "kick": (["kick_members"], "high", "Kick operation"),
    "timeout": (["moderate_members"], "high", "Timeout operation"),
    "purge": (["manage_messages", "read_message_history"], "high", "Bulk delete messages"),
    "pin": (["manage_messages"], "high", "Pin message"),
    "unpin": (["manage_messages"], "high", "Unpin message"),
    "clear_reactions": (["manage_messages"], "high", "Clear reactions"),
    "add_roles": (["manage_roles"], "high", "Add roles"),
    "remove_roles": (["manage_roles"], "high", "Remove roles"),
    "create_role": (["manage_roles"], "high", "Create role"),
    "create_webhook": (["manage_webhooks"], "high", "Create webhook"),
    "create_invite": (["create_instant_invite"], "high", "Create invite"),
    "audit_logs": (["view_audit_log"], "high", "View audit logs"),
    "fetch_audit_logs": (["view_audit_log"], "high", "Fetch audit logs"),
    "prune_members": (["kick_members"], "high", "Prune members"),
    "move_to": (["move_members"], "high", "Move to voice channel"),
    "set_permissions": (["manage_roles"], "high", "Set channel permissions"),

    # Medium confidence - context dependent
    "send": (["send_messages"], "medium", "Send message (guild channels only)"),
    "delete": (["manage_messages"], "low", "Delete message (others' messages only)"),
    "create_thread": (["create_public_threads"], "medium", "Create thread"),
    "archive": (["manage_threads"], "medium", "Archive thread"),
    "unarchive": (["manage_threads"], "medium", "Unarchive thread"),

    # Channel creation
    "create_text_channel": (["manage_channels"], "high", "Create text channel"),
    "create_voice_channel": (["manage_channels"], "high", "Create voice channel"),
    "create_category": (["manage_channels"], "high", "Create category"),
    "create_stage_channel": (["manage_channels"], "high", "Create stage channel"),
    "create_forum": (["manage_channels"], "high", "Create forum"),

    # Emoji/Sticker
    "create_custom_emoji": (["manage_guild_expressions"], "high", "Create emoji"),
    "delete_emoji": (["manage_guild_expressions"], "high", "Delete emoji"),
    "create_sticker": (["manage_guild_expressions"], "high", "Create sticker"),
    "delete_sticker": (["manage_guild_expressions"], "high", "Delete sticker"),

    # Events
    "create_scheduled_event": (["manage_events"], "high", "Create event"),
    "delete_scheduled_event": (["manage_events"], "high", "Delete event"),

    # Reactions
    "add_reaction": (["add_reactions", "read_message_history"], "medium", "Add reaction"),
}

# member.edit() keyword argument to permission mapping
MEMBER_EDIT_KWARGS_PERMISSIONS: Dict[str, Tuple[str, str]] = {
    "nick": ("manage_nicknames", "Change member nickname"),
    "mute": ("mute_members", "Server mute member"),
    "deafen": ("deafen_members", "Server deafen member"),
    "suppress": ("mute_members", "Suppress in stage channel"),
    "roles": ("manage_roles", "Change member roles"),
    "voice_channel": ("move_members", "Move to voice channel"),
    "timed_out_until": ("moderate_members", "Timeout member"),
    "bypass_verification": ("moderate_members", "Bypass verification"),
}

# Receiver type hints for better chain detection
RECEIVER_TYPE_HINTS = {
    "member": ["member", "author", "user", "target", "m"],
    "guild": ["guild", "server", "g"],
    "channel": ["channel", "ch", "text_channel", "voice_channel", "thread", "forum"],
    "message": ["message", "msg"],
    "role": ["role", "r"],
    "webhook": ["webhook", "wh"],
    "emoji": ["emoji", "e"],
    "sticker": ["sticker", "s"],
    "thread": ["thread", "t"],
    "scheduledevent": ["event", "scheduled_event"],
}

# Legacy compatibility - simple method name to permissions list
METHOD_TO_PERMISSIONS = {k: v[0] for k, v in SIMPLE_METHOD_PERMISSIONS.items()}

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


def get_permission_value(name: str) -> Optional[int]:
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


def get_permissions_from_method(
    method_name: str,
    receiver_hint: str = None
) -> Tuple[List[str], str, str]:
    """
    Get likely required permissions for a discord.py method call.

    Args:
        method_name: The method name (e.g., "ban", "kick", "send")
        receiver_hint: Optional hint about the receiver type (e.g., "member", "guild")

    Returns:
        Tuple of (permissions_list, confidence, description)
    """
    # Try chain-based lookup first
    if receiver_hint:
        chain_key = f"{receiver_hint.lower()}.{method_name}"
        if chain_key in METHOD_PERMISSION_RULES:
            return METHOD_PERMISSION_RULES[chain_key]

    # Fall back to simple method name lookup
    if method_name in SIMPLE_METHOD_PERMISSIONS:
        return SIMPLE_METHOD_PERMISSIONS[method_name]

    return ([], "none", "")


def get_member_edit_permissions(kwargs: List[str]) -> List[Tuple[str, str, str]]:
    """
    Get permissions required for member.edit() based on kwargs.

    Args:
        kwargs: List of keyword argument names passed to member.edit()

    Returns:
        List of (permission, confidence, description) tuples
    """
    results = []
    for kwarg in kwargs:
        if kwarg in MEMBER_EDIT_KWARGS_PERMISSIONS:
            perm, desc = MEMBER_EDIT_KWARGS_PERMISSIONS[kwarg]
            results.append((perm, "high", desc))
    return results


def infer_receiver_type(name: str) -> Optional[str]:
    """
    Try to infer the receiver type from a variable name.

    Args:
        name: Variable name (e.g., "member", "ctx.author", "target_user")

    Returns:
        Receiver type hint (e.g., "member", "guild") or None
    """
    name_lower = name.lower()
    for receiver_type, hints in RECEIVER_TYPE_HINTS.items():
        for hint in hints:
            if hint in name_lower:
                return receiver_type
    return None


def calculate_permission_integer(permission_names: Set[str]) -> int:
    """Calculate the combined permission integer from a set of permission names."""
    total = 0
    for name in permission_names:
        value = get_permission_value(name)
        if value is not None:
            total |= value
    return total


def get_all_permission_names() -> List[str]:
    """Get all canonical permission names."""
    return list(PERMISSIONS.keys())


def resolve_permission_name(name: str) -> Optional[str]:
    """Resolve a permission name to its canonical form."""
    name_lower = name.lower()
    if name_lower in PERMISSIONS:
        return name_lower
    if name_lower in PERMISSION_ALIASES:
        return PERMISSION_ALIASES[name_lower]
    return None


# Legacy compatibility - keep the old 'permissions' dict name
# but point to the new PERMISSIONS
permissions = PERMISSIONS
