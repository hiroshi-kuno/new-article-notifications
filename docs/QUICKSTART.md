# クイックスタート

5分でセットアップできるガイドです。

## 1. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

## 2. 監視ソースの設定

`config/sources.json` を編集して、監視したいページを追加します。
`webhook` フィールドで通知先を指定できます：

```json
{
  "sources": [
    {
      "url": "https://www.nytimes.com/by/agnes-chang",
      "enabled": true,
      "webhook": "WEBHOOK_URL_NYT"
    }
  ]
}
```

## 3. ローカルでテスト

```bash
python check_articles.py
```

実行後、`state/` ディレクトリに状態ファイルが作成されていることを確認してください。

## 4. GitHubにデプロイ

```bash
git init
git add .
git commit -m "Initial commit"

# GitHubリポジトリを作成してプッシュ
gh repo create new-article-notifications --public --source=. --remote=origin --push
```

## 5. GitHub Actionsを有効化

1. GitHubリポジトリの **Actions** タブを開く
2. 「ワークフローを有効にする」をクリック
3. 以後、毎時間自動的に実行されます

## 6. Secretsの設定

1. リポジトリの **Settings** → **Secrets and variables** → **Actions**
2. 使用するwebhookのシークレットを追加（例: `WEBHOOK_URL_NYT`）

## 7. 動作確認

初回実行後：

```bash
git pull
cat state/agnes-chang.json
```

最新の記事データが保存されていれば成功です。

## よく使うコマンド

```bash
# 手動実行
python check_articles.py

# 状態確認
ls state/
cat state/*.json

# GitHub Actionsのログ確認
gh run list
gh run view --log

# 手動でワークフロー実行
gh workflow run check-articles.yml
```

## 実行時の出力例

### 初回実行
- 各ソースの状態ファイルを作成
- 現在のトップ記事をベースラインとして記録
- 「新記事」とは検出されない（初回はベースライン取得）

### 2回目以降
- トップ記事に変化があるか確認
- 変化あり → `NEW ARTICLE DETECTED!` をログ出力し、Discordに通知
- 変化なし → `No change` または `Page not modified (304)` をログ出力

### 新記事が検出されたとき
```
  NEW ARTICLE DETECTED!

  Previous article:
    Title: 旧記事タイトル
    URL: https://www.nytimes.com/...

  New article:
    Title: 新記事タイトル
    URL: https://www.nytimes.com/...
```

## トラブルシューティング

### 状態ファイルが作成されない
- `state/` ディレクトリの書き込み権限を確認
- スクリプトの出力にエラーがないか確認

### GitHub Actionsが動かない
- Settings → Actions → General で Actions が有効になっているか確認
- ワークフローファイルの構文を確認
- リポジトリに書き込み権限があるか確認

### 記事が検出されない
- DOMの構造が変わった可能性あり
- `docs/TESTING.md` のデバッグ手順を参照
