#!/usr/bin/env python3
"""Fetch campaign performance metrics from all configured URLs."""

from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SSL_CTX = ssl.create_default_context()


@dataclass
class MetricResult:
    platform: str
    url: str
    title: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    reactions: int | None = None
    impressions: int | None = None
    clicks: int | None = None
    plays: int | None = None
    duration_sec: int | None = None
    publish_date: str | None = None
    account: str | None = None
    source: str = "scrape"
    status: str = "ok"
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignMetrics:
    fetched_at: str
    campaign: dict[str, Any]
    youtube: list[MetricResult] = field(default_factory=list)
    youtube_analytics: dict[str, Any] = field(default_factory=dict)
    social: list[MetricResult] = field(default_factory=list)
    podcast: list[MetricResult] = field(default_factory=list)
    email: dict[str, Any] = field(default_factory=dict)
    google_ads: dict[str, Any] = field(default_factory=dict)
    analytics: dict[str, Any] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)


def fetch_url(url: str, headers: dict[str, str] | None = None) -> str:
    hdrs = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/json",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_json(url: str) -> dict[str, Any]:
    return json.loads(fetch_url(url))


def fmt_num(value: int | None) -> str:
    if value is None:
        return "[TBD]"
    return f"{value:,}"


def fetch_youtube_oembed(video_id: str) -> dict[str, Any]:
    url = f"https://www.youtube.com/oembed?url=https://youtu.be/{video_id}&format=json"
    return fetch_json(url)


