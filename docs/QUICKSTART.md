# Quick Start Guide

Get the NYT article monitor running in 5 minutes.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure Sources

Edit `config/sources.json` to add reporter pages you want to monitor:

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

## 3. Test Locally

```bash
python check_articles.py
```

Check output and verify `state/` directory contains state files.

## 4. Deploy to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: NYT article monitor"

# Create GitHub repository and push
gh repo create new-article-notifications --public --source=. --remote=origin --push
# Or manually:
# git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
# git push -u origin main
```

## 5. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Click "I understand my workflows, go ahead and enable them"
4. The workflow will run automatically every hour

## 6. Verify It's Working

After the first run:

```bash
git pull
cat state/agnes-chang.json
```

You should see the latest article data.

## Common Commands

```bash
# Run manually
python check_articles.py

# Check state
ls state/
cat state/*.json

# View logs from GitHub Actions
gh run list
gh run view --log

# Trigger manual run
gh workflow run check-articles.yml
```

## What to Expect

### First Run
- Creates state files for each source
- Records the current top article
- No "new article" detected (establishing baseline)

### Subsequent Runs
- Checks if top article changed
- If yes: Logs "NEW ARTICLE DETECTED!"
- If no: Logs "No change" or "Page not modified (304)"
- Updates state files

### When New Article Published
```
NEW ARTICLE DETECTED!

Previous article:
  Title: Old Article Title
  URL: https://www.nytimes.com/...

New article:
  Title: Brand New Article Title
  URL: https://www.nytimes.com/...
```

## Troubleshooting

### No state files created
- Check write permissions
- Verify `state/` directory exists
- Check script output for errors

### GitHub Actions not running
- Verify Actions are enabled in Settings
- Check workflow file syntax
- Ensure repository has write permissions

### Articles not detected
- DOM structure may have changed
- Check TESTING.md for debugging steps
- Open an issue with sample HTML

## Next Steps

- Add more reporter pages to `config/sources.json`
- Set up notifications (see README.md)
- Customize check frequency in `.github/workflows/check-articles.yml`
- Fork and extend for other news sites

## Getting Help

- Read full README.md for details
- Check TESTING.md for debugging
- Review GitHub Actions logs
- Open an issue on GitHub
