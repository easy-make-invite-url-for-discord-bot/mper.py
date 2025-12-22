"""
mper.py - Discord Bot Permission Scanner

Scans Python code to detect required Discord permissions and generates
bot invite links with the appropriate permission bits.

Detection methods:
1. Decorator-based detection (primary, most accurate):
   - @commands.has_permissions(...) - User permission requirements
   - @commands.bot_has_permissions(...) - Bot permission requirements
   - @commands.has_guild_permissions(...) - User guild permission requirements
   - @commands.bot_has_guild_permissions(...) - Bot guild permission requirements
   - @app_commands.checks.has_permissions(...) - App command user permissions
   - @app_commands.checks.bot_has_permissions(...) - App command bot permissions
   - @app_commands.default_permissions(...) - Default command permissions
   - @commands.check_any(...) - Nested permission checks
   - @commands.check(...) - Custom permission checks with guild_permissions

2. Permission object detection:
   - discord.Permissions(...) - Permission object construction
   - Permissions.update(...) - Permission updates
   - PermissionOverwrite(...) - Channel permission overwrites
   - guild_permissions.<perm> / permissions_for(...).<perm> - Permission attribute access

3. Method-based heuristics (secondary, best-effort):
   - Maps discord.py method calls to likely required permissions
   - e.g., .ban() -> ban_members, .kick() -> kick_members
"""

import os
import argparse
import ast
import sys
from typing import Set, Dict, List, Any

from .permissions import (
    PERMISSIONS,
    PERMISSION_ALIASES,
    METHOD_TO_PERMISSIONS,
    PERMISSION_DECORATORS,
    APP_COMMAND_PERMISSION_DECORATORS,
    BOT_PERMISSION_DECORATORS,
    APP_COMMAND_BOT_PERMISSION_DECORATORS,
    WRAPPER_DECORATORS,
    PERMISSION_CLASSES,
    PERMISSION_ATTRIBUTES,
    get_permission_value,
    calculate_permission_integer,
)

# Directories to exclude by default
DEFAULT_EXCLUDE_DIRS = {
    '.venv',
    'venv',
    '.env',
    'env',
    '__pycache__',
    '.git',
    '.hg',
    '.svn',
    'node_modules',
    'site-packages',
    'dist-packages',
    '.tox',
    '.nox',
    '.pytest_cache',
    '.mypy_cache',
    'build',
    'dist',
    'egg-info',
}


