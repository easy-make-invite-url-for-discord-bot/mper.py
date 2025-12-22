"""
mper.py - Discord Bot Permission Scanner

Scans Python code to detect required Discord permissions and generates
bot invite links with the appropriate permission bits.

Detection methods:
1. Decorator-based detection (primary, most accurate):
   - @commands.has_permissions(...)
   - @commands.bot_has_permissions(...)
   - @app_commands.checks.has_permissions(...)
   - @app_commands.default_permissions(...)

2. Method-based heuristics (secondary, best-effort):
   - Maps discord.py method calls to likely required permissions
   - e.g., .ban() -> ban_members, .kick() -> kick_members
"""

import os
import argparse
import ast
import sys
from typing import Set, Dict, List, Tuple

from .permissions import (
    PERMISSIONS,
    PERMISSION_ALIASES,
    METHOD_TO_PERMISSIONS,
    PERMISSION_DECORATORS,
    APP_COMMAND_PERMISSION_DECORATORS,
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
        self.declared_permissions: Set[str] = set()  # From decorators (explicit)
        self.inferred_permissions: Set[str] = set()  # From method calls (heuristic)
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
    
    def _extract_permissions_from_decorator(self, decorator: ast.expr) -> None:
        """Extract permission names from a decorator."""
        # Handle @commands.has_permissions(...) or @has_permissions(...)
        if isinstance(decorator, ast.Call):
            decorator_name = self._get_decorator_name(decorator.func)
            
            # Check if it's a permission decorator
            if decorator_name in PERMISSION_DECORATORS or \
               decorator_name in APP_COMMAND_PERMISSION_DECORATORS or \
               decorator_name == 'default_permissions':
                # Extract keyword arguments (permission names)
                for keyword in decorator.keywords:
                    if keyword.arg is not None:
                        perm_name = keyword.arg.lower()
                        # Check if the value is True (or a truthy constant)
                        if isinstance(keyword.value, ast.Constant):
                            if keyword.value.value:  # Only add if True
                                self._add_declared_permission(perm_name)
                        elif isinstance(keyword.value, ast.NameConstant):  # Python 3.7 compat
                            if keyword.value.value:
                                self._add_declared_permission(perm_name)
                        else:
                            # If it's not a constant, assume it might be True
                            self._add_declared_permission(perm_name)
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get the name of a decorator from its AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle commands.has_permissions, app_commands.checks.has_permissions, etc.
            return node.attr
        return ""
    
    def _add_declared_permission(self, perm_name: str) -> None:
        """Add a declared permission, resolving aliases if needed."""
        # Normalize the permission name
        perm_lower = perm_name.lower()
        
        # Check if it's a valid permission or alias
        if perm_lower in PERMISSIONS:
            self.declared_permissions.add(perm_lower)
        elif perm_lower in PERMISSION_ALIASES:
            canonical = PERMISSION_ALIASES[perm_lower]
            self.declared_permissions.add(canonical)
        else:
            self.warnings.append(f"Unknown permission: {perm_name}")
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect discord.py method usage."""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            # Check if this method maps to permissions
            if method_name in METHOD_TO_PERMISSIONS:
                perms = METHOD_TO_PERMISSIONS[method_name]
                for perm in perms:
                    self.inferred_permissions.add(perm)
        
        self.generic_visit(node)


def scan_file(file_path: str) -> Tuple[Set[str], Set[str], List[str]]:
    """
    Scan a single Python file for permission requirements.
    
    Returns:
        Tuple of (declared_permissions, inferred_permissions, warnings)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except (IOError, OSError) as e:
        return set(), set(), [f"Could not read file {file_path}: {e}"]
    except UnicodeDecodeError as e:
        return set(), set(), [f"Encoding error in {file_path}: {e}"]
    
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        return set(), set(), [f"Syntax error in {file_path}: {e}"]
    
    visitor = PermissionVisitor()
    visitor.visit(tree)
    
    return visitor.declared_permissions, visitor.inferred_permissions, visitor.warnings


def scan_directory(
    directory: str,
    exclude_dirs: Set[str] = None,
    include_inferred: bool = True,
    verbose: bool = False
) -> Dict[str, any]:
    """
    Scan a directory for Discord permission requirements.
    
    Args:
        directory: Path to the directory to scan
        exclude_dirs: Set of directory names to exclude
        include_inferred: Whether to include inferred permissions from method calls
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary containing:
        - declared_permissions: Set of explicitly declared permissions
        - inferred_permissions: Set of inferred permissions from method calls
        - all_permissions: Combined set of all permissions
        - warnings: List of warning messages
        - files_scanned: Number of files scanned
        - files_with_errors: Number of files with errors
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS
    
    declared_permissions: Set[str] = set()
    inferred_permissions: Set[str] = set()
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
                
                declared, inferred, warnings = scan_file(file_path)
                
                declared_permissions.update(declared)
                inferred_permissions.update(inferred)
                
                if warnings:
                    files_with_errors += 1
                    all_warnings.extend(warnings)
    
    # Combine permissions
    all_permissions = declared_permissions.copy()
    if include_inferred:
        all_permissions.update(inferred_permissions)
    
    return {
        'declared_permissions': declared_permissions,
        'inferred_permissions': inferred_permissions,
        'all_permissions': all_permissions,
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
    
    if result['declared_permissions']:
        lines.append("Declared Permissions (from decorators):")
        for perm in sorted(result['declared_permissions']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    if result['inferred_permissions']:
        lines.append("Inferred Permissions (from method calls - best effort):")
        for perm in sorted(result['inferred_permissions']):
            value = get_permission_value(perm)
            lines.append(f"  - {perm} (0x{value:X})")
        lines.append("")
    
    if result['warnings']:
        lines.append("Warnings:")
        for warning in result['warnings'][:10]:  # Limit to first 10
            lines.append(f"  - {warning}")
        if len(result['warnings']) > 10:
            lines.append(f"  ... and {len(result['warnings']) - 10} more warnings")
        lines.append("")
    
    total_perms = calculate_permissions(result['all_permissions'])
    lines.append(f"Total Permission Integer: {total_perms}")
    lines.append(f"Total Permission Hex: 0x{total_perms:X}")
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
    
    # Calculate permissions
    total_permissions = calculate_permissions(result['all_permissions'])
    
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