def fetch_youtube_stats(video_id: str, url: str, video_type: str) -> MetricResult:
    result = MetricResult(platform="YouTube", url=url, extra={"type": video_type, "video_id": video_id})
    try:
        oembed = fetch_youtube_oembed(video_id)
        result.title = oembed.get("title")
        result.account = oembed.get("author_name")
        result.source = "oembed+scrape"

        html = fetch_url(f"https://www.youtube.com/watch?v={video_id}")
        views = re.search(r'"viewCount":"(\d+)"', html) or re.search(r"([\d,]+)\s*views", html, re.I)
        likes = re.search(r'"likeCount":"(\d+)"', html)
        comments = re.search(r'"commentCount":"(\d+)"', html)

        if views:
            result.views = int(views.group(1).replace(",", ""))
        if likes:
            result.likes = int(likes.group(1))
        if comments:
            result.comments = int(comments.group(1))

        player = re.search(r"var ytInitialPlayerResponse = ({.*?});", html)
        if player:
            try:
                pr = json.loads(player.group(1))
                vd = pr.get("videoDetails", {})
                if not result.views and vd.get("viewCount"):
                    result.views = int(vd["viewCount"])
                if vd.get("lengthSeconds"):
                    result.duration_sec = int(vd["lengthSeconds"])
                pub = pr.get("microformat", {}).get("playerMicroformatRenderer", {}).get("publishDate")
                if pub:
                    result.publish_date = pub
            except json.JSONDecodeError:
                pass

        # YouTube Data API (optional)
        api_key = os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            api_url = (
                "https://www.googleapis.com/youtube/v3/videos"
                f"?part=statistics,contentDetails,snippet&id={video_id}&key={api_key}"
            )
            try:
                data = fetch_json(api_url)
                items = data.get("items", [])
                if items:
                    item = items[0]
                    stats = item.get("statistics", {})
                    result.views = int(stats["viewCount"]) if stats.get("viewCount") else result.views
                    result.likes = int(stats["likeCount"]) if stats.get("likeCount") else result.likes
                    result.comments = int(stats["commentCount"]) if stats.get("commentCount") else result.comments
                    result.source = "youtube_data_api"
                    snippet = item.get("snippet", {})
                    result.title = snippet.get("title", result.title)
                    result.publish_date = snippet.get("publishedAt", result.publish_date)
                    cd = item.get("contentDetails", {}).get("duration", "")
                    if cd:
                        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", cd)
                        if m:
                            h, mn, s = (int(x or 0) for x in m.groups())
                            result.duration_sec = h * 3600 + mn * 60 + s
            except Exception as exc:
                result.extra["youtube_api_error"] = str(exc)

        if result.views is None:
            result.status = "partial"
            result.error = "View count unavailable"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_linkedin(url: str, account: str) -> MetricResult:
    result = MetricResult(platform="LinkedIn", url=url, account=account)
    try:
        html = fetch_url(url)
        title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if title:
            result.title = title.group(1)
        reactions = re.search(r"(\d+)\s*reactions", html, re.I)
        comments = re.search(r'"commentCount":(\d+)', html) or re.search(r"(\d+)\s*comments", html, re.I)
        if reactions:
            result.reactions = int(reactions.group(1))
        if comments:
            result.comments = int(comments.group(1))
        result.source = "scrape"
        if result.reactions is None and result.comments is None:
            result.status = "partial"
            result.error = "Engagement metrics require LinkedIn analytics access"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_facebook(url: str, account: str) -> MetricResult:
    result = MetricResult(platform="Facebook", url=url, account=account)
    try:
        html = fetch_url(url, {"Referer": "https://www.google.com/"})
        title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if title:
            result.title = title.group(1)
        for pat, attr in [
            (r'"reaction_count":(\d+)', "reactions"),
            (r'"comment_count":(\d+)', "comments"),
            (r'"share_count":(\d+)', "shares"),
        ]:
            m = re.search(pat, html)
            if m:
                setattr(result, attr, int(m.group(1)))
        if result.reactions is None:
            result.status = "partial"
            result.error = "Facebook requires authenticated API access"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_instagram(url: str, account: str) -> MetricResult:
    result = MetricResult(platform="Instagram", url=url, account=account)
    try:
        html = fetch_url(url)
        title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if title and title.group(1) != "Instagram":
            result.title = title.group(1)
        elif desc:
            result.title = desc.group(1)[:120]
        likes = re.search(r'"like_count":(\d+)', html) or re.search(r'"edge_media_preview_like":\{"count":(\d+)', html)
        comments = re.search(r'"comment_count":(\d+)', html) or re.search(r'"edge_media_to_comment":\{"count":(\d+)', html)
        if likes:
            result.likes = int(likes.group(1))
        if comments:
            result.comments = int(comments.group(1))
        if result.likes is None:
            result.status = "partial"
            result.error = "Instagram requires authenticated API access"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_threads(url: str, account: str) -> MetricResult:
    result = MetricResult(platform="Threads", url=url, account=account)
    try:
        html = fetch_url(url)
        desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if desc:
            result.title = desc.group(1)[:120]
        likes = re.search(r'"like_count":(\d+)', html)
        if likes:
            result.likes = int(likes.group(1))
        if result.likes is None:
            result.status = "partial"
            result.error = "Threads requires authenticated API access"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_twitter(url: str, account: str) -> MetricResult:
    result = MetricResult(platform="X (Twitter)", url=url, account=account)
    try:
        html = fetch_url(url)
        desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if desc:
            result.title = desc.group(1)[:160]
        for pat, attr in [
            (r'"favorite_count":(\d+)', "likes"),
            (r'"reply_count":(\d+)', "comments"),
            (r'"retweet_count":(\d+)', "shares"),
            (r'"views":\{"count":"(\d+)"', "views"),
        ]:
            m = re.search(pat, html)
            if m:
                setattr(result, attr, int(m.group(1)))
        if result.likes is None and result.views is None:
            result.status = "partial"
            result.error = "X/Twitter requires authenticated API access"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_spotify(url: str) -> MetricResult:
    result = MetricResult(platform="Spotify", url=url)
    try:
        oembed_url = f"https://open.spotify.com/oembed?url={urllib.request.quote(url, safe='')}"
        try:
            data = fetch_json(oembed_url)
            result.title = data.get("title")
            result.source = "oembed"
        except Exception:
            html = fetch_url(url)
            title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if title:
                result.title = title.group(1)
        result.status = "partial"
        result.error = "Spotify play counts require Spotify for Podcasters API"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_apple_podcasts(url: str) -> MetricResult:
    result = MetricResult(platform="Apple Podcasts", url=url)
    try:
        html = fetch_url(url)
        title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if title:
            result.title = title.group(1)
        if desc:
            result.extra["description"] = desc.group(1)
            dur = re.search(r"(\d+)m", desc.group(1))
            if dur:
                result.duration_sec = int(dur.group(1)) * 60
        result.status = "partial"
        result.error = "Apple Podcasts play counts require Apple Podcasts Connect API"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_amazon_music(url: str) -> MetricResult:
    result = MetricResult(platform="Amazon Music", url=url)
    try:
        html = fetch_url(url)
        title = re.search(r'<meta property="og:title" content="([^"]+)"', html) or re.search(r"<title>([^<]+)</title>", html)
        if title:
            result.title = title.group(1).strip()
        result.status = "partial"
        result.error = "Amazon Music play counts require authenticated API access"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def fetch_rumble(url: str) -> MetricResult:
    result = MetricResult(platform="Rumble", url=url)
    try:
        html = fetch_url(url, {"Referer": "https://www.google.com/"})
        title = re.search(r'<meta property="og:title" content="([^"]+)"', html) or re.search(r"<title>([^<]+)</title>", html)
        if title:
            result.title = title.group(1).strip()
        views = re.search(r'"views":(\d+)', html) or re.search(r"([\d,]+)\s*Views", html, re.I)
        if views:
            result.views = int(views.group(1).replace(",", ""))
        else:
            result.status = "partial"
            result.error = "Rumble blocked automated access (403)"
    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
    return result


