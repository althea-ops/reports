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
- **Constant Contact, Google Ads, GA4** — **Zapier MCP via Desktop Cursor** → `output/zapier/*.json`
- Direct API env vars (see below) as fallback

### Zapier MCP (Constant Contact, Google Ads, GA4)

Cloud Agents cannot access your Desktop Zapier connection. To pull authenticated
metrics, run the report build in **Desktop Cursor** where Zapier MCP is connected.
See `output/zapier/README.md` for the exact prompt to paste.

Metrics that can't be pulled automatically appear as **[TBD]** in the deck and are listed in `output/missing_data.md`.

## Development environment (Cursor Cloud Agents)

This repo ships a ready-to-use, versioned Cloud Agent environment in `.cursor/`:

- `.cursor/Dockerfile` — Ubuntu 24.04 base with Python 3.12, `git`/`curl`, and
  **LibreOffice Impress** (required by `scripts/build_report.py` to export the deck to
  PDF). Python packages install into an isolated virtualenv at `/opt/venv` (on `PATH`),
  which avoids the Ubuntu 24.04 PEP 668 "externally-managed" restriction.
- `.cursor/environment.json` — runs `pip install -r requirements.txt` on setup and
  prints a credential summary (`scripts/check_credentials.py`) on each start.

### Local setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# LibreOffice is needed only for the PDF export step:
#   sudo apt-get install -y libreoffice-impress
python3 scripts/build_report.py links.yaml -o output
```

PDF export requires LibreOffice on the `PATH`; without it the `.pptx`, `metrics.json`,
and `missing_data.md` deliverables are still produced.

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
