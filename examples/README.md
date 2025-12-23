# mper Examples / サンプルコード

## ファイル一覧

| ファイル | 説明 |
|----------|------|
| `basic_usage.py` | 基本的な使い方（ディレクトリスキャン、招待URL生成） |
| `custom_permissions.py` | パーミッション名を直接指定して招待URLを作成 |

## 実行方法

```bash
# mperをインストール
pip install mper

# サンプルを実行
python basic_usage.py
python custom_permissions.py
```

## クイックスタート

```python
import mper

# たった1行で招待URLを生成
url = mper.generate_invite_url("./your_bot", client_id="YOUR_CLIENT_ID")
print(url)
```
