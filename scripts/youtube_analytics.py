#!/usr/bin/env python3
"""Fetch YouTube Analytics metrics (watch time, retention, geography)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class YouTubeVideoAnalytics:
    video_id: str
    title: str | None = None
    video_views: int | None = None
    average_percentage_viewed: float | None = None
    average_view_duration: str | None = None  # e.g. "12:34"
    average_view_duration_sec: float | None = None
    watch_time_hours: float | None = None
    pct_watched_25: float | None = None
    pct_watched_50: float | None = None
    pct_watched_90: float | None = None
    geography: list[dict[str, Any]] = field(default_factory=list)
    geography_totals: dict[str, Any] = field(default_factory=dict)
    source: str = "missing"
    status: str = "missing"
    error: str | None = None


def _sec_to_hms(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _load_json(path: Path) -> dict[str, Any] | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _parse_video_record(video_id: str, data: dict[str, Any]) -> YouTubeVideoAnalytics:
    geo = data.get("geography", [])
    totals = data.get("geography_totals") or _compute_geo_totals(geo)
    return YouTubeVideoAnalytics(
        video_id=video_id,
        title=data.get("title"),
        video_views=data.get("video_views") or data.get("views"),
        average_percentage_viewed=data.get("average_percentage_viewed"),
        average_view_duration=data.get("average_view_duration"),
        average_view_duration_sec=data.get("average_view_duration_sec"),
        watch_time_hours=data.get("watch_time_hours"),
        pct_watched_25=data.get("pct_watched_25"),
        pct_watched_50=data.get("pct_watched_50"),
        pct_watched_90=data.get("pct_watched_90"),
        geography=geo,
        geography_totals=totals,
        source=data.get("source", "file"),
        status="ok",
    )


def _compute_geo_totals(geography: list[dict[str, Any]]) -> dict[str, Any]:
    total_views = sum(g.get("views", 0) or 0 for g in geography)
    total_watch_hours = sum(g.get("watch_time_hours", 0) or 0 for g in geography)
    # Weighted avg duration
    weighted_dur = 0.0
    weight = 0
    for g in geography:
        v = g.get("views") or 0
        d = g.get("average_view_duration_sec") or 0
        if v and d:
            weighted_dur += d * v
            weight += v
    avg_dur_sec = weighted_dur / weight if weight else None
    return {
        "views": total_views,
        "watch_time_hours": round(total_watch_hours, 2) if total_watch_hours else None,
        "average_view_duration": _sec_to_hms(avg_dur_sec) if avg_dur_sec else None,
        "average_view_duration_sec": avg_dur_sec,
        "countries": len(geography),
    }


def fetch_via_youtube_analytics_api(
    video_ids: list[str],
    channel_id: str | None = None,
    start_date: str = "2020-01-01",
    end_date: str = "2030-12-31",
) -> dict[str, YouTubeVideoAnalytics]:
    """Pull metrics via YouTube Analytics API v2 (requires OAuth)."""
    results: dict[str, YouTubeVideoAnalytics] = {}

    token_path = os.environ.get("YOUTUBE_OAUTH_TOKEN_FILE") or os.environ.get("GOOGLE_OAUTH_TOKEN_FILE")
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    client_secrets = os.environ.get("YOUTUBE_CLIENT_SECRETS_FILE")
    yt_refresh = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    yt_client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    yt_client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")

    if not any([token_path, creds_path, client_secrets, yt_refresh, os.environ.get("YOUTUBE_REFRESH_TOKEN")]):
        for vid in video_ids:
            results[vid] = YouTubeVideoAnalytics(
                video_id=vid,
                status="missing",
                error="YouTube Analytics API requires OAuth (YOUTUBE_OAUTH_TOKEN_FILE or GOOGLE_APPLICATION_CREDENTIALS)",
            )
        return results

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        for vid in video_ids:
            results[vid] = YouTubeVideoAnalytics(
                video_id=vid,
                status="error",
                error="Install google-api-python-client and google-auth",
            )
        return results

    try:
        if token_path and Path(token_path).exists():
            token_data = json.loads(Path(token_path).read_text())
            creds = Credentials.from_authorized_user_info(token_data)
        elif yt_refresh and yt_client_id and yt_client_secret:
            creds = Credentials(
                None,
                refresh_token=yt_refresh,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=yt_client_id,
                client_secret=yt_client_secret,
            )
        else:
            from google.oauth2.credentials import Credentials as C
            creds = C(
                None,
                refresh_token=os.environ.get("YOUTUBE_REFRESH_TOKEN"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.environ.get("YOUTUBE_CLIENT_ID"),
                client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET"),
            )

        yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)
        yt_data = build("youtube", "v3", credentials=creds)

        if not channel_id:
            ch_resp = yt_data.channels().list(part="id", mine=True).execute()
            items = ch_resp.get("items", [])
            channel_id = items[0]["id"] if items else None

        for video_id in video_ids:
            rec = YouTubeVideoAnalytics(video_id=video_id, source="youtube_analytics_api")

            # Core metrics
            core = yt_analytics.reports().query(
                ids=f"channel=={channel_id}",
                startDate=start_date,
                endDate=end_date,
                metrics="views,averageViewDuration,averageViewPercentage,estimatedMinutesWatched",
                filters=f"video=={video_id}",
            ).execute()

            rows = core.get("rows", [])
            if rows:
                views, avg_dur_sec, avg_pct, est_minutes = rows[0]
                rec.video_views = int(views)
                rec.average_view_duration_sec = float(avg_dur_sec)
                rec.average_view_duration = _sec_to_hms(avg_dur_sec)
                rec.average_percentage_viewed = float(avg_pct)
                rec.watch_time_hours = round(est_minutes / 60, 2)

            # Audience retention (% still watching at 25%, 50%, 90% of video)
            try:
                retention = yt_analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    startDate=start_date,
                    endDate=end_date,
                    dimensions="elapsedVideoTimeRatio",
                    metrics="audienceWatchRatio",
                    filters=f"video=={video_id}",
                    sort="elapsedVideoTimeRatio",
                ).execute()
                ret_rows = retention.get("rows", [])
                if ret_rows:
                    rec.pct_watched_25 = _retention_at_ratio(ret_rows, 0.25)
                    rec.pct_watched_50 = _retention_at_ratio(ret_rows, 0.50)
                    rec.pct_watched_90 = _retention_at_ratio(ret_rows, 0.90)
            except Exception:
                pass

            # Geography
            try:
                geo = yt_analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    startDate=start_date,
                    endDate=end_date,
                    dimensions="country",
                    metrics="views,averageViewDuration,estimatedMinutesWatched",
                    filters=f"video=={video_id}",
                    sort="-views",
                    maxResults=25,
                ).execute()
                geo_rows = geo.get("rows", [])
                headers = [h["name"] for h in geo.get("columnHeaders", [])]
                rec.geography = []
                for row in geo_rows:
                    entry = dict(zip(headers, row))
                    avg_sec = float(entry.get("averageViewDuration", 0))
                    watch_hrs = round(float(entry.get("estimatedMinutesWatched", 0)) / 60, 2)
                    rec.geography.append({
                        "country": entry.get("country"),
                        "views": int(entry.get("views", 0)),
                        "average_view_duration": _sec_to_hms(avg_sec),
                        "average_view_duration_sec": avg_sec,
                        "watch_time_hours": watch_hrs,
                    })
                rec.geography_totals = _compute_geo_totals(rec.geography)
            except Exception:
                pass

            rec.status = "ok" if rec.video_views is not None else "partial"
            results[video_id] = rec

    except Exception as exc:
        for vid in video_ids:
            results[vid] = YouTubeVideoAnalytics(
                video_id=vid,
                status="error",
                error=str(exc),
                source="youtube_analytics_api",
            )

    return results


def _retention_at_ratio(rows: list, target: float) -> float | None:
    """Interpolate audienceWatchRatio at target elapsedVideoTimeRatio."""
    best = None
    best_diff = 999
    for row in rows:
        ratio, watch = row[0], row[1]
        diff = abs(float(ratio) - target)
        if diff < best_diff:
            best_diff = diff
            best = float(watch) * 100
    return round(best, 1) if best is not None else None


def fetch_youtube_analytics(
    video_ids: list[str],
    views_fallback: dict[str, int | None] | None = None,
) -> dict[str, YouTubeVideoAnalytics]:
    """
    Load YouTube analytics from (in priority order):
    1. output/zapier/youtube_analytics.json
    2. output/youtube_analytics.json
    3. YouTube Analytics API (OAuth)
    """
    views_fallback = views_fallback or {}
    results: dict[str, YouTubeVideoAnalytics] = {}

    # 1. Zapier / manual JSON files
    for path in [
        Path(os.environ.get("YOUTUBE_ANALYTICS_FILE", "output/zapier/youtube_analytics.json")),
        Path("output/youtube_analytics.json"),
    ]:
        data = _load_json(path)
        if data and "videos" in data:
            for vid, vdata in data["videos"].items():
                if vid in video_ids:
                    vdata = dict(vdata)
                    vdata["source"] = data.get("source", "zapier")
                    if not vdata.get("video_views") and views_fallback.get(vid):
                        vdata["video_views"] = views_fallback[vid]
                    results[vid] = _parse_video_record(vid, vdata)
            if all(vid in results for vid in video_ids):
                return results

    # 2. YouTube Analytics API
    api_results = fetch_via_youtube_analytics_api(video_ids)
    for vid in video_ids:
        if vid in api_results and api_results[vid].status == "ok":
            results[vid] = api_results[vid]
        elif vid not in results:
            rec = api_results.get(vid) or YouTubeVideoAnalytics(video_id=vid)
            if views_fallback.get(vid):
                rec.video_views = views_fallback[vid]
            rec.status = "partial"
            rec.error = rec.error or "YouTube Analytics requires OAuth or output/zapier/youtube_analytics.json"
            results[vid] = rec

    return results


def analytics_to_dict(results: dict[str, YouTubeVideoAnalytics]) -> dict[str, Any]:
    return {vid: asdict(rec) for vid, rec in results.items()}


# Expected schema for Zapier / desktop agent
YOUTUBE_ANALYTICS_SCHEMA = {
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
}
