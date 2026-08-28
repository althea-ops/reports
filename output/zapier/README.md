# Zapier MCP — Pull Exact Metrics

Cloud Agents cannot access your Desktop Zapier connection. Run this in **Desktop Cursor**.

## Paste this prompt in Desktop Cursor Agent

```
Pull these exact metrics for Equify Financial CS 67 via Zapier MCP and rebuild the report.

1. Call list_enabled_zapier_actions first.

2. YOUTUBE ANALYTICS (video RZMgRG6HlB4) — save to output/zapier/youtube_analytics.json:
   - Video Views
   - Average Percentage Viewed
   - Average View Duration
   - Watch Time Hours
   - % viewers watching 25% or more
   - % viewers watching 50% or more
   - % viewers watching 90% or more
   - Geography table: country, views, avg view duration, watch time + TOTAL row

3. CONSTANT CONTACT (via Zapier) — save to output/zapier/constant_contact.json:
   - Successful Deliveries
   - Opens
   - Open Rate
   - Clicks

4. GOOGLE ADS (via Zapier) — save to output/zapier/google_ads.json:
   - Clicks to URL
   - Landing Page URL (per ad/campaign)

5. Rebuild: python3 scripts/build_report.py links.yaml -o output
6. Commit and push.
```

## JSON schemas

See `scripts/zapier_fetch.py` for exact field names expected by the report builder.

| File | Key fields |
|------|------------|
| `youtube_analytics.json` | `video_views`, `average_percentage_viewed`, `average_view_duration`, `watch_time_hours`, `pct_watched_25/50/90`, `geography[]`, `geography_totals` |
| `constant_contact.json` | `successful_deliveries`, `opens`, `open_rate`, `clicks` |
| `google_ads.json` | `ads[].clicks_to_url`, `ads[].landing_page_url` |

## Current status (public scrape only)

| Metric | Value |
|--------|-------|
| YouTube Video Views (main) | 52,895 |
| YouTube Analytics (retention, geography) | [TBD] — needs YouTube Analytics API |
| Constant Contact | [TBD] — needs Zapier in Desktop Cursor |
| Google Ads | [TBD] — needs Zapier in Desktop Cursor |
