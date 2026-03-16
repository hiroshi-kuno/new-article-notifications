# リポジトリ構成

プロジェクトのファイル構成を説明します。

## ディレクトリツリー

```
new-article-notifications/
├── .github/
│   └── workflows/
│       └── check-articles.yml       # GitHub Actions ワークフロー（毎時間実行）
│
├── config/
│   └── sources.json                 # 監視対象URL・webhook設定（ユーザーが編集）
│
├── src/
│   ├── __init__.py                  # パッケージ初期化
│   ├── config.py                    # 設定ローダー
│   ├── models.py                    # データモデル（Article, SourceState）
│   ├── notifications.py             # Discord通知
│   ├── scrapers.py                  # スクレイピングロジック
│   └── state_manager.py             # 状態の永続化
│
├── state/
│   └── {source-id}.json             # 状態ファイル（自動生成）
│
├── docs/                            # ドキュメント
│   ├── ARCHITECTURE.md              # アーキテクチャ詳細
│   ├── QUICKSTART.md                # クイックスタート
│   ├── REPOSITORY_STRUCTURE.md      # このファイル
│   ├── RSS_SUPPORT.md               # RSS対応について
│   ├── SLACK_SETUP.md               # Discord通知のセットアップ
│   ├── SUMMARY.md                   # プロジェクト概要
│   └── TESTING.md                   # テストガイド
│
├── tests/                           # テストスクリプト
│   ├── test_new_sites.py            # GIJN・Datawrapper のスクレイパーテスト
│   ├── test_notification_logic.py   # 通知ロジックのテスト
│   ├── test_nyt.py                  # NYTスクレイパーのテスト
│   ├── test_nyt_webhook.py          # NYT webhook通知のテスト
│   ├── test_representative.py       # 各サイト種別の代表ソーステスト
│   └── test_slack.py                # Discordデフォルトwebhookのテスト
│
├── check_articles.py                # メインエントリーポイント
├── requirements.txt                 # Python依存ライブラリ
├── README.md                        # メインドキュメント
├── CHANGELOG.md                     # 変更履歴
└── LICENSE                          # MITライセンス
```

## ファイル説明

### 設定ファイル

#### `config/sources.json` ⭐ ユーザーが編集するファイル

監視するURLと通知先を設定します。

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/reporter-name",
      "enabled": true,
      "webhook": "WEBHOOK_URL_NYT"
    }
  ]
}
```

**フィールド：**
- `url`: 監視対象のURL
- `enabled`: true/false で有効・無効を切り替え（削除不要）
- `webhook`: 通知先のwebhook環境変数名（省略時は `DISCORD_WEBHOOK_URL` を使用）

### ソースコード

#### `check_articles.py`

メインのオーケストレーションスクリプト：
- 設定の読み込み
- StateManager の初期化
- 各ソースのチェック
- エラーのグレースフルな処理
- 詳細ログの出力
- 状態の保存
- 適切な終了コードの返却

#### `src/config.py`

設定管理：
- `sources.json` の読み込み
- 有効なソースのフィルタリング
- URLからの source_id 抽出

#### `src/models.py`

Pythonデータクラスによるモデル定義：

- `Article`: ニュース記事
  - `title`: タイトル
  - `url`: URL（同一性の判定に使用）
  - `published_time`: 公開日時

- `SourceState`: ソースの状態
  - `source_id`: ソースID
  - `last_article`: 前回の記事
  - `last_checked`: 最終チェック日時
  - `etag` / `last_modified`: HTTPキャッシュヘッダー
  - `error_count` / `last_error`: エラー情報

#### `src/state_manager.py`

状態の永続化レイヤー：
- JSONファイルの読み書き
- `state/` ディレクトリの自動作成
- 欠損・破損ファイルのハンドリング
- タイムスタンプの自動更新

#### `src/scrapers.py`

スクレイピングロジック：

| クラス | 用途 |
|---|---|
| `NYTReporterScraper` | NYT記者ページ（HTML解析、複数パース戦略） |
| `RSSScraper` | RSSフィード（feedparserによるXML解析） |
| `GenericHTMLScraper` | その他HTMLページ（GIJN, Datawrapper, Reuters等） |

`get_scraper(url)` ファクトリ関数がURLからスクレイパーを自動選択します。
新しいサイトは `_GENERIC_HTML_DOMAINS` に追加するだけで対応できます。

#### `src/notifications.py`

Discord通知：
- `WEBHOOK_URL_*` 環境変数を自動収集
- `sources.json` の `webhook` フィールドで通知先を選択
- デフォルトは `DISCORD_WEBHOOK_URL`

### GitHub Actions

#### `.github/workflows/check-articles.yml`

自動ワークフロー：
- **トリガー**: 毎時間（`0 * * * *`）+ 手動実行
- **環境変数**: `DISCORD_WEBHOOK_URL`, `WEBHOOK_URL_NYT`, `WEBHOOK_URL_WAPO`, `WEBHOOK_URL_BLOG`
- **権限**: `contents: write`（状態ファイルのコミットに必要）

### 状態ファイル

#### `state/{source-id}.json`（自動生成）

チェックのたびに更新されます。Gitにコミットされることで永続化されます。

```json
{
  "source_id": "agnes-chang",
  "last_article": {
    "title": "記事タイトル",
    "url": "https://www.nytimes.com/...",
    "published_time": "2025-01-28T10:00:00Z"
  },
  "last_checked": "2025-01-28T15:30:00Z",
  "etag": "W/\"abc123\"",
  "last_modified": "Mon, 28 Jan 2025 10:00:00 GMT",
  "error_count": 0,
  "last_error": null
}
```

## 依存ライブラリ

### ランタイム

| ライブラリ | 用途 |
|---|---|
| Python 3.11+ | 言語ランタイム |
| requests | HTTPクライアント |
| beautifulsoup4 | HTMLパース |
| feedparser | RSSフィードのパース |

### 外部サービス

| サービス | 用途 |
|---|---|
| GitHub Actions | 自動実行プラットフォーム |
| Git | バージョン管理 & 状態ストレージ |
| Discord Webhooks | 通知の送信先 |

## Gitワークフロー

### コミットパターン

```
ユーザーによるコミット:
- "Add new reporter: Agnes Chang"
- "Update scraper parsing strategy"
- "Add WEBHOOK_URL_XXX for new source"

botによるコミット:
- "Update article check state [skip ci]"
```

### 状態ストレージにGitを使う理由

1. **無料**: データベース不要
2. **永続性**: Git履歴がバックアップになる
3. **監査可能**: 状態変化の履歴が全て残る
4. **シンプル**: 外部サービス不要
5. **可搬性**: どこでも動作する

## 拡張方法

### ソースの追加（コード変更不要）

`config/sources.json` に追加するだけ：
```json
{
  "url": "https://新しいサイト/記者ページ",
  "enabled": true,
  "webhook": "WEBHOOK_URL_XXX"
}
```

### 新しいwebhookの追加（コード変更不要）

1. `sources.json` に `"webhook": "WEBHOOK_URL_NEW"` を追加
2. GitHub Secrets に `WEBHOOK_URL_NEW` を追加
3. ワークフローの `env:` に追加

### 新しいサイト種別の追加

HTMLスクレイピングで対応できるサイトなら `_GENERIC_HTML_DOMAINS` に追加：

```python
_GENERIC_HTML_DOMAINS = ('gijn.org', 'datawrapper.de', 'reuters.com', 'newsite.com')
```

特殊なパースロジックが必要な場合は専用スクレイパークラスを作成します。
