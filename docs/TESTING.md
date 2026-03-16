# テストガイド

GitHub Actionsにデプロイする前にローカルでテストする方法を説明します。

## 事前準備

```bash
# Python 3.11以上
python3 --version

# 依存ライブラリのインストール
pip install -r requirements.txt
```

## ローカルテスト

### 1. 基本動作テスト

チェッカーを一度実行します：

```bash
python check_articles.py
```

正常な出力例：
```
############################################################
# New Article Notification Checker
# Started: 2025-01-28T15:30:00.000000Z
############################################################

Found 1 enabled source(s)

============================================================
Checking: agnes-chang
URL: https://www.nytimes.com/by/agnes-chang
============================================================
Fetching page...

Top article found:
  Title: [記事タイトル]
  URL: https://www.nytimes.com/...
  Published: 2025-01-28T...

  First check for this source - recording article

State saved successfully

############################################################
# Summary
############################################################

Total sources: 1
Successful: 1
Failed: 0

Completed: 2025-01-28T15:30:05.000000Z
```

### 2. 状態ファイルの確認

```bash
ls -la state/
cat state/agnes-chang.json
```

以下の内容が含まれているか確認：
- `source_id`
- `last_article`（title・URL・published_time）
- `last_checked` タイムスタンプ
- `etag` と `last_modified`（サーバーが返す場合）

### 3. 変化検知のテスト

もう一度実行します：

```bash
python check_articles.py
```

以下のどちらかが表示されるはずです：
```
  Page not modified (304), skipping parse
```
または：
```
  No change (same article as before)
```

### 4. 複数ソースのテスト

`config/sources.json` にソースを追加して実行：

```bash
python check_articles.py
```

すべてのソースがチェックされることを確認します。

### 5. エラーハンドリングのテスト

存在しないURLを追加して実行：

```json
{
  "url": "https://www.nytimes.com/by/this-does-not-exist-12345",
  "enabled": true
}
```

確認事項：
- エラーがログに記録される
- 他のソースは正常に処理される
- スクリプトがクラッシュしない

```bash
python check_articles.py
echo "終了コード: $?"
```

終了コードは 0 のはずです（全ソースが失敗した場合を除く）。

### 6. 無効化ソースのテスト

ソースを無効化：

```json
{
  "url": "https://www.nytimes.com/by/test",
  "enabled": false
}
```

そのソースがチェックされないことを確認します。

## 各コンポーネントのテスト

### テストスクリプト（tests/ ディレクトリ）

```bash
# NYTスクレイパーのテスト
python tests/test_nyt.py

# 通知ロジックのテスト
python tests/test_notification_logic.py

# 複数サイトのテスト（GIJN, Datawrapper）
python tests/test_new_sites.py

# 各サイト種別の代表ソースをテスト
python tests/test_representative.py

# Discordデフォルトwebhookのテスト（DISCORD_WEBHOOK_URLが必要）
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python tests/test_slack.py

# NYT専用webhookのテスト（WEBHOOK_URL_NYTが必要）
export WEBHOOK_URL_NYT="https://discord.com/api/webhooks/..."
python tests/test_nyt_webhook.py
```

### 設定読み込みのテスト

```python
from src.config import Config

config = Config()
sources = config.get_enabled_sources()
print(f"有効なソース数: {len(sources)}")
for source in sources:
    source_id = Config.extract_source_id(source['url'])
    webhook = source.get('webhook', 'デフォルト')
    print(f"  - {source_id}: webhook={webhook}")
```

### 状態管理のテスト

```python
from src.state_manager import StateManager
from src.models import Article

sm = StateManager()

state = sm.load_state("test-id")
print(f"状態: {state.source_id}")

article = Article(
    title="テスト記事",
    url="https://example.com/test",
    published_time="2025-01-28T10:00:00Z"
)

state.last_article = article
sm.save_state(state)

state2 = sm.load_state("test-id")
print(f"読み込んだ記事: {state2.last_article.title}")
```

### スクレイパーのテスト

```python
from src.scrapers import NYTReporterScraper

scraper = NYTReporterScraper()
url = "https://www.nytimes.com/by/agnes-chang"

try:
    article, etag, last_modified = scraper.scrape(url)
    if article:
        print(f"タイトル: {article.title}")
        print(f"URL: {article.url}")
        print(f"公開日時: {article.published_time}")
        print(f"ETag: {etag}")
    else:
        print("記事が見つからないか、ページが更新されていません")
except Exception as e:
    print(f"エラー: {e}")
```

## HTMLの手動デバッグ

スクレイピングが失敗する場合、HTMLを手動で確認します：

```python
import requests
from bs4 import BeautifulSoup

url = "https://www.nytimes.com/by/agnes-chang"
headers = {'User-Agent': 'Mozilla/5.0 (compatible; TestBot/1.0)'}

response = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

# デバッグ用にHTMLを保存
with open('debug.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("debug.html に保存しました")

# <ol>タグの確認
print("\n<ol> タグ:")
for ol in soup.find_all('ol')[:3]:
    print(f"  class={ol.get('class')}")

# 記事リンクの確認
print("\n記事リンク候補:")
links = soup.find_all('a', href=lambda x: x and '/2025/' in x)
for link in links[:5]:
    print(f"  {link.get('href')}")
    title = link.find(['h1', 'h2', 'h3'])
    if title:
        print(f"    タイトル: {title.get_text(strip=True)[:50]}...")
```

## GitHub Actionsのテスト

### 1. ワークフロー構文のチェック

```bash
# actionlintのインストール（macOS）
brew install actionlint

# 構文チェック
actionlint .github/workflows/check-articles.yml
```

### 2. actでローカル実行

```bash
# actのインストール（macOS）
brew install act

# ワークフロー実行
act workflow_dispatch
```

### 3. GitHubで手動実行

1. コードをGitHubにプッシュ
2. Actions タブ → **Check for New Articles**
3. **Run workflow** をクリック
4. 実行ログを確認

### 4. 状態の永続化を確認

初回実行後：

```bash
git pull
ls state/
cat state/*.json
```

確認事項：
- 状態ファイルが存在する
- 正しいデータが含まれている
- `github-actions[bot]` によってコミットされている

## トラブルシューティング

### ImportError / ModuleNotFoundError

```bash
# プロジェクトルートにいるか確認
pwd

# sys.path を確認
python -c "import sys; print(sys.path)"

# 明示的にパスを指定して実行
PYTHONPATH=. python check_articles.py
```

### HTTP 403 Forbidden

NYTのIPブロックの可能性があります：
1. 数分待ってから再実行
2. VPNを使用
3. リクエスト頻度が高すぎないか確認

### 記事が検出されない

DOMの構造が変わった可能性があります。上記のHTML手動デバッグを実行し、`src/scrapers.py` のパース戦略を更新してください。

### GitHub ActionsでStateがコミットされない

1. Settings → Actions → General → **Workflow permissions** を確認
2. **Read and write permissions** に設定
3. ワークフローに `permissions: contents: write` があるか確認

## パフォーマンステスト

複数ソースで実行時間を計測：

```bash
time python check_articles.py
```

10ソースで2秒の遅延を設定している場合、目安は20〜30秒です。
