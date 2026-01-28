# プロジェクト概要

## NYT記事通知システム

NYT（New York Times）の記者ページを監視し、新しい記事が公開されたときに検知するPythonベースのシステムです。

## 主な特徴

### シンプルな設定
- **`config/sources.json`** に監視したいURLを追加するだけ
- 設定フォーマットは `url` と `enabled` のみ
- ソースIDはURLから自動抽出

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true
    }
  ]
}
```

### 自動実行
- GitHub Actions で1時間ごとに自動チェック
- 状態はGitリポジトリに自動保存
- データベース不要

### サーバー負荷への配慮
- 条件付きリクエスト（ETag、If-Modified-Since）
- リクエスト間に2秒の遅延
- タイムアウト設定（15秒）
- リトライなし（失敗したら次回に）

### 堅牢性
- 1つのソースが失敗しても他のソースは継続
- 複数のHTML解析戦略でDOM変更に対応
- エラーは記録されるが全体は停止しない

## ファイル構成

```
new-article-notifications/
├── config/sources.json          # ← ここを編集して記者を追加
├── state/*.json                 # 自動生成される状態ファイル
├── src/                         # Pythonソースコード
│   ├── config.py               # 設定読み込み
│   ├── models.py               # データモデル
│   ├── scrapers.py             # スクレイピングロジック
│   └── state_manager.py        # 状態管理
├── check_articles.py            # メインスクリプト
└── .github/workflows/           # GitHub Actions設定
    └── check-articles.yml
```

## 使い方

### 1. セットアップ

```bash
pip install -r requirements.txt
```

### 2. 記者の追加

`config/sources.json` を編集：

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true
    },
    {
      "url": "https://www.nytimes.com/by/another-reporter",
      "enabled": true
    }
  ]
}
```

### 3. ローカルテスト

```bash
python check_articles.py
```

### 4. GitHubにデプロイ

```bash
git add .
git commit -m "Add reporters"
git push
```

GitHub Actionsが自動的に1時間ごとに実行されます。

## 状態の確認

```bash
# 状態ファイルを確認
cat state/agnes-chang.json
```

状態ファイルには以下が保存されます：
- 最後に検知した記事（タイトル、URL、公開時刻）
- 最終チェック時刻
- HTTPキャッシュヘッダー（ETag、Last-Modified）
- エラー情報

## 新記事の検知

記事が変わったときのログ例：

```
NEW ARTICLE DETECTED!

Previous article:
  Title: Old Article Title
  URL: https://www.nytimes.com/...

New article:
  Title: Brand New Article Title
  URL: https://www.nytimes.com/...
```

## 技術スタック

- **Python 3.11+**
- **requests** - HTTP通信
- **BeautifulSoup4** - HTML解析
- **GitHub Actions** - 自動実行
- **Git** - 状態保存

## 拡張性

### 通知の追加

`check_articles.py` を編集して、新記事検知時に通知を送信できます：

```python
if state.last_article != article:
    # 新記事検知
    send_slack_notification(...)
    send_email(...)
```

### 他サイトへの対応

`src/scrapers.py` に新しいスクレイパークラスを追加：

```python
def get_scraper(url: str):
    if 'nytimes.com/by/' in url:
        return NYTReporterScraper()
    elif 'example.com/author/' in url:
        return ExampleScraper()
```

## ドキュメント

- **README.md** - 包括的なドキュメント
- **QUICKSTART.md** - 5分で始める
- **TESTING.md** - テストガイド
- **ARCHITECTURE.md** - アーキテクチャ詳細
- **REPOSITORY_STRUCTURE.md** - ファイル構成

## ライセンス

MIT License

## 連絡先

問題や質問がある場合は、GitHubのIssuesで報告してください。
