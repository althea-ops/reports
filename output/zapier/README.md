# Zapier MCP Metrics (Desktop Cursor)

Cloud Agents **cannot access your Desktop Zapier MCP connection**. Your Zapier
integrations (Constant Contact, Google Ads, Google Analytics) are authenticated
in **Desktop Cursor**, not in the isolated cloud VM.

## Quick fix — run in Desktop Cursor

1. Open this repo in **Desktop Cursor** (not Cloud Agent)
2. Start a new Agent chat locally
3. Paste this prompt:

```
Pull campaign metrics for Equify Financial CS 67 via Zapier MCP and rebuild the report.

1. Call list_enabled_zapier_actions to see my connected tools.
2. Use execute_zapier_read_action for:
   - Constant Contact → email campaign stats (sends, opens, clicks, bounces)
   - Google Ads → campaign performance (impressions, clicks, CTR, cost, conversions)
   - Google Analytics → UTM clicks for crownsmen.com/equify-financial-construction-equipment-financing/
3. Save results to output/zapier/constant_contact.json, google_ads.json, google_analytics.json
4. Run: python3 scripts/build_report.py links.yaml -o output
5. Commit and push the updated report.
```

The desktop agent has your Zapier auth and will fill in all `[TBD]` slides.

## Expected JSON files

| File | Zapier source | Slides updated |
|------|---------------|----------------|
| `constant_contact.json` | Constant Contact read actions | Slide 7 (Email) |
| `google_ads.json` | Google Ads read actions | Slide 9 (Paid Media) |
| `google_analytics.json` | GA4 read actions | Slide 8 (Website/UTM) |
| `youtube_analytics.json` | YouTube Analytics (optional) | Slide 3 enrichment |

See `scripts/zapier_fetch.py` for the expected JSON schema.

## Why cloud agents can't see Zapier

When I tried to call Zapier MCP from this cloud run:

```
serverStatus: "needsAuth"
Interactive MCP authentication is only available in the Cursor desktop IDE
```

Your Zapier connection lives in Desktop Cursor's MCP session. Cloud agents run
in a separate VM without that session.

## Manual alternative

If you prefer, export metrics from Zapier manually and place JSON files here.
Then re-run:

```bash
python3 scripts/build_report.py links.yaml -o output
```
