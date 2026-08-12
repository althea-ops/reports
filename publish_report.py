#!/usr/bin/env python3
"""Publish a campaign report and get a shareable client link."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from generate_campaign_report import (
    TEMPLATES_DIR,
    enrich_with_youtube_api,
    load_report_data,
)

APP_DIR = Path(__file__).resolve().parent
REPORTS_DIR = APP_DIR / "data" / "reports"


def slugify(value: str) -> str:
    slug = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "report"


def default_slug(data: dict) -> str:
    report = data.get("report") or {}
    client = report.get("client_name", "report")
    episode = report.get("episode_number", "")
    base = f"{client}-{episode}" if episode else client
    return slugify(base)


def publish_report(
    data: dict,
    slug: str,
    *,
    full_video_id: str | None = None,
    highlight_video_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    credentials_path: Path | None = None,
    token_path: Path | None = None,
) -> Path:
    if full_video_id or highlight_video_id:
        data = enrich_with_youtube_api(
            data,
            full_video_id=full_video_id,
            highlight_video_id=highlight_video_id,
            start_date=start_date,
            end_date=end_date,
            credentials_path=credentials_path,
            token_path=token_path,
        )

    data["slug"] = slug
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{slug}.json"
    output_path.write_text(json.dumps(data, indent=2))
    return output_path


def build_share_url(slug: str, base_url: str | None = None) -> str:
    base = (base_url or "http://localhost:5000").rstrip("/")
    return f"{base}/report/{slug}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish a report and get a shareable client link.",
    )
    parser.add_argument(
        "--data-json",
        type=Path,
        default=TEMPLATES_DIR / "report_data.example.json",
        help="Report data JSON file",
    )
    parser.add_argument(
        "--slug",
        help="URL slug for the report (e.g. prospex-mn360). Auto-generated if omitted.",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:5000",
        help="Public base URL for the share link (change when deployed)",
    )
    parser.add_argument("--full-video-id", help="Optional YouTube full episode video ID")
    parser.add_argument("--highlight-video-id", help="Optional YouTube highlight video ID")
    parser.add_argument("--start-date", help="Analytics start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Analytics end date (YYYY-MM-DD)")
    parser.add_argument("--credentials", type=Path, help="OAuth credentials JSON path")
    parser.add_argument("--token", type=Path, help="OAuth token JSON path")
    args = parser.parse_args()

    data = load_report_data(args.data_json)
    slug = args.slug or default_slug(data)

    output_path = publish_report(
        data,
        slug,
        full_video_id=args.full_video_id,
        highlight_video_id=args.highlight_video_id,
        start_date=args.start_date,
        end_date=args.end_date,
        credentials_path=args.credentials,
        token_path=args.token,
    )

    share_url = build_share_url(slug, args.base_url)
    print(f"Report published: {output_path}")
    print(f"\nShare this link with your client:\n  {share_url}\n")
    print("Start the web server with:  python web_app.py")


if __name__ == "__main__":
    main()
