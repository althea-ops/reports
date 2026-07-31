#!/usr/bin/env python3
"""Pull campaign report metrics from promotional links."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


USER_AGENT = "CrownsmenReportBot/1.0"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3/videos"


@dataclass
class YouTubeStats:
    url: str
    video_id: str | None = None
    title: str | None = None
    view_count: int | None = None
    duration_seconds: int | None = None
    average_percentage_viewed: str | None = None
    average_view_duration: str | None = None
    watch_time_hours: int | None = None
    pct_25_plus: str | None = None
    pct_50_plus: str | None = None
    pct_90_plus: str | None = None
    geography: list[dict[str, Any]] = field(default_factory=list)
    source: str = "unavailable"
    notes: str = ""


@dataclass
class EmailStats:
    url: str
    successful_deliveries: int | None = None
    opens: int | None = None
    open_rate: str | None = None
    clicks: int | None = None
    source: str = "unavailable"
    notes: str = ""


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def fetch_text(url: str, timeout: int = 20) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode(errors="replace")
    except urllib.error.URLError:
        return None


def youtube_video_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname in {"youtu.be"}:
        return parsed.path.lstrip("/").split("/")[0] or None
    if "youtube.com" in (parsed.hostname or ""):
        if parsed.path == "/watch":
            return urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1]
    return None


def seconds_to_duration(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def parse_iso8601_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        value,
    )
    if not match:
        return None
    hours, minutes, seconds = (int(x) if x else 0 for x in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def fetch_youtube_oembed(url: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(url, safe="")
    data = fetch_json(f"https://www.youtube.com/oembed?url={encoded}&format=json") or {}
    return {"title": data.get("title"), "author_name": data.get("author_name")}


def fetch_youtube_data_api(video_id: str, api_key: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
            "key": api_key,
        }
    )
    payload = fetch_json(f"{YOUTUBE_API}?{params}") or {}
    items = payload.get("items") or []
    if not items:
        return {}
    item = items[0]
    stats = item.get("statistics") or {}
    snippet = item.get("snippet") or {}
    content = item.get("contentDetails") or {}
    return {
        "title": snippet.get("title"),
        "view_count": int(stats["viewCount"]) if stats.get("viewCount") else None,
        "duration_seconds": parse_iso8601_duration(content.get("duration")),
    }


def fetch_youtube_analytics(video_id: str) -> dict[str, Any]:
    """Use YouTube Analytics API when OAuth credentials are configured."""
    token_path = os.environ.get("YOUTUBE_OAUTH_TOKEN_PATH")
    if not token_path or not Path(token_path).exists():
        return {}

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return {"notes": "Install google-api-python-client and google-auth-oauthlib for Analytics API."}

    creds = Credentials.from_authorized_user_file(token_path)
    youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)

    end = date.today().isoformat()
    start = date(date.today().year, 1, 1).isoformat()
    metrics = (
        "views,averageViewDuration,averageViewPercentage,"
        "estimatedMinutesWatched,subscribersGained"
    )
    report = (
        youtube_analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start,
            endDate=end,
            metrics=metrics,
            filters=f"video=={video_id}",
        )
        .execute()
    )

    headers = report.get("columnHeaders") or []
    rows = report.get("rows") or []
    if not rows:
        return {}

    keyed = {h["name"]: value for h, value in zip(headers, rows[0])}

    retention_report = (
        youtube_analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start,
            endDate=end,
            metrics="audienceWatchRatio",
            dimensions="elapsedVideoTimeRatio",
            filters=f"video=={video_id}",
            sort="elapsedVideoTimeRatio",
        )
        .execute()
    )

    pct_25 = pct_50 = pct_90 = None
    for row in retention_report.get("rows") or []:
        ratio, watch_ratio = row
        if ratio >= 0.25 and pct_25 is None:
            pct_25 = round(watch_ratio * 100)
        if ratio >= 0.50 and pct_50 is None:
            pct_50 = round(watch_ratio * 100)
        if ratio >= 0.90 and pct_90 is None:
            pct_90 = round(watch_ratio * 100)

    geo_report = (
        youtube_analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start,
            endDate=end,
            metrics="views",
            dimensions="country",
            filters=f"video=={video_id}",
            sort="-views",
            maxResults=10,
        )
        .execute()
    )
    geography = [
        {"country": row[0], "views": row[1]}
        for row in geo_report.get("rows") or []
    ]

    avg_pct = keyed.get("averageViewPercentage")
    avg_duration = keyed.get("averageViewDuration")
    watch_minutes = keyed.get("estimatedMinutesWatched")

    return {
        "view_count": keyed.get("views"),
        "average_percentage_viewed": f"{round(avg_pct)}%" if avg_pct is not None else None,
        "average_view_duration": seconds_to_duration(int(avg_duration)) if avg_duration else None,
        "watch_time_hours": int(watch_minutes / 60) if watch_minutes else None,
        "pct_25_plus": f"{pct_25}%" if pct_25 is not None else None,
        "pct_50_plus": f"{pct_50}%" if pct_50 is not None else None,
        "pct_90_plus": f"{pct_90}%" if pct_90 is not None else None,
        "geography": geography,
        "source": "youtube_analytics_api",
    }


def collect_youtube(url: str) -> YouTubeStats:
    video_id = youtube_video_id(url)
    stats = YouTubeStats(url=url, video_id=video_id)

    oembed = fetch_youtube_oembed(url)
    stats.title = oembed.get("title")

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if video_id and api_key:
        api_data = fetch_youtube_data_api(video_id, api_key)
        stats.title = api_data.get("title") or stats.title
        stats.view_count = api_data.get("view_count")
        stats.duration_seconds = api_data.get("duration_seconds")
        stats.source = "youtube_data_api"

    if video_id:
        analytics = fetch_youtube_analytics(video_id)
        if analytics:
            stats.view_count = analytics.get("view_count") or stats.view_count
            stats.average_percentage_viewed = analytics.get("average_percentage_viewed")
            stats.average_view_duration = analytics.get("average_view_duration")
            stats.watch_time_hours = analytics.get("watch_time_hours")
            stats.pct_25_plus = analytics.get("pct_25_plus")
            stats.pct_50_plus = analytics.get("pct_50_plus")
            stats.pct_90_plus = analytics.get("pct_90_plus")
            stats.geography = analytics.get("geography") or []
            stats.source = analytics.get("source", stats.source)

    if stats.view_count is None:
        stats.notes = (
            "Public view count unavailable without YOUTUBE_API_KEY. "
            "Retention/geography require YOUTUBE_OAUTH_TOKEN_PATH (YouTube Analytics API)."
        )
    elif not stats.average_percentage_viewed:
        stats.notes = (
            "View count pulled from YouTube Data API. "
            "Retention/geography require YouTube Analytics OAuth or Studio CSV export."
        )

    return stats


def fetch_email_stats(url: str) -> EmailStats:
    stats = EmailStats(url=url)
    if "constantcontact.com" in url:
        stats.notes = (
            "Constant Contact campaign stats require API auth. "
            "Connect Constant Contact in Zapier MCP or paste stats from CC dashboard."
        )
    else:
        stats.notes = "Email stats not available from public campaign URL."
    return stats


def fetch_conversion_clicks(tracking_url: str) -> dict[str, Any]:
    return {
        "tracking_url": tracking_url,
        "total_clicks": None,
        "notes": "Click totals require client analytics (GA4, HubSpot, etc.) — not available from URL alone.",
    }


def load_links(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def collect_all(links_path: Path) -> dict[str, Any]:
    config = load_links(links_path)
    launch = config.get("episode_launch") or {}

    full_url = launch.get("youtube_full", "")
    highlight_url = launch.get("youtube_highlight", "")

    result = {
        "report": config.get("report", {}),
        "episode_launch_links": {
            "YouTube (Full Episode)": full_url,
            "YouTube (Highlight)": highlight_url,
            "LinkedIn – Crownsmen Partners": launch.get("linkedin_crownsmen"),
            "LinkedIn – Mining Now": launch.get("linkedin_mining_now"),
            "Facebook": launch.get("facebook"),
            "Instagram": launch.get("instagram"),
            "Threads": launch.get("threads"),
            "X (Twitter)": launch.get("x_twitter"),
            "Spotify": launch.get("spotify"),
            "Rumble": launch.get("rumble"),
            "Crownsmen Website": launch.get("crownsmen_website"),
            "Apple Podcasts": launch.get("apple_podcasts"),
            "LinkedIn Newsletter": launch.get("linkedin_newsletter"),
            "Email": launch.get("email"),
        },
        "event_promotion": config.get("event_promotion") or [],
        "youtube_full": asdict(collect_youtube(full_url)) if full_url else None,
        "youtube_highlight": asdict(collect_youtube(highlight_url)) if highlight_url else None,
        "email_marketing": asdict(fetch_email_stats(launch.get("email", ""))),
        "one_click_conversion": fetch_conversion_clicks(
            (config.get("one_click_conversion") or {}).get("tracking_url", "")
        ),
        "collection_notes": [
            "Titles and public view counts: YouTube Data API (YOUTUBE_API_KEY).",
            "Retention, watch time, geography: YouTube Analytics API (YOUTUBE_OAUTH_TOKEN_PATH).",
            "Email stats: Constant Contact API / Zapier MCP.",
            "Conversion clicks: client analytics dashboard.",
        ],
    }
    return result


def main() -> None:
    links_path = Path(sys.argv[1] if len(sys.argv) > 1 else "links.yaml")
    if not links_path.exists():
        print(json.dumps({"error": f"Missing {links_path}. Copy templates/links.example.yaml to links.yaml."}, indent=2))
        sys.exit(1)

    output = collect_all(links_path)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
