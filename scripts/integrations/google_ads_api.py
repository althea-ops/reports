"""Google Ads API — automated clicks and landing page URLs."""

from __future__ import annotations

import os
from typing import Any


def fetch_ads_metrics(
    campaign_name_contains: str = "Equify",
    customer_id: str | None = None,
) -> dict[str, Any]:
    """
    Returns clicks, impressions, ads[] with clicks_to_url and landing_page_url.
    Requires env: GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID,
    GOOGLE_ADS_CLIENT_SECRET, GOOGLE_ADS_REFRESH_TOKEN, GOOGLE_ADS_CUSTOMER_ID
    """
    customer_id = customer_id or os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    client_id = os.environ.get("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")

    if not all([dev_token, client_id, client_secret, refresh_token, customer_id]):
        return {
            "status": "missing",
            "error": "Set GOOGLE_ADS_DEVELOPER_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, CUSTOMER_ID",
        }

    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        return {"status": "error", "error": "Install google-ads: pip install google-ads"}

    config = {
        "developer_token": dev_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "use_proto_plus": True,
    }

    try:
        client = GoogleAdsClient.load_from_dict(config)
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
              campaign.name,
              campaign.id,
              ad_group.name,
              ad_group_ad.ad.final_urls,
              metrics.clicks,
              metrics.impressions,
              metrics.ctr,
              metrics.cost_micros
            FROM ad_group_ad
            WHERE campaign.name LIKE '%{campaign_name_contains}%'
              AND ad_group_ad.status != 'REMOVED'
            ORDER BY metrics.clicks DESC
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        ads = []
        total_clicks = 0
        total_impressions = 0
        total_cost_micros = 0

        for row in response:
            clicks = row.metrics.clicks
            total_clicks += clicks
            total_impressions += row.metrics.impressions
            total_cost_micros += row.metrics.cost_micros
            final_urls = list(row.ad_group_ad.ad.final_urls) if row.ad_group_ad.ad.final_urls else []
            ads.append({
                "name": row.campaign.name,
                "ad_group": row.ad_group.name,
                "clicks_to_url": clicks,
                "clicks": clicks,
                "landing_page_url": final_urls[0] if final_urls else None,
                "impressions": row.metrics.impressions,
            })

        ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
        return {
            "source": "google_ads_api",
            "status": "ok",
            "clicks": total_clicks,
            "impressions": total_impressions,
            "ctr": round(ctr, 2),
            "cost": round(total_cost_micros / 1_000_000, 2),
            "campaign_name": campaign_name_contains,
            "ads": ads,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
