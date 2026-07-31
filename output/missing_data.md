# Missing Data Report

Generated: 2026-07-31T17:50:58.497964+00:00
Campaign: CS 67 — Equify Financial

The following metrics could not be automatically retrieved and are marked as **[TBD]** in the report deck.

## Missing Metrics

1. YouTube likes/comments for https://youtu.be/RZMgRG6HlB4
2. YouTube likes/comments for https://youtu.be/-y_KlhcE80k
3. YouTube likes/comments for https://youtu.be/cb6VcOTrP0w
4. Facebook (Crownsmen Partners): reactions, comments, shares, reach (Facebook Graph API)
5. Instagram (@crownsmenp): likes, comments, reach, saves (Instagram Graph API)
6. Threads (@crownsmenp): likes, replies, views (Meta API)
7. X (Twitter) (@CrownsmenP): likes, retweets, replies, impressions (X API)
8. Spotify (https://open.spotify.com/episode/7HThkUd9VXWB6YlVPhWMyf?si=4pK9_mMxTUa5PLQazCMBPg): plays/downloads (platform analytics)
9. Apple Podcasts (https://podcasts.apple.com/us/podcast/cs-67-equify-financial-the-hidden-cash-inside-your/id1365112754?i=1000769959116): plays/downloads (platform analytics)
10. Amazon Music (https://music.amazon.com/podcasts/c29d9c84-881d-4839-9bc4-d0d799cd3f3d/episodes/1ff7e9f5-6893-408a-897d-35ef4b6ec88f): plays/downloads (platform analytics)
11. Rumble (https://rumble.com/v7ahm0u-equify-financial-the-hidden-cash-inside-your-equipment-fleet-67.html): views (Rumble creator dashboard)
12. Constant Contact email metrics: sends, opens, clicks, bounces, unsubscribes (Zapier MCP — authenticate in Cursor desktop)
13. Google Ads metrics: impressions, clicks, CTR, cost, conversions (Google Ads API credentials)
14. Landing page UTM click analytics for crownsmen.com/equify-financial-* (GA4 / client analytics dashboard)

## How to Fill Gaps

### Constant Contact (Email)
- Authenticate Zapier MCP in Cursor desktop (Settings → Tools & MCP → Connect)
- Enable Constant Contact read actions in Zapier MCP
- Re-run: `python3 scripts/build_report.py links.yaml -o output`

### Google Ads
- Set `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`
- Or export metrics to `output/google_ads.json` and set `GOOGLE_ADS_METRICS_FILE`

### Google Analytics (UTM Clicks)
- Set `GA4_PROPERTY_ID` and `GOOGLE_APPLICATION_CREDENTIALS`
- Or export UTM click data to `output/analytics.json` and set `GA_METRICS_FILE`

### YouTube Analytics API
- Set `YOUTUBE_API_KEY` for public stats (views, likes, comments)
- YouTube Analytics API (watch time, traffic sources) requires OAuth credentials

### Social Platforms
- LinkedIn, Facebook, Instagram, Threads, X require platform API credentials or creator dashboard exports

### Podcast Platforms
- Spotify for Podcasters, Apple Podcasts Connect, Amazon Music, Rumble creator dashboards

## Successfully Retrieved

### YouTube
- ✓ Equify Financial: The Hidden Cash Inside Your Equipment Fleet #67: views=52,894, likes=[TBD], comments=[TBD]
- ✓ Equify Financial Shares Why Renting Equipment First Improves Financing Approval: views=2,104, likes=[TBD], comments=[TBD]
- ✓ Equify Financial Talks About Equipment Financing Mistakes Contractors Make: views=1,617, likes=[TBD], comments=[TBD]

### Social Media
- ✓ LinkedIn (Crownsmen Partners): ok
- ✓ LinkedIn (The Construction Show): ok
- ⚠ Facebook (Crownsmen Partners): error
- ⚠ Instagram (@crownsmenp): partial
- ⚠ Threads (@crownsmenp): partial
- ⚠ X (Twitter) (@CrownsmenP): partial

### Podcast
- ✓ Spotify: CS 67. Equify Financial: The Hidden Cash Inside Your Equipment Fleet
- ✓ Apple Podcasts: CS 67. Equify Financial: The Hidden Cash Inside Your Equipment Fleet
- ⚠ Amazon Music: title unavailable
- ⚠ Rumble: title unavailable
