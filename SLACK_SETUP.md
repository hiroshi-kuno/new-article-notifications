# Slack通知のセットアップ

新記事が検出されたときに、Slackに自動通知を送る設定方法です。

## 1. Slack Incoming Webhookの作成

### ステップ1: Slackアプリを作成

1. https://api.slack.com/apps にアクセス
2. **Create New App** をクリック
3. **From scratch** を選択
4. アプリ名を入力（例: "Article Notifications"）
5. ワークスペースを選択
6. **Create App** をクリック

### ステップ2: Incoming Webhookを有効化

1. 左メニューから **Incoming Webhooks** を選択
2. **Activate Incoming Webhooks** をオンに切り替え
3. **Add New Webhook to Workspace** をクリック
4. 通知を送信したいチャンネルを選択
5. **許可する** をクリック

### ステップ3: Webhook URLをコピー

1. **Webhook URL** が表示されます
2. URLをコピー（例: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`）

## 2. GitHubシークレットの設定

### ステップ1: リポジトリの設定を開く

1. GitHubリポジトリのページに移動
2. **Settings** タブをクリック
3. 左メニューから **Secrets and variables** → **Actions** を選択

### ステップ2: シークレットを追加

1. **New repository secret** をクリック
2. Name: `SLACK_WEBHOOK_URL`
3. Secret: コピーしたWebhook URLを貼り付け
4. **Add secret** をクリック

## 3. 動作確認

### GitHub Actionsで確認

1. リポジトリの **Actions** タブを開く
2. **Check for New Articles** ワークフローを選択
3. **Run workflow** をクリック
4. ワークフローのログを確認:
   - `✓ Slack notifications enabled` と表示されればOK
   - 新記事が検出されると Slack に通知が送信されます

### ローカルで確認（オプション）

環境変数を設定してローカルでテスト:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
python check_articles.py
```

## 通知の内容

Slackに送信されるメッセージの例:

```
🗽 New Article: agnes-chang

Title:
Breaking: Example Article Title

URL:
View Article (リンク)

Published:
2025-01-28T10:00:00Z

Previous: Old Article Title
```

### サイト別の絵文字

- **NYT**: 🗽
- **Washington Post**: 🏛️
- **その他**: 📰

## トラブルシューティング

### 通知が送信されない

**症状**: `⚠ Slack notifications disabled` と表示される

**原因**: `SLACK_WEBHOOK_URL` が設定されていない

**解決策**:
1. GitHubシークレットが正しく設定されているか確認
2. シークレット名が `SLACK_WEBHOOK_URL` と完全に一致しているか確認
3. ワークフローファイルで環境変数が渡されているか確認

### Webhook URLが無効

**症状**: `✗ Slack notification failed: HTTP 404`

**原因**: Webhook URLが間違っているか、削除された

**解決策**:
1. Slackアプリの設定画面でWebhook URLを確認
2. GitHubシークレットを正しいURLで更新

### タイムアウトエラー

**症状**: `✗ Slack notification error: timeout`

**原因**: Slackのサーバーに接続できない

**解決策**:
- 一時的なネットワーク問題の可能性が高い
- 次回の実行で自動的に再試行される
- 通知失敗してもメインの処理は継続される

## 通知の無効化

通知を一時的に無効にしたい場合:

1. GitHubシークレット `SLACK_WEBHOOK_URL` を削除
2. または、ワークフローファイルの `env:` セクションをコメントアウト:

```yaml
# env:
#   SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## カスタマイズ

### 通知メッセージのカスタマイズ

`src/notifications.py` の `_build_message()` メソッドを編集:

```python
def _build_message(self, source_id: str, article: Article, previous_article: Optional[Article]) -> dict:
    # ここでメッセージの内容をカスタマイズ
    pass
```

### 通知条件のカスタマイズ

特定のソースだけ通知したい場合、`check_articles.py` を編集:

```python
# 例: NYTの記事のみ通知
if 'nytimes.com' in article.url:
    notifier.send(source_id, article, state.last_article)
```

## セキュリティ

### Webhook URLの保護

- **絶対にコードに直接書かない**
- **Gitにコミットしない**
- **GitHub Secretsで管理する**
- Webhook URLを知っている人は誰でもメッセージを送信できます

### URLが漏洩した場合

1. Slackアプリの設定画面に移動
2. Incoming Webhook を無効化
3. 再度有効化して新しいURLを取得
4. GitHubシークレットを更新

## 高度な設定

### 複数のチャンネルに通知

異なるソースを異なるチャンネルに通知したい場合:

1. 複数のWebhook URLを作成（チャンネルごと）
2. 複数のシークレットを設定:
   - `SLACK_WEBHOOK_URL_NYT`
   - `SLACK_WEBHOOK_URL_WAPO`
3. コードで条件分岐

### メンション機能

特定のユーザーやグループにメンションしたい場合:

```python
# メッセージに追加
{
    "type": "section",
    "text": {
        "type": "mrkdwn",
        "text": "<!channel> 新しい記事が公開されました"
    }
}
```

利用可能なメンション:
- `<!channel>`: チャンネル全体
- `<!here>`: オンラインユーザー
- `<@USER_ID>`: 特定ユーザー

## その他の通知方法

Slack以外の通知も実装可能:

### Discord

`src/notifications.py` に `DiscordNotifier` を追加

### メール

SMTPやSendGridを使用

### Microsoft Teams

Incoming Webhookを使用

### LINE Notify

LINE Notify APIを使用

実装例は `src/notifications.py` の `SlackNotifier` を参考にしてください。

## まとめ

✅ Slack Incoming Webhookを作成
✅ GitHubシークレット `SLACK_WEBHOOK_URL` を設定
✅ 新記事検出時に自動的にSlackに通知
✅ 通知失敗してもメインの処理は継続
✅ いつでも有効/無効を切り替え可能
