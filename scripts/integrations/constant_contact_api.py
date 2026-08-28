"""Constant Contact API v3 — automated email metrics."""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
import json
from typing import Any


CC_BASE = "https://api.cc.email/v3"


def _headers() -> dict[str, str]:
    token = os.environ.get("CONSTANT_CONTACT_ACCESS_TOKEN")
    if not token:
        raise ValueError("CONSTANT_CONTACT_ACCESS_TOKEN not set")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _get(path: str) -> dict[str, Any]:
    req = urllib.request.Request(f"{CC_BASE}{path}", headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def find_campaign(search_terms: list[str]) -> dict[str, Any] | None:
    """Find email campaign by name keywords (e.g. Equify, CS 67)."""
    data = _get("/emails?limit=100")
    campaigns = data.get("campaigns") or data.get("bulk_email_campaigns") or []
    if isinstance(data, list):
        campaigns = data

    best = None
    best_score = 0
    for c in campaigns:
        name = (c.get("name") or c.get("campaign_name") or "").lower()
        score = sum(1 for term in search_terms if term.lower() in name)
        if score > best_score:
            best_score = score
            best = c
    return best


def fetch_campaign_metrics(
    campaign_id: str | None = None,
    search_terms: list[str] | None = None,
) -> dict[str, Any]:
    """
    Returns:
      successful_deliveries, opens, open_rate, clicks, campaign_name, subject_line
    """
    search_terms = search_terms or ["Equify", "CS 67"]
    if not campaign_id:
        campaign = find_campaign(search_terms)
        if not campaign:
            return {"status": "error", "error": f"No Constant Contact campaign matching {search_terms}"}
        campaign_id = campaign.get("campaign_id") or campaign.get("id")
        campaign_name = campaign.get("name") or campaign.get("campaign_name")
    else:
        campaign_name = None

    stats_resp = _get(f"/reports/stats/email_campaigns/{campaign_id}")
    results = stats_resp.get("results") or []
    if not results:
        return {"status": "error", "error": f"No stats for campaign {campaign_id}"}

    row = results[0]
    stats = row.get("stats", {})
    percents = row.get("percents", {})

    sends = stats.get("em_sends", 0)
    bounces = stats.get("em_bounces", 0)
    deliveries = sends - bounces if sends else 0
    opens = stats.get("em_opens", 0)
    clicks = stats.get("em_clicks", 0)
    open_rate = percents.get("open")

    return {
        "source": "constant_contact_api",
        "status": "ok",
        "campaign_id": campaign_id,
        "campaign_name": campaign_name or search_terms[0],
        "successful_deliveries": deliveries,
        "delivered": deliveries,
        "opens": opens,
        "unique_opens": opens,
        "open_rate": float(open_rate) if open_rate is not None else (opens / deliveries * 100 if deliveries else 0),
        "clicks": clicks,
        "unique_clicks": clicks,
        "sends": sends,
        "bounces": bounces,
    }
