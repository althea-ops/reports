#!/usr/bin/env python3
"""Flask web app — share campaign performance reports via client links."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from flask import Flask, abort, render_template

from generate_campaign_report import build_report_context, load_report_data

APP_DIR = Path(__file__).resolve().parent
REPORTS_DIR = APP_DIR / "data" / "reports"

app = Flask(__name__)
app.config["REPORTS_DIR"] = REPORTS_DIR


def _slugify(value: str) -> str:
    slug = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "report"


def report_path(slug: str) -> Path:
    return REPORTS_DIR / f"{slug}.json"


def list_reports() -> list[dict]:
    reports = []
    if not REPORTS_DIR.exists():
        return reports
    for path in sorted(REPORTS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        report = data.get("report") or {}
        reports.append(
            {
                "slug": path.stem,
                "client_name": report.get("client_name", "Untitled Report"),
                "episode_number": report.get("episode_number", ""),
                "date_created": report.get("date_created", ""),
            }
        )
    return reports


@app.route("/")
def index():
    return render_template("index.html", reports=list_reports())


@app.route("/report/<slug>")
def view_report(slug: str):
    path = report_path(slug)
    if not path.exists():
        abort(404)
    data = load_report_data(path)
    context = build_report_context(data)
    return render_template("campaign_performance_report_web.html", **context)


@app.route("/health")
def health():
    return {"status": "ok"}


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
