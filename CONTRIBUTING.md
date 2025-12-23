# コントリビューションガイド

mperへの貢献に興味を持っていただきありがとうございます！このガイドでは、プロジェクトへの貢献方法を説明します。

## 目次

- [行動規範](#行動規範)
- [貢献の方法](#貢献の方法)
- [開発環境のセットアップ](#開発環境のセットアップ)
- [コーディング規約](#コーディング規約)
- [コミットメッセージ](#コミットメッセージ)
- [プルリクエスト](#プルリクエスト)
- [リリースプロセス](#リリースプロセス)

## 行動規範

このプロジェクトでは、すべての参加者に敬意を持って接することを求めます。

- 建設的なフィードバックを心がける
- 他の貢献者を尊重する
- 多様な意見を歓迎する

## 貢献の方法

### バグ報告

バグを見つけた場合：

1. [既存のIssue](https://github.com/FreeWiFi7749/mper/issues)を確認し、重複がないか確認
2. 新しいIssueを作成し、[バグ報告テンプレート](.github/ISSUE_TEMPLATE/bug_report.yml)に従って記入

### 機能提案

新機能のアイデアがある場合：

1. [既存のIssue](https://github.com/FreeWiFi7749/mper/issues)を確認
2. [機能要望テンプレート](.github/ISSUE_TEMPLATE/feature_request.yml)を使用してIssueを作成

### コードの貢献

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 開発環境のセットアップ

### 必要条件

- Python 3.10以上
- Git

### セットアップ手順

```bash
# リポジトリをクローン
git clone https://github.com/FreeWiFi7749/mper.git
cd mper

# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 開発用依存関係をインストール
pip install -e ".[dev]"

# または手動でインストール
pip install -e .
pip install ruff mypy pytest pytest-cov
```

### 開発用コマンド

```bash
# Lintチェック
ruff check mper/

# フォーマットチェック
ruff format --check mper/

# フォーマット適用
ruff format mper/

# 型チェック
mypy mper/ --ignore-missing-imports

# テスト実行
pytest tests/ -v

# カバレッジ付きテスト
pytest tests/ --cov=mper --cov-report=html

# CLIテスト
mper examples/sample_bot 123456789012345678 --report
```

## コーディング規約

### 言語

- **コード**: 英語（変数名、関数名、クラス名）
- **ドキュメント**: 日本語（docstring、コメント、README）
- **コミットメッセージ**: 英語（Conventional Commits形式）

### スタイル

このプロジェクトでは[Ruff](https://docs.astral.sh/ruff/)を使用しています。

```python
# 良い例
def get_permission_value(name: str) -> Optional[int]:
    """
    パーミッション名からビット値を取得する。

    Args:
        name: パーミッション名

    Returns:
        ビット値、存在しない場合はNone
    """
    return PERMISSIONS.get(name.lower())


# 悪い例
def getPermissionValue(name):  # キャメルケース、型ヒントなし
    # コメントが英語
    return PERMISSIONS.get(name.lower())
```

### 型ヒント

すべての関数に型ヒントを付けてください：

```python
from typing import Optional, List, Set, Dict

def scan_file(file_path: str) -> Dict[str, Any]:
    ...

def calculate_permissions(permission_names: Set[str]) -> int:
    ...
```

### Docstring

Google形式のdocstringを日本語で記述してください：

```python
def create_invite_link(
    client_id: str,
    permissions: int,
    scopes: Optional[List[str]] = None,
) -> str:
    """
    Discord Bot招待リンクを生成する。

    Args:
        client_id: BotのクライアントID
        permissions: パーミッション整数
        scopes: OAuth2スコープのリスト

    Returns:
        招待URL

    Raises:
        ValueError: client_idが空の場合

    Example:
        >>> url = create_invite_link("123456789", 8)
        >>> print(url)
        https://discord.com/oauth2/authorize?...
    """
```

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/)形式を使用してください：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type

| Type | 説明 |
|------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `style` | コードの意味に影響しない変更（空白、フォーマット等） |
| `refactor` | バグ修正でも機能追加でもないコード変更 |
| `perf` | パフォーマンス改善 |
| `test` | テストの追加・修正 |
| `chore` | ビルドプロセスやツールの変更 |
| `ci` | CI設定の変更 |
| `deps` | 依存関係の更新 |

### 例

```bash
feat(cli): add --json option for machine-readable output

fix(scanner): handle async context managers correctly

docs: update README with new CLI options

refactor(permissions): simplify permission calculation logic

ci: add Python 3.13 to test matrix
```

## プルリクエスト

### PRの前に

- [ ] `ruff check mper/` がパスする
- [ ] `ruff format --check mper/` がパスする
- [ ] テストがパスする（`pytest tests/`）
- [ ] 必要に応じてドキュメントを更新
- [ ] コミットメッセージがConventional Commits形式

### PRテンプレート

PRを作成する際は、以下の情報を含めてください：

```markdown
## 概要
この変更の概要を記述

## 変更内容
- 変更点1
- 変更点2

## 関連Issue
Fixes #123

## チェックリスト
- [ ] Lintチェックがパスする
- [ ] テストを追加/更新した
- [ ] ドキュメントを更新した
```

### レビュープロセス

1. CIチェックがすべてパスすることを確認
2. メンテナーがコードをレビュー
3. 必要に応じて修正を依頼
4. 承認後、マージ

## リリースプロセス

メンテナー向けのリリース手順：

### 1. バージョン更新

```bash
# mper/__init__.py の __version__ を更新
# pyproject.toml の version を更新
```

### 2. CHANGELOGの確認

```bash
# git-cliffでプレビュー
git cliff --unreleased
```

### 3. タグの作成

```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### 4. 自動リリース

タグをプッシュすると、GitHub Actionsが自動的に：
- リリースノートを生成
- PyPIにパブリッシュ

## 質問・サポート

- **質問**: [Issueを作成](https://github.com/FreeWiFi7749/mper/issues/new?template=question.yml)
- **ディスカッション**: GitHub Discussionsを使用（有効な場合）

---

貢献をお待ちしています！ 🎉
