#!/usr/bin/env python3
"""
Merge metrics pulled via Zapier MCP into the campaign metrics pipeline.

When running in Desktop Cursor (where Zapier MCP is authenticated), the agent
should call Zapier read actions and write results to output/zapier/*.json.
This module loads those files automatically during report builds.

Expected files (any that exist will be merged):
  output/zapier/constant_contact.json
  output/zapier/google_ads.json
  output/zapier/google_analytics.json
  output/zapier/youtube_analytics.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ZAPIER_DIR = Path("output/zapier")

# Schema reference for desktop agent pulling via Zapier MCP
EXPECTED_SCHEMAS: dict[str, dict[str, Any]] = {
    "constant_contact.json": {
        "source": "constant_contact",
        "status": "ok",
        "campaign_name": "Equify Financial CS 67",
        "subject_line": "CS 67: Equify Financial — The Hidden Cash Inside Your Equipment Fleet",
        "send_date": "2026-05-28",
        "sends": 0,
        "delivered": 0,
        "unique_opens": 0,
        "open_rate": 0.0,
        "unique_clicks": 0,
        "click_rate": 0.0,
        "bounces": 0,
        "unsubscribes": 0,
    },
    "google_ads.json": {
        "source": "google_ads",
        "status": "ok",
        "impressions": 0,
        "clicks": 0,
        "ctr": 0.0,
        "cost": 0.0,
        "conversions": 0,
        "cost_per_conversion": 0.0,
        "avg_cpc": 0.0,
        "video_views": 0,
        "campaigns": [
            {
                "name": "Crownsmen - Equify Financial",
                "ad_group": "CS 67",
                "impressions": 0,
                "clicks": 0,
                "cost": 0.0,
            }
        ],
    },
    "google_analytics.json": {
        "source": "google_analytics",
        "status": "ok",
        "landing_page": "https://www.crownsmen.com/equify-financial-construction-equipment-financing/",
        "utm_campaign": "crownsmen",
        "pageviews": 0,
        "sessions": 0,
        "users": 0,
        "avg_duration": "0:00",
        "utm_clicks": 0,
        "bounce_rate": 0.0,
        "client_clicks": 0,
        "conversion_rate": 0.0,
        "utm_breakdown": [
            {"source": "email", "medium": "email", "campaign": "crownsmen", "clicks": 0},
            {"source": "youtube", "medium": "video", "campaign": "crownsmen", "clicks": 0},
        ],
    },
    "youtube_analytics.json": {
        "source": "youtube_analytics",
        "videos": {
            "RZMgRG6HlB4": {
                "watch_time_minutes": 0,
                "avg_view_duration": "0:00",
                "traffic_sources": {},
            }
        },
    },
}


def load_zapier_metrics(zapier_dir: Path | None = None) -> dict[str, Any]:
    """Load all available Zapier-pulled metric files."""
    base = zapier_dir or ZAPIER_DIR
    merged: dict[str, Any] = {}

    if not base.exists():
        return merged

    file_map = {
        "constant_contact.json": "email",
        "google_ads.json": "google_ads",
        "google_analytics.json": "analytics",
        "youtube_analytics.json": "youtube_analytics",
    }

    for filename, key in file_map.items():
        path = base / filename
        if path.exists():
            try:
                data = json.loads(path.read_text())
                data["status"] = data.get("status", "ok")
                data["source"] = data.get("source", key)
                merged[key] = data
            except (json.JSONDecodeError, OSError) as exc:
                merged[key] = {"status": "error", "error": str(exc)}

    return merged


def write_schema_templates(zapier_dir: Path | None = None) -> None:
    """Write example schema files (with placeholder zeros) for reference."""
    base = zapier_dir or ZAPIER_DIR
    base.mkdir(parents=True, exist_ok=True)
    for filename, schema in EXPECTED_SCHEMAS.items():
        path = base / filename
        if not path.exists():
            path.write_text(json.dumps(schema, indent=2) + "\n")


DESKTOP_AGENT_PROMPT = """
Pull campaign metrics for Equify Financial CS 67 via Zapier MCP and rebuild the report.

1. Call list_enabled_zapier_actions to see available tools.
2. Use execute_zapier_read_action (reads — no confirmation needed) for:
   - Constant Contact: find the email campaign for CS 67 / Equify Financial
     → saves, opens, clicks, bounces, unsubscribes, subject line, send date
   - Google Ads: campaign performance for Crownsmen / Equify / CS 67
     → impressions, clicks, CTR, cost, conversions, video views
   - Google Analytics (GA4): UTM clicks for landing page
     crownsmen.com/equify-financial-construction-equipment-financing/
     → sessions, pageviews, users, utm_breakdown by source/medium/campaign
   - YouTube Analytics (if enabled): watch time and traffic sources for RZMgRG6HlB4
3. Write results to:
   - output/zapier/constant_contact.json
   - output/zapier/google_ads.json
   - output/zapier/google_analytics.json
   - output/zapier/youtube_analytics.json (optional)
4. Rebuild: python3 scripts/build_report.py links.yaml -o output
5. Commit and push updated output files.
"""


if __name__ == "__main__":
    import sys

    write_schema_templates()
    loaded = load_zapier_metrics()
    if loaded:
        print(json.dumps(loaded, indent=2))
    else:
        print("No Zapier metrics found in output/zapier/")
        print("\n--- Desktop Agent Prompt ---")
        print(DESKTOP_AGENT_PROMPT)
