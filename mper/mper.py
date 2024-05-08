import os
import argparse
import ast
from permissions import permissions

def scan_directory(directory):
    required_permissions = set()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=file)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                            if func_name in permissions:
                                required_permissions.add(permissions[func_name])
    return required_permissions

def calculate_permissions(required_permissions):
    total_permissions = 0
    for perm in required_permissions:
        total_permissions |= perm
    return total_permissions

def create_invite_link(client_id, permissions):
    return f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions={permissions}&scope=bot"

def write_invite_link_to_file(invite_link):
    file_path = 'bot_invite_url.txt'
    with open(file_path, 'a') as file:
        file.write(invite_link + '\n')

def main():
    parser = argparse.ArgumentParser(description="Generate a Discord bot invite link.")
    parser.add_argument('directory', type=str, help='Directory to scan')
    parser.add_argument('client_id', type=str, help='Client ID of the Discord bot')
    args = parser.parse_args()

    required_permissions = scan_directory(args.directory)
    total_permissions = calculate_permissions(required_permissions)
    invite_link = create_invite_link(args.client_id, total_permissions)
    write_invite_link_to_file(invite_link)
    print("Generated Discord invite link:", invite_link)

if __name__ == "__main__":
    main()