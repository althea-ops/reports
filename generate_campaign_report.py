#!/usr/bin/env python3
"""Generate a Campaign Performance Report PDF matching the Crownsmen sample deck."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from youtube_video_report import fetch_video_metrics

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
DEFAULT_OUTPUT = Path("Automated_Campaign_Report.pdf")
DEFAULT_FOOTER = "© 2018 Crownsmen Partners | www.crownsmen.com | info@crownsmen.com"

EPISODE_LAUNCH_LABELS = {
    "youtube_full": "YouTube (Full Episode)",
    "youtube_highlight": "YouTube (Highlight)",
    "linkedin_crownsmen": "LinkedIn – Crownsmen Partners",
    "linkedin_mining_now": "LinkedIn – Mining Now",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "threads": "Threads",
    "x_twitter": "X (Twitter)",
    "spotify": "Spotify",
    "rumble": "Rumble",
    "crownsmen_website": "Crownsmen Website",
    "apple_podcasts": "Apple Podcasts",
    "linkedin_newsletter": "LinkedIn Newsletter",
    "email": "Email",
}


def fmt_num(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float) and value == int(value):
        return f"{int(value):,}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def fmt_percent(value: float | int | str | None, decimals: int = 0) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        return value if "%" in value else f"{value}%"
    if decimals == 0:
        return f"{int(round(float(value)))}%"
    return f"{float(value):.{decimals}f}%"


def fmt_duration(seconds: float | int | str | None) -> str:
    if seconds is None:
        return "N/A"
    if isinstance(seconds, str):
        return seconds
    total = int(round(float(seconds)))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


def fmt_report_date(value: str | None = None) -> str:
    if not value:
        return date.today().strftime("%m/%d/%Y")
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return value


def _youtube_metrics(youtube: dict, *, include_watch_time: bool) -> list[dict[str, str]]:
    metrics = [
        {"label": "Video Views", "value": fmt_num(youtube.get("view_count"))},
        {
            "label": "Average Percentage Viewed",
            "value": fmt_percent(youtube.get("average_percentage_viewed")),
        },
        {
            "label": "Average View Duration",
            "value": fmt_duration(youtube.get("average_view_duration")),
        },
    ]
    if include_watch_time:
        metrics.append(
            {"label": "Watch Time Hours", "value": fmt_num(youtube.get("watch_time_hours"))}
        )
    metrics.extend(
        [
            {
                "label": "% of viewers watching 25% or more",
                "value": fmt_percent(youtube.get("pct_25_plus")),
            },
            {
                "label": "% of viewers watching 50% or more",
                "value": fmt_percent(youtube.get("pct_50_plus")),
            },
            {
                "label": "% of viewers watching 90% or more",
                "value": fmt_percent(youtube.get("pct_90_plus")),
            },
        ]
    )
    return metrics


def _normalize_episode_launch_links(data: dict) -> list[dict[str, str]]:
    if "episode_launch_links" in data:
        links = data["episode_launch_links"]
        if isinstance(links, dict):
            return [{"platform": platform, "url": url or ""} for platform, url in links.items()]
        return links

    launch = data.get("episode_launch") or {}
    return [
        {"platform": EPISODE_LAUNCH_LABELS.get(key, key.replace("_", " ").title()), "url": url or ""}
        for key, url in launch.items()
    ]


def _merge_youtube_api_data(youtube: dict, api_data: dict) -> dict:
    merged = {**youtube}
    field_map = {
        "total_views": "view_count",
        "average_percentage_viewed": "average_percentage_viewed",
        "average_view_duration_seconds": "average_view_duration",
        "watch_time_hours": "watch_time_hours",
    }
    for api_key, youtube_key in field_map.items():
        if api_key in api_data and api_data[api_key] is not None:
            merged[youtube_key] = api_data[api_key]

    if "views_by_country" in api_data:
        geography = []
        for country, views in api_data["views_by_country"].items():
            geography.append({"country": country, "views": views})
        if geography:
            merged["geography"] = geography

    return merged


def build_report_context(data: dict) -> dict:
    """Build the Jinja2 context from a report data dictionary."""
    report = data.get("report") or {}
    youtube_full = data.get("youtube_full") or {}
    youtube_highlight = data.get("youtube_highlight") or {}
    email = data.get("email_marketing") or {}
    conversion = data.get("one_click_conversion") or {}

    geography = data.get("geography") or youtube_full.get("geography") or []
    geography_rows = [
        {"country": row.get("country", ""), "views": fmt_num(row.get("views"))}
        for row in geography
    ]

    episode_number = report.get("episode_number", "01")
    if isinstance(episode_number, int):
        episode_number = f"{episode_number:02d}"

    return {
        "report": {
            "year": report.get("year", date.today().year),
            "date_created": fmt_report_date(report.get("date_created")),
            "episode_number": episode_number,
            "episode_section_number": str(report.get("episode_section_number", "1")),
        },
        "footer": data.get("footer", DEFAULT_FOOTER),
        "episode_launch_links": _normalize_episode_launch_links(data),
        "event_promotion": data.get("event_promotion") or [],
        "youtube_full": {
            "title": youtube_full.get("title") or "Full Episode",
            "metrics": _youtube_metrics(youtube_full, include_watch_time=True),
        },
        "youtube_highlight": {
            "title": youtube_highlight.get("title") or "Highlight Episode",
            "metrics": _youtube_metrics(youtube_highlight, include_watch_time=False),
        },
        "geography": geography_rows,
        "email_marketing": {
            "metrics": [
                {
                    "label": "Successful Deliveries",
                    "value": fmt_num(email.get("successful_deliveries")),
                },
                {"label": "Opens", "value": fmt_num(email.get("opens"))},
                {"label": "Open Rate", "value": fmt_percent(email.get("open_rate"))},
                {"label": "Clicks", "value": fmt_num(email.get("clicks"))},
            ]
        },
        "one_click_conversion": {
            "tracking_url": conversion.get("tracking_url") or "N/A",
            "total_clicks": fmt_num(conversion.get("total_clicks")),
        },
    }


def render_html(context: dict, templates_dir: Path = TEMPLATES_DIR) -> str:
    """Render the campaign report HTML string with Jinja2."""
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("campaign_performance_report.html")
    return template.render(**context)


def html_to_pdf(html_string: str, output_path: Path, templates_dir: Path = TEMPLATES_DIR) -> Path:
    """Convert a rendered HTML string to a PDF file using WeasyPrint."""
    HTML(string=html_string, base_url=str(templates_dir)).write_pdf(str(output_path))
    return output_path


def enrich_with_youtube_api(
    data: dict,
    *,
    full_video_id: str | None = None,
    highlight_video_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    credentials_path: Path | None = None,
    token_path: Path | None = None,
) -> dict:
    """Fetch YouTube API metrics and merge them into the report data."""
    enriched = json.loads(json.dumps(data))
    fetch_kwargs: dict = {
        "start_date": start_date,
        "end_date": end_date,
    }
    if credentials_path is not None:
        fetch_kwargs["credentials_path"] = credentials_path
    if token_path is not None:
        fetch_kwargs["token_path"] = token_path

    if full_video_id:
        api_data = fetch_video_metrics(video_id=full_video_id, **fetch_kwargs)
        enriched["youtube_full"] = _merge_youtube_api_data(
            enriched.get("youtube_full") or {},
            api_data,
        )
        if api_data.get("views_by_country"):
            enriched["geography"] = [
                {"country": country, "views": views}
                for country, views in api_data["views_by_country"].items()
            ]

    if highlight_video_id:
        api_data = fetch_video_metrics(video_id=highlight_video_id, **fetch_kwargs)
        enriched["youtube_highlight"] = _merge_youtube_api_data(
            enriched.get("youtube_highlight") or {},
            api_data,
        )

    return enriched


def generate_campaign_report(
    data: dict,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    full_video_id: str | None = None,
    highlight_video_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    credentials_path: Path | None = None,
    token_path: Path | None = None,
) -> Path:
    """Render the report template and write the PDF."""
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

    context = build_report_context(data)
    html_string = render_html(context)
    return html_to_pdf(html_string, output_path)


def load_report_data(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Automated_Campaign_Report.pdf from report JSON data.",
    )
    parser.add_argument(
        "--data-json",
        type=Path,
        default=TEMPLATES_DIR / "report_data.example.json",
        help="Report data JSON file (default: templates/report_data.example.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output PDF path (default: Automated_Campaign_Report.pdf)",
    )
    parser.add_argument(
        "--full-video-id",
        help="Optional YouTube video ID for full episode API enrichment",
    )
    parser.add_argument(
        "--highlight-video-id",
        help="Optional YouTube video ID for highlight API enrichment",
    )
    parser.add_argument("--start-date", help="Analytics start date (YYYY-MM-DD)")
    parser.add_argument(
        "--end-date",
        default=date.today().isoformat(),
        help="Analytics end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        help="Path to OAuth client secrets JSON file",
    )
    parser.add_argument(
        "--token",
        type=Path,
        help="Path to OAuth token JSON file",
    )
    args = parser.parse_args()

    data = load_report_data(args.data_json)
    output_path = generate_campaign_report(
        data,
        output_path=args.output,
        full_video_id=args.full_video_id,
        highlight_video_id=args.highlight_video_id,
        start_date=args.start_date,
        end_date=args.end_date,
        credentials_path=args.credentials,
        token_path=args.token,
    )
    print(f"Report saved to {output_path.resolve()}")


if __name__ == "__main__":
    main()