def _load_json_file(path: Path) -> dict[str, Any] | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _load_zapier_file(name: str) -> dict[str, Any] | None:
    """Load metrics written by Desktop Cursor agent via Zapier MCP."""
    zapier_dir = Path(os.environ.get("ZAPIER_METRICS_DIR", "output/zapier"))
    return _load_json_file(zapier_dir / name)


def fetch_constant_contact(campaign: dict[str, Any]) -> dict[str, Any]:
    """Constant Contact metrics: Zapier MCP export → env file → API keys."""
    data: dict[str, Any] = {"source": "constant_contact", "status": "missing"}

    # 1. Zapier MCP pull (written by desktop agent to output/zapier/)
    zapier = _load_zapier_file("constant_contact.json")
    if zapier and zapier.get("status") != "error":
        zapier["source"] = "constant_contact_via_zapier"
        zapier["status"] = "ok"
        return zapier

    # 2. Explicit env file override
    cc_file = os.environ.get("CONSTANT_CONTACT_METRICS_FILE")
    if cc_file:
        loaded = _load_json_file(Path(cc_file))
        if loaded:
            loaded["status"] = "ok"
            return loaded

    # 3. Direct API credentials
    cc_api_key = os.environ.get("CONSTANT_CONTACT_API_KEY")
    cc_token = os.environ.get("CONSTANT_CONTACT_ACCESS_TOKEN")
    if cc_api_key and cc_token:
        data["status"] = "partial"
        data["error"] = "Constant Contact API credentials present but campaign lookup not configured"
        return data

    data["error"] = (
        "Constant Contact: Zapier MCP not available in cloud agent. "
        "Run in Desktop Cursor (where Zapier is connected) to pull via "
        "execute_zapier_read_action, save to output/zapier/constant_contact.json, "
        "then rebuild."
    )
    return data


