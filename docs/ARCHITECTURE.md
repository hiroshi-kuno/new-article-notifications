# アーキテクチャ

システムの内部構造を説明します。

## システム概要

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Actions                          │
│                  （スケジューラー / オーケストレーター）         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ 毎時間トリガー
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   check_articles.py                          │
│               （メインオーケストレーター）                      │
└─────┬───────────────────────────────────────────────────────┘
      │
      │ 読み込み
      ▼
┌─────────────────────────────────────────────────────────────┐
│                  config/sources.json                         │
│        （監視対象のURLリスト・webhook設定）                     │
└──────────────────────────────────────────────────────────────┘
      │
      │ ソースごとに処理
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    StateManager                              │
│                  （前回の状態を読み込み）                       │
│                                                              │
│  state/source-1.json ◄──┐                                   │
│  state/source-2.json    │ 読み書き                           │
│  state/source-3.json ◄──┘                                   │
└──────────────────────────────────────────────────────────────┘
      │
      │ 取得・解析
      ▼
┌─────────────────────────────────────────────────────────────┐
│                     各種スクレイパー                           │
│                                                              │
│  1. 条件付きHTTPリクエスト                                     │
│     If-None-Match: etag                                      │
│     If-Modified-Since: date                                  │
│                                                              │
│  2. 304 Not Modified の処理                                   │
│     └─> パースをスキップ                                       │
│                                                              │
│  3. HTML/XML パース                                           │
│     ├─> Strategy 1: <ol> リスト                              │
│     ├─> Strategy 2: <div> コンテナ                            │
│     └─> Strategy 3: フォールバック                             │
│                                                              │
│  4. Article オブジェクトの抽出                                  │
│     ├─> title                                                │
│     ├─> url                                                  │
│     └─> published_time                                       │
└──────────────────────────────────────────────────────────────┘
      │
      │ 比較
      ▼
┌─────────────────────────────────────────────────────────────┐
│                     変化検知                                  │
│                                                              │
│  IF article.url != state.last_article.url:                   │
│     新記事を検出！                                             │
│     └─> 状態を更新 & Discord通知                              │
│  ELSE:                                                       │
│     変化なし                                                  │
└──────────────────────────────────────────────────────────────┘
      │
      │ 保存
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    StateManager                              │
│                  （更新した状態を保存）                         │
└──────────────────────────────────────────────────────────────┘
      │
      │ コミット & プッシュ
      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Git リポジトリ                              │
│              （永続的な状態ストレージ）                         │
└──────────────────────────────────────────────────────────────┘
```

## コンポーネント詳細

### 1. check_articles.py（メインオーケストレーター）

**役割：**
- 設定の読み込み
- StateManager の初期化
- 有効なすべてのソースをループ処理
- ソースごとのエラー分離
- サマリーの出力
- 終了コードの返却

**エラーハンドリング：**
- 個別ソースの失敗がシステム全体をクラッシュさせない
- エラーはログに記録・カウント
- 全ソースが失敗した場合のみエラー終了

### 2. Config（src/config.py）

**役割：**
- `sources.json` の読み込み
- 有効なソースのフィルタリング
- URLからの source_id 自動抽出

**設定フォーマット：**
```json
{
  "sources": [
    {
      "url": "https://...",
      "enabled": true,
      "webhook": "WEBHOOK_URL_NYT"
    }
  ]
}
```

`webhook` フィールドで通知先のDiscord webhookを指定します。未指定の場合は `DISCORD_WEBHOOK_URL` にフォールバックします。

### 3. StateManager（src/state_manager.py）

**役割：**
- JSONファイルから状態を読み込み
- JSONファイルに状態を保存
- `state/` ディレクトリの自動作成
- 破損・欠損した状態ファイルの処理

**状態ファイルフォーマット：**
```json
{
  "source_id": "agnes-chang",
  "last_article": {
    "title": "...",
    "url": "...",
    "published_time": "..."
  },
  "last_checked": "2025-01-28T15:30:00Z",
  "etag": "W/\"abc123\"",
  "last_modified": "Mon, 28 Jan 2025 10:00:00 GMT",
  "error_count": 0,
  "last_error": null
}
```

### 4. Models（src/models.py）

**Article：**
```python
@dataclass
class Article:
    title: str
    url: str
    published_time: Optional[str]

    def __eq__(self, other):
        # URLが同じなら同一記事とみなす
        return self.url == other.url
```

**SourceState：**
```python
@dataclass
class SourceState:
    source_id: str
    last_article: Optional[Article]
    last_checked: Optional[str]
    etag: Optional[str]
    last_modified: Optional[str]
    error_count: int
    last_error: Optional[str]