class PermissionVisitor(ast.NodeVisitor):
    """AST visitor to extract permission requirements from Python code."""
    
    def __init__(self):
        # Separate user and bot permissions for clarity
        self.user_permissions: Set[str] = set()  # User permission requirements
        self.bot_permissions: Set[str] = set()   # Bot permission requirements
        self.inferred_permissions: Set[str] = set()  # From method calls (heuristic)
        self.permission_objects: Set[str] = set()  # From Permissions() construction
        self.attribute_permissions: Set[str] = set()  # From guild_permissions.X access
        self.warnings: List[str] = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to check for permission decorators."""
        self._check_decorators(node.decorator_list)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions to check for permission decorators."""
        self._check_decorators(node.decorator_list)
        self.generic_visit(node)
    
    def _check_decorators(self, decorators: List[ast.expr]) -> None:
        """Check decorators for permission declarations."""
        for decorator in decorators:
            self._extract_permissions_from_decorator(decorator)
    
    def _extract_permissions_from_decorator(self, decorator: ast.expr, is_bot: bool = False) -> None:
        """Extract permission names from a decorator, recursively handling nested decorators."""
        if isinstance(decorator, ast.Call):
            decorator_name = self._get_decorator_name(decorator.func)
            
            # Check for wrapper decorators that may contain nested permission checks
            if decorator_name in WRAPPER_DECORATORS:
                # Recursively check all arguments for nested permission decorators
                for arg in decorator.args:
                    self._extract_permissions_from_decorator(arg, is_bot)
                # Also check keyword arguments
                for keyword in decorator.keywords:
                    if keyword.value:
                        self._extract_permissions_from_decorator(keyword.value, is_bot)
                return
            
            # Determine if this is a bot or user permission decorator
            is_bot_decorator = (
                decorator_name in BOT_PERMISSION_DECORATORS or
                decorator_name in APP_COMMAND_BOT_PERMISSION_DECORATORS
            )
            is_user_decorator = (
                decorator_name in PERMISSION_DECORATORS or
                decorator_name in APP_COMMAND_PERMISSION_DECORATORS or
                decorator_name == 'default_permissions'
            )
            
            if is_bot_decorator or is_user_decorator:
                # Extract keyword arguments (permission names)
                for keyword in decorator.keywords:
                    if keyword.arg is not None:
                        perm_name = keyword.arg.lower()
                        # Check if the value is True (or a truthy constant)
                        if self._is_truthy_value(keyword.value):
                            if is_bot_decorator:
                                self._add_permission(perm_name, self.bot_permissions)
                            else:
                                self._add_permission(perm_name, self.user_permissions)
    
    def _is_truthy_value(self, node: ast.expr) -> bool:
        """Check if an AST node represents a truthy value."""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        elif isinstance(node, ast.NameConstant):  # Python 3.7 compat
            return bool(node.value)
        elif isinstance(node, ast.Name):
            # Variable reference - assume it might be True
            return True
        return True  # Default to True for complex expressions
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get the name of a decorator from its AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle commands.has_permissions, app_commands.checks.has_permissions, etc.
            return node.attr
        return ""
    
    def _add_permission(self, perm_name: str, target_set: Set[str]) -> None:
        """Add a permission to the target set, resolving aliases if needed."""
        perm_lower = perm_name.lower()
        
        if perm_lower in PERMISSIONS:
            target_set.add(perm_lower)
        elif perm_lower in PERMISSION_ALIASES:
            canonical = PERMISSION_ALIASES[perm_lower]
            target_set.add(canonical)
        else:
            self.warnings.append(f"Unknown permission: {perm_name}")
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect discord.py method usage and Permissions objects."""
        func_name = self._get_call_name(node.func)
        
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            # Check if this method maps to permissions (heuristic)
            if method_name in METHOD_TO_PERMISSIONS:
                perms = METHOD_TO_PERMISSIONS[method_name]
                for perm in perms:
                    self.inferred_permissions.add(perm)
            
            # Check for Permissions.update() calls
            if method_name == 'update':
                for keyword in node.keywords:
                    if keyword.arg and self._is_truthy_value(keyword.value):
                        self._add_permission(keyword.arg, self.permission_objects)
            
            # Check for discord.Permissions() or discord.PermissionOverwrite() construction
            if method_name in PERMISSION_CLASSES:
                for keyword in node.keywords:
                    if keyword.arg and self._is_truthy_value(keyword.value):
                        self._add_permission(keyword.arg, self.permission_objects)
        
        elif isinstance(node.func, ast.Name):
            # Check for Permissions() or PermissionOverwrite() construction (without module prefix)
            if func_name in PERMISSION_CLASSES:
                for keyword in node.keywords:
                    if keyword.arg and self._is_truthy_value(keyword.value):
                        self._add_permission(keyword.arg, self.permission_objects)
        
        self.generic_visit(node)
    
    def _get_call_name(self, node: ast.expr) -> str:
        """Get the name of a function call from its AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access to detect guild_permissions.X patterns."""
        # Check for patterns like: ctx.author.guild_permissions.manage_messages
        # or interaction.permissions.ban_members
        if isinstance(node.value, ast.Attribute):
            parent_attr = node.value.attr
            if parent_attr in PERMISSION_ATTRIBUTES:
                # The current node.attr is the permission being checked
                perm_name = node.attr.lower()
                if perm_name in PERMISSIONS or perm_name in PERMISSION_ALIASES:
                    self._add_permission(perm_name, self.attribute_permissions)
        
        self.generic_visit(node)
    
    @property
    def declared_permissions(self) -> Set[str]:
        """Combined declared permissions (for backward compatibility)."""
        return self.user_permissions | self.bot_permissions
    
    @property
    def all_detected_permissions(self) -> Set[str]:
        """All detected permissions from all sources."""
        return (
            self.user_permissions |
            self.bot_permissions |
            self.inferred_permissions |
            self.permission_objects |
            self.attribute_permissions
        )


def scan_file(file_path: str) -> Dict[str, Any]:
    """
    Scan a single Python file for permission requirements.
    
    Returns:
        Dictionary containing:
        - user_permissions: Set of user permission requirements (from @has_permissions)
        - bot_permissions: Set of bot permission requirements (from @bot_has_permissions)
        - inferred_permissions: Set of inferred permissions from method calls
        - permission_objects: Set of permissions from Permissions() construction
        - attribute_permissions: Set of permissions from guild_permissions.X access
        - warnings: List of warning messages
    """
    empty_result = {
        'user_permissions': set(),
        'bot_permissions': set(),
        'inferred_permissions': set(),
        'permission_objects': set(),
        'attribute_permissions': set(),
        'warnings': [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except (IOError, OSError) as e:
        empty_result['warnings'] = [f"Could not read file {file_path}: {e}"]
        return empty_result
    except UnicodeDecodeError as e:
        empty_result['warnings'] = [f"Encoding error in {file_path}: {e}"]
        return empty_result
    
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        empty_result['warnings'] = [f"Syntax error in {file_path}: {e}"]
        return empty_result
    
    visitor = PermissionVisitor()
    visitor.visit(tree)
    
    return {
        'user_permissions': visitor.user_permissions,
        'bot_permissions': visitor.bot_permissions,
        'inferred_permissions': visitor.inferred_permissions,
        'permission_objects': visitor.permission_objects,
        'attribute_permissions': visitor.attribute_permissions,
        'warnings': visitor.warnings,
    }


def scan_directory(
    directory: str,
    exclude_dirs: Set[str] = None,
    include_inferred: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Scan a directory for Discord permission requirements.
    
    Args:
        directory: Path to the directory to scan
        exclude_dirs: Set of directory names to exclude
        include_inferred: Whether to include inferred permissions from method calls
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary containing:
        - user_permissions: Set of user permission requirements
        - bot_permissions: Set of bot permission requirements (for invite link)
        - inferred_permissions: Set of inferred permissions from method calls
        - permission_objects: Set of permissions from Permissions() construction
        - attribute_permissions: Set of permissions from guild_permissions.X access
        - all_bot_permissions: Combined bot permissions for invite link
        - warnings: List of warning messages
        - files_scanned: Number of files scanned
        - files_with_errors: Number of files with errors
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    
    user_permissions: Set[str] = set()
    bot_permissions: Set[str] = set()
    inferred_permissions: Set[str] = set()
    permission_objects: Set[str] = set()
    attribute_permissions: Set[str] = set()
    all_warnings: List[str] = []
    files_scanned = 0
    files_with_errors = 0
    
    for root, dirs, files in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                files_scanned += 1
                
                if verbose:
                    print(f"Scanning: {file_path}")
                
                result = scan_file(file_path)
                
                user_permissions.update(result['user_permissions'])
                bot_permissions.update(result['bot_permissions'])
                inferred_permissions.update(result['inferred_permissions'])
                permission_objects.update(result['permission_objects'])
                attribute_permissions.update(result['attribute_permissions'])
                
                if result['warnings']:
                    files_with_errors += 1
                    all_warnings.extend(result['warnings'])
    
    # Calculate bot permissions for invite link
    # Bot permissions = explicit bot_has_permissions + inferred (if enabled)
    all_bot_permissions = bot_permissions.copy()
    if include_inferred:
        all_bot_permissions.update(inferred_permissions)
    
    # For backward compatibility
    declared_permissions = user_permissions | bot_permissions
    
    return {
        'user_permissions': user_permissions,
        'bot_permissions': bot_permissions,
        'inferred_permissions': inferred_permissions,
        'permission_objects': permission_objects,
        'attribute_permissions': attribute_permissions,
        'declared_permissions': declared_permissions,  # backward compat
        'all_bot_permissions': all_bot_permissions,
        'warnings': all_warnings,
        'files_scanned': files_scanned,
        'files_with_errors': files_with_errors,
    }


def calculate_permissions(permission_names: Set[str]) -> int:
    """Calculate the combined permission integer from permission names."""
    return calculate_permission_integer(permission_names)


def create_invite_link(
    client_id: str,
    permissions: int,
    scopes: List[str] = None
) -> str:
    """
    Create a Discord bot invite link.
    
    Args:
        client_id: The bot's client ID
        permissions: The permission integer
        scopes: List of OAuth2 scopes (default: ['bot', 'applications.commands'])
    
    Returns:
        The invite URL
    """
    if scopes is None:
        scopes = ['bot', 'applications.commands']
    
    scope_str = '%20'.join(scopes)
    return f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions={permissions}&scope={scope_str}"


def write_invite_link_to_file(invite_link: str, file_path: str = 'bot_invite_url.txt') -> None:
    """Write the invite link to a file."""
    with open(file_path, 'a') as file:
        file.write(invite_link + '\n')


def format_permissions_report(result: Dict) -> str:
    """Format a human-readable permissions report."""
    lines = []
    lines.append("=" * 60)
    lines.append("Discord Bot Permission Scan Report")
    lines.append("=" * 60)
    lines.append("")
    
    lines.append(f"Files scanned: {result['files_scanned']}")
    lines.append(f"Files with errors: {result['files_with_errors']}")
    lines.append("")
    
    # Bot permissions (from @bot_has_permissions decorators)
    if result.get('bot_permissions'):
        lines.append("Bot Permissions (from @bot_has_permissions - for invite link):")
        for perm in sorted(result['bot_permissions']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    # User permissions (from @has_permissions decorators)
    if result.get('user_permissions'):
        lines.append("User Permissions (from @has_permissions - command requirements):")
        for perm in sorted(result['user_permissions']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    # Inferred permissions from method calls
    if result.get('inferred_permissions'):
        lines.append("Inferred Permissions (from method calls - best effort):")
        for perm in sorted(result['inferred_permissions']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    # Permissions from Permissions() objects
    if result.get('permission_objects'):
        lines.append("Permissions from Objects (Permissions(), PermissionOverwrite()):")
        for perm in sorted(result['permission_objects']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    # Permissions from attribute access
    if result.get('attribute_permissions'):
        lines.append("Permissions from Attribute Access (guild_permissions.X):")
        for perm in sorted(result['attribute_permissions']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    if result.get('warnings'):
        lines.append("Warnings:")
        for warning in result['warnings'][:10]:  # Limit to first 10
            lines.append(f"  - {warning}")
        if len(result['warnings']) > 10:
            lines.append(f"  ... and {len(result['warnings']) - 10} more warnings")
        lines.append("")
    
    # Calculate bot permissions for invite link
    bot_perms = result.get('all_bot_permissions', result.get('bot_permissions', set()))
    total_perms = calculate_permissions(bot_perms)
    lines.append("-" * 60)
    lines.append("Bot Invite Link Permissions (bot_has_permissions + inferred):")
    lines.append(f"  Permission Integer: {total_perms}")
    lines.append(f"  Permission Hex: 0x{total_perms:X}")
    lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Scan Discord bot code and generate invite links with required permissions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mper /path/to/bot 123456789012345678
  mper /path/to/bot 123456789012345678 --verbose
  mper /path/to/bot 123456789012345678 --no-inferred
  mper /path/to/bot 123456789012345678 --scope bot --scope applications.commands
        """
    )
    parser.add_argument('directory', type=str, help='Directory to scan')
    parser.add_argument('client_id', type=str, help='Client ID of the Discord bot')
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--no-inferred',
        action='store_true',
        help='Only use declared permissions (from decorators), ignore inferred permissions'
    )
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='*',
        default=[],
        help='Additional directories to exclude'
    )
    parser.add_argument(
        '--scope',
        type=str,
        nargs='*',
        default=['bot', 'applications.commands'],
        help='OAuth2 scopes for the invite link (default: bot applications.commands)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='bot_invite_url.txt',
        help='Output file for the invite link (default: bot_invite_url.txt)'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Print a detailed permissions report'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    # Build exclude set
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    exclude_dirs.update(args.exclude)
    
    # Scan directory
    result = scan_directory(
        args.directory,
        exclude_dirs=exclude_dirs,
        include_inferred=not args.no_inferred,
        verbose=args.verbose
    )
    
    # Calculate bot permissions for invite link
    # Use all_bot_permissions (bot_has_permissions + inferred if enabled)
    total_permissions = calculate_permissions(result['all_bot_permissions'])
    
    # Generate invite link
    invite_link = create_invite_link(args.client_id, total_permissions, args.scope)
    
    # Write to file
    write_invite_link_to_file(invite_link, args.output)
    
    # Output
    if args.report:
        print(format_permissions_report(result))
    
    print(f"Generated Discord invite link: {invite_link}")
    print(f"Invite link saved to: {args.output}")
    
    if result['warnings'] and not args.report:
        print(f"\nNote: {len(result['warnings'])} warning(s) encountered. Use --report for details.")


if __name__ == "__main__":
    main()
