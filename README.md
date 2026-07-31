# Crownsmen Partners — Campaign Performance Reports

Automate client episode performance reports from **links only**.

## Quick start in Cursor

1. Copy `templates/links.example.yaml` → `links.yaml` and paste your episode URLs
2. Paste the prompt from `templates/campaign-performance-report-prompt.md`
3. Attach `@links.yaml` and the sample PDF format reference

## Local run

```bash
pip install -r requirements.txt
python3 scripts/collect_report_data.py links.yaml > data/collected.json
python3 scripts/generate_report.py data/collected.json output/report.pptx
```

## What pulls automatically from links

| Metric | Source |
|--------|--------|
| Video titles | YouTube oEmbed (no auth) |
| View counts | YouTube Data API (`YOUTUBE_API_KEY`) |
| Retention, watch time, geography | YouTube Analytics API (`YOUTUBE_OAUTH_TOKEN_PATH`) |
| Email opens/clicks | Constant Contact via Zapier MCP |
| Conversion clicks | Client analytics (GA4 etc.) via Zapier MCP |

Some metrics (retention %, email stats, UTM clicks) are **not on the public page** — they require API credentials or Zapier connections.
