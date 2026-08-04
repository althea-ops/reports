#!/usr/bin/env python3
"""Fetch YouTube video metrics and return them as a dictionary.

Uses YouTube Data API v3 for total view count and YouTube Analytics API for
watch-time metrics and geographic breakdowns. Analytics metrics (average view
duration, watch time, views by country) are only available through the
Analytics API, not the Data API.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

DEFAULT_CREDENTIALS_PATH = Path("credentials.json")
DEFAULT_TOKEN_PATH = Path("token.json")
DEFAULT_COUNTRIES = ("CA", "AU")


def authenticate(
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> Credentials:
    """Authenticate with Google OAuth 2.0 and return valid credentials."""
    credentials: Credentials | None = None

    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"OAuth client secrets not found at {credentials_path}. "
                    "Download credentials.json from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            credentials = flow.run_local_server(port=0)

        token_path.write_text(credentials.to_json())

    return credentials


def _column_index(headers: list[dict], name: str) -> int:
    for index, header in enumerate(headers):
        if header.get("name") == name:
            return index
    raise KeyError(f"Column '{name}' not found in Analytics API response.")


def _parse_analytics_row(headers: list[dict], row: list) -> dict[str, float | int]:
    parsed: dict[str, float | int] = {}
    for header in headers:
        name = header["name"]
        value = row[_column_index(headers, name)]
        if name in {"views"}:
            parsed[name] = int(value)
        else:
            parsed[name] = float(value)
    return parsed


def get_total_views(youtube, video_id: str) -> int:
    """Return cumulative view count from YouTube Data API v3."""
    response = (
        youtube.videos()
        .list(part="statistics", id=video_id)
        .execute()
    )

    items = response.get("items", [])
    if not items:
        raise ValueError(f"No video found for ID: {video_id}")

    return int(items[0]["statistics"]["viewCount"])


def get_analytics_summary(
    youtube_analytics,
    video_id: str,
    start_date: str,
    end_date: str,
) -> dict[str, float | int]:
    """Return aggregate analytics metrics for a single video."""
    response = (
        youtube_analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,averageViewDuration,averageViewPercentage,estimatedMinutesWatched",
            filters=f"video=={video_id}",
        )
        .execute()
    )

    headers = response.get("columnHeaders", [])
    rows = response.get("rows", [])
    if not rows:
        return {
            "views": 0,
            "averageViewDuration": 0.0,
            "averageViewPercentage": 0.0,
            "estimatedMinutesWatched": 0.0,
        }

    return _parse_analytics_row(headers, rows[0])


def get_views_by_country(
    youtube_analytics,
    video_id: str,
    countries: tuple[str, ...],
    start_date: str,
    end_date: str,
) -> dict[str, int]:
    """Return view counts grouped by country for the requested ISO country codes."""
    response = (
        youtube_analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views",
            dimensions="country",
            filters=f"video=={video_id}",
            sort="-views",
        )
        .execute()
    )

    headers = response.get("columnHeaders", [])
    rows = response.get("rows", [])

    country_index = _column_index(headers, "country")
    views_index = _column_index(headers, "views")

    views_by_country = {country: 0 for country in countries}
    for row in rows:
        country_code = row[country_index]
        if country_code in views_by_country:
            views_by_country[country_code] = int(row[views_index])

    return views_by_country


def fetch_video_metrics(
    video_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    countries: tuple[str, ...] = DEFAULT_COUNTRIES,
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> dict:
    """Fetch video metrics and return them as a simple dictionary."""
    if end_date is None:
        end_date = date.today().isoformat()
    if start_date is None:
        start_date = "2010-01-01"

    credentials = authenticate(credentials_path, token_path)

    youtube = build("youtube", "v3", credentials=credentials)
    youtube_analytics = build("youtubeAnalytics", "v2", credentials=credentials)

    total_views = get_total_views(youtube, video_id)
    analytics_summary = get_analytics_summary(
        youtube_analytics,
        video_id,
        start_date,
        end_date,
    )
    views_by_country = get_views_by_country(
        youtube_analytics,
        video_id,
        countries,
        start_date,
        end_date,
    )

    watch_time_hours = round(
        float(analytics_summary["estimatedMinutesWatched"]) / 60,
        2,
    )

    return {
        "video_id": video_id,
        "date_range": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "total_views": total_views,
        "average_view_duration_seconds": round(
            float(analytics_summary["averageViewDuration"]),
            2,
        ),
        "average_percentage_viewed": round(
            float(analytics_summary["averageViewPercentage"]),
            1,
        ),
        "watch_time_hours": watch_time_hours,
        "views_by_country": {
            "Canada": views_by_country.get("CA", 0),
            "Australia": views_by_country.get("AU", 0),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video metrics and print them as JSON.",
    )
    parser.add_argument("video_id", help="YouTube video ID to report on")
    parser.add_argument(
        "--start-date",
        default="2010-01-01",
        help="Analytics start date (YYYY-MM-DD). Default: 2010-01-01",
    )
    parser.add_argument(
        "--end-date",
        default=date.today().isoformat(),
        help="Analytics end date (YYYY-MM-DD). Default: today",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=DEFAULT_CREDENTIALS_PATH,
        help="Path to OAuth client secrets JSON file",
    )
    parser.add_argument(
        "--token",
        type=Path,
        default=DEFAULT_TOKEN_PATH,
        help="Path to store/read OAuth token JSON file",
    )
    args = parser.parse_args()

    metrics = fetch_video_metrics(
        video_id=args.video_id,
        start_date=args.start_date,
        end_date=args.end_date,
        credentials_path=args.credentials,
        token_path=args.token,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