```

### 5. Scrapers（src/scrapers.py）

使用するスクレイパーはURLから自動判別されます（`get_scraper()` ファクトリ関数）。

| URLパターン | スクレイパー |
|---|---|
| `/rss/` 含む・`.rss`/`.xml` 終わり | RSSScraper |
| `nytimes.com/by/` 含む | NYTReporterScraper |
| gijn.org / datawrapper.de / reuters.com | GenericHTMLScraper |

新しいサイトを追加する場合は `_GENERIC_HTML_DOMAINS` に追加するか、専用スクレイパークラスを作成します。

**共通機能：**
- 条件付きリクエスト（ETag / If-Modified-Since）
- 15秒タイムアウト
- リクエスト間2秒の遅延
- リトライなし（次回実行で再試行）

**NYTReporterScraper のパース戦略：**

| 戦略 | 対象 | 説明 |
|---|---|---|
| Strategy 1 | `<ol>` リスト | 年パターン付きリンクを探す（最も信頼性が高い） |
| Strategy 2 | `<div>`/`<section>`/`<article>` | 見出しタグを持つ記事リンクを探す |
| Strategy 3 | フォールバック | 任意の年パターンリンクを探す |

複数戦略を持つ理由：DOMの構造は変わりやすいため、堅牢性を高めるために複数のアプローチを試みます。

### 6. DiscordNotifier（src/notifications.py）

**webhook ルーティング：**

`WEBHOOK_URL_*` プレフィックスの環境変数を自動収集します。各ソースの `sources.json` に記載した `webhook` キーで通知先を指定します。

```python
# 環境変数の自動収集
self._webhooks = {
    key: value
    for key, value in os.environ.items()
    if key.startswith('WEBHOOK_URL_') and value
}
```

| sources.json の webhook 値 | 使用される環境変数 |
|---|---|
| `"WEBHOOK_URL_NYT"` | `WEBHOOK_URL_NYT` |
| `"WEBHOOK_URL_WAPO"` | `WEBHOOK_URL_WAPO` |
| `"WEBHOOK_URL_BLOG"` | `WEBHOOK_URL_BLOG` |
| 未指定 | `DISCORD_WEBHOOK_URL`（デフォルト） |

### 7. GitHub Actions ワークフロー

**トリガー：**
1. **スケジュール**: `cron: '0 * * * *'`（毎時間）
2. **手動**: workflow_dispatch

**ステップ：**
```yaml
1. コードのチェックアウト
2. Python 3.11 のセットアップ
3. 依存ライブラリのインストール（キャッシュあり）
4. check_articles.py の実行
5. 状態変更のコミット
6. リポジトリへのプッシュ
```

**コミット戦略：**
```bash
git add state/
if 変更あり:
    git commit -m "Update article check state [skip ci]"
    git push
```

`[skip ci]` タグにより、状態コミットが新たなワークフロー実行をトリガーしません（無限ループ防止）。

## データフロー

### 初回実行（コールドスタート）

```
1. 設定の読み込み
   └─> sources.json: [source1, source2]

2. source1 の処理:
   ├─> 状態の読み込み
   │   └─> ファイルなし → 空の状態を作成
   ├─> ページ取得（条件付きヘッダーなし）
   │   └─> HTTP 200 OK
   ├─> HTML パース → 記事 A を取得
   ├─> 比較
   │   └─> 前回の記事なし → ベースラインとして記録
   └─> 状態を保存: state/source1.json

3. 以降のソースも同様に処理

4. 状態ファイルをコミット & プッシュ
```

### 2回目以降の実行

```
1. 設定の読み込み
2. source1 の処理:
   ├─> 状態の読み込み: last_article = A
   ├─> ページ取得（etag / last-modified 付き）
   │   ├─> HTTP 304 → パースをスキップ
   │   └─> HTTP 200 → パース → 記事 B を取得
   ├─> 比較
   │   ├─> B == A → 変化なし
   │   └─> B != A → 新記事検出！→ Discord通知
   └─> 状態を保存: state/source1.json

3. 変更があればコミット
```

## 拡張ポイント

### 新しいスクレイパーの追加

1. スクレイパークラスを作成：
```python
class CustomScraper:
    def scrape(self, url, etag, last_modified):
        # スクレイピングロジックの実装
        return article, etag, last_modified
```

2. ファクトリに登録（`_GENERIC_HTML_DOMAINS` に追加 or 条件を追加）：
```python
_GENERIC_HTML_DOMAINS = ('gijn.org', 'datawrapper.de', 'reuters.com', 'example.com')
```

3. `sources.json` にソースを追加：
```json
{"url": "https://example.com/author/...", "enabled": true, "webhook": "WEBHOOK_URL_XXX"}
```

### 新しい通知先の追加

1. `sources.json` に `webhook` フィールドを指定：
```json
{"url": "...", "enabled": true, "webhook": "WEBHOOK_URL_NEW"}
```

2. GitHub Secrets に `WEBHOOK_URL_NEW` を追加

3. ワークフローの `env:` に追加：
```yaml
WEBHOOK_URL_NEW: ${{ secrets.WEBHOOK_URL_NEW }}
```

Pythonコードの変更は不要です。

## パフォーマンス

### 所要時間の目安

N ソース・遅延 D=2秒 の場合：
- 最良（全て304）: 約 2N 秒
- 最悪（全てパース): 約 2N + パース時間

10ソースの場合：最良 約20秒、最悪 約30秒

### メモリ

- BeautifulSoup は1ページずつ処理
- セッション再利用でメモリ節約
- HTMLのキャッシュなし

### ネットワーク

- 条件付きリクエストで帯域幅を節約
- セッションによるコネクションプール
- 記事本文の取得なし（見出し・URLのみ）

## セキュリティ

### Secretsの管理

- WebhookのURLは必ずGitHub Secretsで管理
- コードやコミットに含めない
- `WEBHOOK_URL_*` パターンの環境変数として設定

### レート制限への配慮

- リクエスト間に2秒の遅延
- アグレッシブなリトライなし
- User-Agentで明確にbot識別
- 304レスポンスを尊重
