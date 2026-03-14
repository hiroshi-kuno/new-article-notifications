# RSS Feed Support

このシステムはNYTの記者ページに加えて、RSSフィードの監視もサポートしています。

## 対応フォーマット

- **RSS 2.0**
- **Atom**
- その他 feedparser が対応する形式

## RSSフィードの追加方法

### 1. URLの追加

`config/sources.json` にRSSフィードのURLを追加するだけです：

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true
    },
    {
      "url": "https://www.washingtonpost.com/arcio/rss/author/Aaron-Steckelberg/",
      "enabled": true
    }
  ]
}
```

### 2. 自動判別

システムはURLから自動的にスクレイパーを選択します：

- **RSSフィード**: URLに `/rss/` が含まれる、または `.rss`/`.xml` で終わる
- **NYT記者ページ**: `nytimes.com/by/` が含まれる

## RSSフィードの利点

### 1. 安定性
- HTMLスクレイピングよりも構造が安定
- DOMの変更に影響されない
- パブリッシャーが公式にサポート

### 2. 効率性
- XMLパースはHTMLパースより高速
- 必要な情報が明確に構造化されている

### 3. 信頼性
- 公式のフィード形式
- 標準化されたフォーマット (RSS/Atom)

## 取得される情報

RSSフィードから以下の情報を抽出します：

- **タイトル** (`<title>`)
- **URL** (`<link>`)
- **公開時刻** (`<pubDate>`, `<published>`, `<updated>`)

## 対応サイト例

### Washington Post
```
https://www.washingtonpost.com/arcio/rss/author/{author-name}/
```

### The Guardian
```
https://www.theguardian.com/{section}/rss
https://www.theguardian.com/profile/{author}/rss
```

### Reuters
```
https://www.reuters.com/rssFeed/{section}
```

### BBC
```
https://feeds.bbci.co.uk/news/rss.xml
https://feeds.bbci.co.uk/news/{section}/rss.xml
```

## RSSフィードの見つけ方

### 方法1: ページのソースを確認

記者やセクションのページで、HTMLソース内を検索：

```html
<link rel="alternate" type="application/rss+xml" href="...">
```

### 方法2: 一般的なパターンを試す

多くのサイトは以下のパターンを使用：

```
/rss/
/feed/
/feeds/
/.rss
/rss.xml
/feed.xml
```

### 方法3: ブラウザ拡張機能

RSSフィードを自動検出するブラウザ拡張機能を使用：
- RSS Subscription Extension (Chrome)
- Awesome RSS (Firefox)

## 設定例

### 複数サイトの混在

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true
    },
    {
      "url": "https://www.washingtonpost.com/arcio/rss/author/Aaron-Steckelberg/",
      "enabled": true
    },
    {
      "url": "https://www.theguardian.com/profile/jane-doe/rss",
      "enabled": true
    },
    {
      "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
      "enabled": true
    }
  ]
}
```

## トラブルシューティング

### フィードが見つからない

```
Error: No scraper available for URL
```

**解決策**: URLに `/rss/` を含むか、`.rss`/`.xml` で終わるようにしてください。

### タイムアウトエラー

```
Request timeout after 15s
```

**原因**: サーバーの応答が遅い、または一時的に利用できない

**対処**:
1. 次回の実行で自動的に再試行されます
2. エラーは記録されますが、他のソースは継続されます
3. `error_count` が増加しますが、システムは停止しません

### 記事が検出されない

```
No article found or page not modified
```

**原因**:
- フィードが空
- フィードの形式が非標準
- 304 Not Modified (正常)

**確認**:
1. ブラウザでRSS URLを開いてXMLが表示されるか確認
2. `state/{source-id}.json` のエラーメッセージを確認
3. feedparserが対応する形式か確認

## 実装の詳細

### スクレイパークラス

`src/scrapers.py` の `RSSScraper` クラス:

```python
class RSSScraper:
    def fetch_feed(self, url, etag, last_modified):
        # 条件付きリクエスト (If-None-Match, If-Modified-Since)
        pass

    def parse_top_article(self, xml):
        # feedparserでXMLをパース
        # 最新のエントリを抽出
        pass

    def scrape(self, url, etag, last_modified):
        # フィード取得 → パース → 記事抽出
        pass
```

### 使用ライブラリ

- **feedparser**: RSSフィードの解析
  - RSS 1.0, RSS 2.0, Atom対応
  - 寛容なパーサー（エラーに強い）
  - 時刻の正規化

## パフォーマンス

### 条件付きリクエスト

RSSフィードでも `ETag` と `Last-Modified` ヘッダーをサポート：

```
GET /rss/feed.xml HTTP/1.1
If-None-Match: "abc123"
If-Modified-Since: Mon, 28 Jan 2025 10:00:00 GMT
```

フィードが更新されていない場合:

```
HTTP/1.1 304 Not Modified
```

これにより:
- 帯域幅を節約
- サーバー負荷を軽減
- 処理時間を短縮

### リクエスト間隔

HTMLスクレイピングと同様に:
- 各リクエスト間に2秒の遅延
- タイムアウト: 15秒
- リトライなし（次回実行で再試行）

## セキュリティ

### User-Agent

明確な識別情報を送信：

```
NYT-Article-Monitor/1.0 (GitHub Actions; article-change-detection; +https://github.com)
```

### 公開フィードのみ

- 認証が必要なフィードには対応していません
- 公開されているRSSフィードのみ使用してください

### robots.txt

RSSフィードは通常、公開配信を目的としていますが、念のため:
1. サイトの robots.txt を確認
2. 利用規約を遵守
3. 過度なリクエストを避ける

## 制限事項

### 現在の制限

1. **最新記事のみ**: フィード内の最初の記事だけを監視
2. **認証なし**: パスワード保護されたフィードは非対応
3. **カスタムフォーマット**: 非標準のXML形式は動作しない可能性

### 将来の拡張

- 認証対応 (Basic Auth, API Key)
- 複数記事の追跡
- カスタムXMLパーサー
- フィード自動検出

## まとめ

RSSフィード対応により:

✅ 複数のニュースサイトを統一的に監視
✅ 安定したデータ取得
✅ 拡張しやすいアーキテクチャ
✅ 最小限のサーバー負荷

設定ファイルにURLを追加するだけで、自動的に適切なスクレイパーが選択されます。
