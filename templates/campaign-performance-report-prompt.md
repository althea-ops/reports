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

### STEP 2 — Build the 10-slide deck

Use `data/collected.json` to populate this exact structure:

| Slide | Title | Auto-filled from |
|-------|-------|------------------|
| 1 | Cover | `report.year`, `report.date_created`, today's date if blank |
| 2 | Report Content | Static: "Episode Performance 01" |
| 3 | Promotional Links - Episode Launch | All URLs from `episode_launch_links` |
| 4 | Promotional Links - Event | `event_promotion[]` — infer **Remarks** from cross-posting patterns in the sample (same platforms listed per content type) |
| 5 | Episode Performance | `report.episode_number` |
| 6 | YouTube \| Full Episode Statistics | `youtube_full.*` |
| 7 | YouTube \| Highlight Episode Statistics | `youtube_highlight.*` (no watch time hours) |
| 8 | YouTube \| Geography | `youtube_full.geography` — bar chart top 10 countries |
| 9 | Email Marketing + One-Click Conversion | `email_marketing.*` + `one_click_conversion.*` |
| 10 | Thank You | Static Crownsmen footer |

Run:
```bash
python3 scripts/generate_report.py data/collected.json output/[Client]_Campaign_Performance_Report.pptx
```

---

### DESIGN RULES

- Match sample deck layout: metric label left, value right, comma-formatted numbers, durations as `M:SS`.
- Footer on slides 1 & 10: `© 2018 Crownsmen Partners | www.crownsmen.com | info@crownsmen.com`
- File name: `[ClientName]_Campaign_Performance_Report_MN_[EpisodeNumber]_Crownsmen_Partners.pptx`

---

### DELIVERABLES

1. `data/collected.json` — all fetched metrics with `source` field per metric
2. Completed `.pptx`
3. `missing_data.md` — anything that could not be pulled from links/APIs and exactly how to fix it (e.g. add `YOUTUBE_API_KEY`)

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