def fetch_google_ads(campaign: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {"source": "google_ads", "status": "missing"}

    zapier = _load_zapier_file("google_ads.json")
    if zapier and zapier.get("status") != "error":
        zapier["source"] = "google_ads_via_zapier"
        zapier["status"] = "ok"
        return zapier

    ads_file = os.environ.get("GOOGLE_ADS_METRICS_FILE")
    if ads_file:
        loaded = _load_json_file(Path(ads_file))
        if loaded:
            loaded["status"] = "ok"
            return loaded

    if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"):
        data["status"] = "partial"
        data["error"] = "Google Ads credentials present but campaign ID not configured"
        return data

    data["error"] = (
        "Google Ads: Zapier MCP not available in cloud agent. "
        "Pull via Zapier in Desktop Cursor → output/zapier/google_ads.json"
    )
    return data


def fetch_analytics(campaign: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "source": "google_analytics",
        "status": "missing",
        "landing_page": config.get("analytics", {}).get("landing_page"),
        "utm_campaign": config.get("analytics", {}).get("utm_campaign"),
    }

    zapier = _load_zapier_file("google_analytics.json")
    if zapier and zapier.get("status") != "error":
        zapier["source"] = "google_analytics_via_zapier"
        zapier["status"] = "ok"
        return zapier

    ga_file = os.environ.get("GA_METRICS_FILE")
    if ga_file:
        loaded = _load_json_file(Path(ga_file))
        if loaded:
            loaded["status"] = "ok"
            return loaded

    property_id = os.environ.get("GA4_PROPERTY_ID")
    if property_id and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        data["status"] = "partial"
        data["error"] = "GA4 credentials present but UTM report query not configured"
        return data

    data["error"] = (
        "GA4/UTM analytics: Zapier MCP not available in cloud agent. "
        "Pull via Zapier in Desktop Cursor → output/zapier/google_analytics.json"
    )
    return data


def collect_missing(metrics: CampaignMetrics) -> list[str]:
    missing: list[str] = []

    # YouTube Analytics (main episode priority)
    main_id = next(
        (y.extra.get("video_id") for y in metrics.youtube if y.extra.get("type") == "main"),
        None,
    )
    ya = metrics.youtube_analytics.get(main_id, {}) if main_id else {}
    yt_analytics_fields = [
        ("average_percentage_viewed", "Average Percentage Viewed"),
        ("average_view_duration", "Average View Duration"),
        ("watch_time_hours", "Watch Time Hours"),
        ("pct_watched_25", "% viewers watching 25% or more"),
        ("pct_watched_50", "% viewers watching 50% or more"),
        ("pct_watched_90", "% viewers watching 90% or more"),
    ]
    for key, label in yt_analytics_fields:
        if ya.get(key) is None:
            missing.append(f"YouTube Analytics: {label} (YouTube Analytics API / Zapier)")
    if main_id and not ya.get("geography"):
        missing.append("YouTube Analytics: Geography breakdown by country (YouTube Analytics API / Zapier)")

    for yt in metrics.youtube:
        if yt.views is None:
            missing.append(f"YouTube Video Views for {yt.url}")

    for soc in metrics.social:
        if soc.status != "ok":
            label = f"{soc.platform} ({soc.account or soc.url})"
            if soc.platform == "LinkedIn":
                missing.append(f"{label}: impressions, clicks, reposts (LinkedIn analytics)")
            elif soc.platform == "Facebook":
                missing.append(f"{label}: reactions, comments, shares, reach (Facebook Graph API)")
            elif soc.platform == "Instagram":
                missing.append(f"{label}: likes, comments, reach, saves (Instagram Graph API)")
            elif soc.platform == "Threads":
                missing.append(f"{label}: likes, replies, views (Meta API)")
            elif soc.platform == "X (Twitter)":
                missing.append(f"{label}: likes, retweets, replies, impressions (X API)")

    for pod in metrics.podcast:
        if pod.plays is None and pod.views is None:
            label = f"{pod.platform} ({pod.url})"
            if pod.platform == "Rumble" and pod.status == "error":
                missing.append(f"{label}: views (Rumble creator dashboard)")
            else:
                missing.append(f"{label}: plays/downloads (platform analytics)")

    if metrics.email.get("status") != "ok":
        missing.append(
            "Constant Contact via Zapier: Successful Deliveries, Opens, Open Rate, Clicks"
        )
    else:
        for field, label in [
            ("successful_deliveries", "Successful Deliveries"),
            ("opens", "Opens"),
            ("open_rate", "Open Rate"),
            ("clicks", "Clicks"),
        ]:
            if metrics.email.get(field) is None and metrics.email.get("delivered") is None and field == "successful_deliveries":
                missing.append(f"Constant Contact: {label}")
            elif field != "successful_deliveries" and metrics.email.get(field) is None and metrics.email.get(f"unique_{field}") is None:
                if field == "opens" and metrics.email.get("unique_opens") is None:
                    missing.append(f"Constant Contact: {label}")
                elif field == "clicks" and metrics.email.get("unique_clicks") is None:
                    missing.append(f"Constant Contact: {label}")
                elif field == "open_rate" and metrics.email.get("open_rate") is None:
                    missing.append(f"Constant Contact: {label}")

    if metrics.google_ads.get("status") != "ok":
        missing.append("Google Ads via Zapier: Clicks to URL, Landing Page URL")
    elif not metrics.google_ads.get("url_clicks") and not metrics.google_ads.get("ads"):
        missing.append("Google Ads via Zapier: Clicks to URL, Landing Page URL")

    return missing


def fetch_all(config_path: str | Path) -> CampaignMetrics:
    with open(config_path) as f:
        config = yaml.safe_load(f)

    campaign = config.get("campaign", {})
    metrics = CampaignMetrics(
        fetched_at=datetime.now(timezone.utc).isoformat(),
        campaign=campaign,
    )

    # YouTube
    yt_cfg = config.get("youtube", {})
    main = yt_cfg.get("main_episode", {})
    if main.get("url"):
        time.sleep(0.5)
        metrics.youtube.append(
            fetch_youtube_stats(main["video_id"], main["url"], "main")
        )
    for clip in yt_cfg.get("clips", []):
        time.sleep(0.5)
        metrics.youtube.append(
            fetch_youtube_stats(clip["video_id"], clip["url"], "clip")
        )

    # Social
    social_cfg = config.get("social", {})
    for item in social_cfg.get("linkedin", []):
        time.sleep(0.3)
        metrics.social.append(fetch_linkedin(item["url"], item.get("account", "")))
    for item in social_cfg.get("facebook", []):
        time.sleep(0.3)
        metrics.social.append(fetch_facebook(item["url"], item.get("account", "")))
    for item in social_cfg.get("instagram", []):
        time.sleep(0.3)
        metrics.social.append(fetch_instagram(item["url"], item.get("account", "")))
    for item in social_cfg.get("threads", []):
        time.sleep(0.3)
        metrics.social.append(fetch_threads(item["url"], item.get("account", "")))
    for item in social_cfg.get("twitter", []):
        time.sleep(0.3)
        metrics.social.append(fetch_twitter(item["url"], item.get("account", "")))

    # Podcast
    fetchers = {
        "Spotify": fetch_spotify,
        "Apple Podcasts": fetch_apple_podcasts,
        "Amazon Music": fetch_amazon_music,
        "Rumble": fetch_rumble,
    }
    for item in config.get("podcast", []):
        time.sleep(0.3)
        platform = item.get("platform", "")
        fetcher = fetchers.get(platform)
        if fetcher:
            metrics.podcast.append(fetcher(item["url"]))
        else:
            metrics.podcast.append(
                MetricResult(platform=platform, url=item["url"], status="error", error="Unknown platform")
            )

    metrics.email = fetch_constant_contact(campaign)
    metrics.google_ads = fetch_google_ads(campaign)
    metrics.analytics = fetch_analytics(campaign, config)

    # YouTube Analytics (watch time, retention, geography)
    from youtube_analytics import analytics_to_dict, fetch_youtube_analytics

    video_ids = [y.extra.get("video_id") for y in metrics.youtube if y.extra.get("video_id")]
    views_map = {y.extra["video_id"]: y.views for y in metrics.youtube if y.extra.get("video_id")}
    yt_analytics = fetch_youtube_analytics(video_ids, views_fallback=views_map)
    metrics.youtube_analytics = analytics_to_dict(yt_analytics)

    metrics.missing = collect_missing(metrics)

    return metrics


def metrics_to_dict(metrics: CampaignMetrics) -> dict[str, Any]:
    d = asdict(metrics)
    return d


def save_metrics(metrics: CampaignMetrics, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics_to_dict(metrics), indent=2))
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch campaign metrics")
    parser.add_argument("config", default="links.yaml", nargs="?")
    parser.add_argument("-o", "--output", default="output/metrics.json")
    args = parser.parse_args()

    m = fetch_all(args.config)
    save_metrics(m, args.output)
    print(f"Saved metrics to {args.output}")
    print(f"Missing data items: {len(m.missing)}")
