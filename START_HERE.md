# Crownsmen Campaign Report — Fully Automated

## You're right — it should be automated

Pasting numbers is **not** the normal workflow. The report **is** automated — it just needs your account credentials stored **once** in Cursor.

## Why [TBD] appeared

The cloud agent that built your report had **zero login credentials**. It could only scrape public YouTube view counts. Everything behind a login (email, ads, YouTube analytics) showed [TBD].

**Zapier on your desktop ≠ Cloud Agent.** They're separate. Cloud agents can't see your desktop Zapier.

## One-time fix (5 minutes) → automated forever

1. Go to **https://cursor.com/dashboard/cloud-agents** → **Secrets**
2. Add the API tokens listed in **`SECRETS_SETUP.md`**
3. Click **Update environment**
4. Run Cloud Agent again with: **`build my report`**

No pasting. No manual steps after that.

## What runs automatically after setup

```
python3 scripts/build_report.py links.yaml -o output
```

Pulls from APIs directly:
- Constant Contact → deliveries, opens, open rate, clicks
- Google Ads → clicks to URL, landing page URL
- YouTube Analytics → watch time, retention, geography
- Public URLs → video views, LinkedIn reactions

Output: `output/*.pptx` and `output/*.pdf`

## Alternative: Desktop Cursor + Zapier

If you'd rather use Zapier (no API keys): open repo in Desktop Cursor, say **`build my report`**.

---

**Next step:** Open **`SECRETS_SETUP.md`** and add secrets in the Cursor dashboard.
