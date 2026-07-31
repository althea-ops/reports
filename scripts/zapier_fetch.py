#!/usr/bin/env python3
"""
Merge metrics pulled via Zapier MCP into the campaign metrics pipeline.

Expected files in output/zapier/:
  constant_contact.json  — Successful Deliveries, Opens, Open Rate, Clicks
  google_ads.json        — Clicks to URL, Landing Page URL per ad
  youtube_analytics.json — Watch time, retention, geography
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ZAPIER_DIR = Path("output/zapier")

EXPECTED_SCHEMAS: dict[str, dict[str, Any]] = {
    "constant_contact.json": {
        "source": "constant_contact_via_zapier",
        "status": "ok",
        "campaign_name": "Equify Financial CS 67",
        "subject_line": "CS 67: Equify Financial — The Hidden Cash Inside Your Equipment Fleet",
        "send_date": "2026-05-28",
        "successful_deliveries": 0,
        "opens": 0,
        "open_rate": 0.0,
        "clicks": 0,
    },
    "google_ads.json": {
        "source": "google_ads_via_zapier",
        "status": "ok",
        "clicks": 0,
        "impressions": 0,
        "ctr": 0.0,
        "cost": 0.0,
        "landing_page_url": "https://www.crownsmen.com/equify-financial-construction-equipment-financing/",
        "ads": [
            {
                "name": "Crownsmen - Equify Financial CS 67",
                "clicks_to_url": 0,
                "landing_page_url": "https://www.crownsmen.com/equify-financial-construction-equipment-financing/",
            }
        ],
    },
    "youtube_analytics.json": {
        "source": "youtube_analytics_via_zapier",
        "status": "ok",
        "videos": {
            "RZMgRG6HlB4": {
                "title": "Equify Financial: The Hidden Cash Inside Your Equipment Fleet #67",
                "video_views": 0,
                "average_percentage_viewed": 0.0,
                "average_view_duration": "0:00",
                "average_view_duration_sec": 0.0,
                "watch_time_hours": 0.0,
                "pct_watched_25": 0.0,
                "pct_watched_50": 0.0,
                "pct_watched_90": 0.0,
                "geography": [
                    {
                        "country": "US",
                        "views": 0,
                        "average_view_duration": "0:00",
                        "average_view_duration_sec": 0.0,
                        "watch_time_hours": 0.0,
                    }
                ],
                "geography_totals": {
                    "views": 0,
                    "watch_time_hours": 0.0,
                    "average_view_duration": "0:00",
                    "countries": 0,
                },
            }
        },
    },
}


def load_zapier_metrics(zapier_dir: Path | None = None) -> dict[str, Any]:
    base = zapier_dir or ZAPIER_DIR
    merged: dict[str, Any] = {}
    if not base.exists():
        return merged
    file_map = {
        "constant_contact.json": "email",
        "google_ads.json": "google_ads",
        "youtube_analytics.json": "youtube_analytics",
    }
    for filename, key in file_map.items():
        path = base / filename
        if path.exists():
            try:
                data = json.loads(path.read_text())
                data["status"] = data.get("status", "ok")
                merged[key] = data
            except (json.JSONDecodeError, OSError) as exc:
                merged[key] = {"status": "error", "error": str(exc)}
    return merged


DESKTOP_AGENT_PROMPT = """
Pull these exact metrics for Equify Financial CS 67 via Zapier MCP and rebuild the report.

## YouTube Analytics (video RZMgRG6HlB4)
Use YouTube Analytics read action if available, else YouTube Data API:
- Video Views
- Average Percentage Viewed
- Average View Duration
- Watch Time Hours
- % of viewers watching 25% or more
- % of viewers watching 50% or more
- % of viewers watching 90% or more
- Geography: country, views per country, average view duration, watch time, plus TOTAL row
→ Save to output/zapier/youtube_analytics.json

## Constant Contact (via Zapier)
- Successful Deliveries
- Opens
- Open Rate
- Clicks
→ Save to output/zapier/constant_contact.json

## Google Ads (via Zapier)
- Clicks to URL
- Landing Page URL (per ad/campaign)
→ Save to output/zapier/google_ads.json

Then run: python3 scripts/build_report.py links.yaml -o output
Commit and push updated output files.
"""
