# Crownsmen Partners Campaign Performance Reports

Automated campaign performance report generator for Crownsmen Partners client campaigns.

## Quick Start

```bash
pip install -r requirements.txt
python3 scripts/build_report.py links.yaml -o output
```

## Deliverables

| Output | Description |
|--------|-------------|
| `output/*.pptx` | 10-slide PowerPoint matching Crownsmen report format |
| `output/*.pdf` | Same presentation exported as PDF |
| `output/metrics.json` | Raw fetched metrics from all URLs |
| `output/missing_data.md` | List of metrics that couldn't be auto-retrieved |

## Data Sources

The build script pulls metrics from:

- **YouTube** — oEmbed + page scrape (+ YouTube Data API if `YOUTUBE_API_KEY` is set)
- **LinkedIn, Facebook, Instagram, Threads, X** — public page scrape (limited without API keys)
- **Spotify, Apple Podcasts, Amazon Music, Rumble** — oEmbed / page metadata
- **Constant Contact** — Zapier MCP (requires authentication in Cursor desktop)
- **Google Ads** — API credentials or `GOOGLE_ADS_METRICS_FILE` JSON export
- **UTM / Landing Page Analytics** — GA4 API or `GA_METRICS_FILE` JSON export

Metrics that can't be pulled automatically appear as **[TBD]** in the deck and are listed in `output/missing_data.md`.

## Configuration

Edit `links.yaml` to configure campaign URLs and metadata for each client/episode.

## Optional Environment Variables

```bash
YOUTUBE_API_KEY              # YouTube Data API v3
GA4_PROPERTY_ID              # Google Analytics 4
GOOGLE_APPLICATION_CREDENTIALS
GOOGLE_ADS_DEVELOPER_TOKEN
GOOGLE_ADS_CLIENT_ID
GOOGLE_ADS_CLIENT_SECRET
GOOGLE_ADS_REFRESH_TOKEN
GA_METRICS_FILE              # Path to pre-exported analytics JSON
GOOGLE_ADS_METRICS_FILE      # Path to pre-exported ads JSON
CONSTANT_CONTACT_METRICS_FILE
```
