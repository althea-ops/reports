# One-Time Setup → Fully Automated Reports Forever

You should **never paste numbers manually**. This repo is built to pull everything automatically — it just needs your login credentials stored **once** in Cursor.

## Why you saw [TBD]

The Cloud Agent that built your report had **no access to your accounts**. Zapier on your desktop doesn't automatically transfer to cloud agents.

**Fix:** Add secrets once in Cursor → every future report fills itself in.

---

## 5-Minute One-Time Setup

### 1. Open Cursor Cloud Agents settings

Go to: **https://cursor.com/dashboard/cloud-agents**

Click **Secrets** (or your Environment → Secrets tab).

### 2. Add these secrets

| Secret name | Where to get it |
|-------------|-----------------|
| `CONSTANT_CONTACT_ACCESS_TOKEN` | Constant Contact → Account → Integrations → API Keys → generate token |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API Center (your MCC/developer token) |
| `GOOGLE_ADS_CLIENT_ID` | Google Cloud Console → OAuth client |
| `GOOGLE_ADS_CLIENT_SECRET` | Same OAuth client |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuth flow for Google Ads API |
| `GOOGLE_ADS_CUSTOMER_ID` | Your Google Ads account ID (10 digits, no dashes) |
| `YOUTUBE_REFRESH_TOKEN` | Google OAuth with YouTube Analytics scope |
| `YOUTUBE_CLIENT_ID` | Google Cloud OAuth client |
| `YOUTUBE_CLIENT_SECRET` | Same OAuth client |

Use **Runtime Secret** type for all of these (values stay hidden).

### 3. Rebuild the environment

In the dashboard: **Update environment** or start a **New Setup Run** so the agent VM picks up the secrets.

### 4. Run the agent again

Start a new Cloud Agent on this repo and say:

```
build my report
```

That's it. Fully automated from here on.

---

## What gets pulled automatically (after setup)

| Source | Metrics |
|--------|---------|
| **YouTube Analytics API** | Views, avg % viewed, watch time, 25/50/90% retention, geography |
| **Constant Contact API** | Successful deliveries, opens, open rate, clicks |
| **Google Ads API** | Clicks to URL, landing page URL |
| **Public scrape** | YouTube view counts, LinkedIn reactions |

---

## Already using Zapier?

Zapier MCP only works in **Desktop Cursor**, not Cloud Agents. For **fully automated cloud reports**, use the API secrets above instead.

If you prefer Zapier on desktop, say `build my report` in Desktop Cursor — no secrets needed there.

---

## Verify secrets are working

After setup, the agent run should show in `output/metrics.json`:

```json
"email": { "status": "ok", "source": "constant_contact_api", ... }
"google_ads": { "status": "ok", "source": "google_ads_api", ... }
```

If still `"status": "missing"`, the secret name may be wrong or the environment needs an update run.
