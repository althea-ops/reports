# Cursor Prompt — Link-Driven Crownsmen Campaign Performance Report

**You only provide links.** Cursor pulls data from those URLs and builds the 10-slide deck.

Attach:
- `@templates/links.example.yaml` (or your filled-in `links.yaml`)
- `@Crownsmen_Partners_Campaign_Performance_Report__MN_360_-_Prospex_Group-compressed.pdf` (format reference)

---

## PROMPT START — copy from here

Generate a **Crownsmen Partners Campaign Performance Report** by pulling all available data from the promotional links below. Do not ask me to manually enter view counts or analytics — fetch them yourself.

**Format reference:** `@Crownsmen_Partners_Campaign_Performance_Report__MN_360_-_Prospex_Group-compressed.pdf`

**Links file:** `@links.yaml`

---

### STEP 1 — Collect data from links (run this first)

```bash
pip install -r requirements.txt
python3 scripts/collect_report_data.py links.yaml > data/collected.json
```

Then enrich the JSON by fetching anything the script could not get:

| Data needed | How to pull it from the links |
|-------------|-------------------------------|
| YouTube video titles | Already from oEmbed / Data API |
| YouTube view counts | `YOUTUBE_API_KEY` env var → YouTube Data API v3 |
| YouTube retention (avg %, 25/50/90%, watch time, geography) | YouTube Analytics API (`YOUTUBE_OAUTH_TOKEN_PATH`) **or** export CSV from YouTube Studio for each video URL and parse it |
| Email opens/clicks/deliveries | Constant Contact API via Zapier MCP (`execute_zapier_read_action` for Constant Contact campaign stats using the email link) **or** fetch from Constant Contact dashboard if connected |
| One-click conversion clicks | Query client analytics for the UTM URL in `one_click_conversion.tracking_url` |

For each link in `episode_launch` and `event_promotion`, visit/fetch the URL and capture any public metadata (title, view count, likes, publish date). Merge into `data/collected.json`.

**Do not invent numbers.** If a metric cannot be fetched, set it to `null` and list it in a `missing_data` array at the end.

---

### STEP 2 — Build PowerPoint + PDF (required deliverables)

Run the one-command builder — it produces **both** a `.pptx` and a `.pdf`:

```bash
python3 scripts/build_report.py links.yaml -o output
```

Outputs in `output/`:
- `[Client]_Campaign_Performance_Report_MN_[Episode]_Crownsmen_Partners.pptx` — editable PowerPoint
- `[Client]_Campaign_Performance_Report_MN_[Episode]_Crownsmen_Partners.pdf` — client-ready PDF (same layout)
- `collected.json` — all fetched metrics
- `missing_data.md` — anything still needed from APIs

The PDF must match the sample deck structure (10 slides). If PDF conversion fails, install LibreOffice and re-run.

Use this **exact slide order**:

---

### DESIGN RULES

- Match sample deck layout: metric label left, value right, comma-formatted numbers, durations as `M:SS`.
- Footer on slides 1 & 10: `© 2018 Crownsmen Partners | www.crownsmen.com | info@crownsmen.com`
- File name: `[ClientName]_Campaign_Performance_Report_MN_[EpisodeNumber]_Crownsmen_Partners.pptx`

---

### DELIVERABLES

1. **`output/*.pptx`** — editable PowerPoint presentation (10 slides)
2. **`output/*.pdf`** — same presentation exported as PDF for the client
3. `output/collected.json` — all fetched metrics with sources
4. `output/missing_data.md` — gaps that need API credentials

Execute all steps now. Start by reading `links.yaml` and pulling data from every URL.

## PROMPT END

---

## One-time setup (enables full auto-pull)

Add to your environment or `.env`:

```bash
# Public view counts + titles (free tier: https://console.cloud.google.com/apis/credentials)
export YOUTUBE_API_KEY="your-key"

# Retention, watch time, geography (one-time OAuth for @CrownsmenPartners channel)
export YOUTUBE_OAUTH_TOKEN_PATH="/path/to/youtube-oauth-token.json"
```

For email stats, enable **Constant Contact → Get Campaign Stats** in Zapier MCP.

For conversion clicks, connect the client's GA4 or analytics tool in Zapier MCP, or provide the dashboard export path in `links.yaml`.
