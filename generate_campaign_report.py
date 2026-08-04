#!/usr/bin/env python3
"""Generate a Campaign Performance Report PDF from YouTube API data."""

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
DEFAULT_EMAIL_METRICS = {
    "delivered": None,
    "opens": None,
    "open_rate": None,
    "clicks": None,
    "click_through_rate": None,
    "bounce_rate": None,
    "unsubscribes": None,
}


def fmt_num(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float) and value == int(value):
        return f"{int(value):,}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def fmt_percent(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def fmt_report_date(value: str | None = None) -> str:
    if value:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    else:
        parsed = datetime.combine(date.today(), datetime.min.time())
    return parsed.strftime(f"%B {parsed.day}, %Y")


def build_report_context(
    youtube_metrics: dict,
    email_metrics: dict | None = None,
    *,
    brand: str = "Crownsmen Partners",
    report_title: str = "Campaign Performance Report",
    episode_label: str = "MN 360",
    report_date: str | None = None,
    footer_year: int | None = None,
) -> dict:
    """Map API metrics into the Jinja2 template context."""
    email = {**DEFAULT_EMAIL_METRICS, **(email_metrics or {})}

    return {
        "brand": brand,
        "report_title": report_title,
        "episode_label": episode_label,
        "report_date": fmt_report_date(report_date),
        "footer_year": footer_year or date.today().year,
        "episode": {
            "views": fmt_num(youtube_metrics.get("total_views")),
            "avg_percentage_viewed": fmt_percent(
                youtube_metrics.get("average_percentage_viewed")
            ),
            "watch_time_hours": fmt_num(youtube_metrics.get("watch_time_hours")),
        },
        "email": {
            "delivered": fmt_num(email.get("delivered")),
            "opens": fmt_num(email.get("opens")),
            "open_rate": fmt_percent(email.get("open_rate")),
            "clicks": fmt_num(email.get("clicks")),
            "click_through_rate": fmt_percent(email.get("click_through_rate")),
            "bounce_rate": fmt_percent(email.get("bounce_rate")),
            "unsubscribes": fmt_num(email.get("unsubscribes")),
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


def generate_campaign_report(
    video_id: str,
    output_path: Path = DEFAULT_OUTPUT,
    email_metrics: dict | None = None,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    credentials_path: Path | None = None,
    token_path: Path | None = None,
    episode_label: str = "MN 360",
    report_date: str | None = None,
) -> Path:
    """Fetch YouTube metrics, render the template, and write the PDF report."""
    fetch_kwargs: dict = {
        "video_id": video_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    if credentials_path is not None:
        fetch_kwargs["credentials_path"] = credentials_path
    if token_path is not None:
        fetch_kwargs["token_path"] = token_path

    youtube_metrics = fetch_video_metrics(**fetch_kwargs)
    context = build_report_context(
        youtube_metrics,
        email_metrics,
        episode_label=episode_label,
        report_date=report_date or end_date,
    )
    html_string = render_html(context)
    return html_to_pdf(html_string, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Automated_Campaign_Report.pdf from YouTube video metrics.",
    )
    parser.add_argument("video_id", help="YouTube video ID to include in the report")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output PDF path (default: Automated_Campaign_Report.pdf)",
    )
    parser.add_argument(
        "--email-json",
        type=Path,
        help="Optional JSON file with email marketing metrics",
    )
    parser.add_argument("--start-date", help="Analytics start date (YYYY-MM-DD)")
    parser.add_argument(
        "--end-date",
        default=date.today().isoformat(),
        help="Analytics end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--episode-label",
        default="MN 360",
        help="Episode label shown in the report header",
    )
    parser.add_argument(
        "--report-date",
        help="Report date shown in header (YYYY-MM-DD). Defaults to --end-date.",
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

    email_metrics = None
    if args.email_json:
        email_metrics = json.loads(args.email_json.read_text())

    output_path = generate_campaign_report(
        video_id=args.video_id,
        output_path=args.output,
        email_metrics=email_metrics,
        start_date=args.start_date,
        end_date=args.end_date,
        credentials_path=args.credentials,
        token_path=args.token,
        episode_label=args.episode_label,
        report_date=args.report_date,
    )
    print(f"Report saved to {output_path.resolve()}")


if __name__ == "__main__":
    main()
