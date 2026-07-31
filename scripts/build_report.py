#!/usr/bin/env python3
"""End-to-end: pull data from links.yaml → PowerPoint + PDF report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from collect_report_data import collect_all  # noqa: E402
from generate_report import generate  # noqa: E402


def slugify(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_")


def convert_to_pdf(pptx_path: Path, output_dir: Path) -> Path | None:
    for cmd in ("libreoffice", "soffice"):
        try:
            subprocess.run(
                [cmd, "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx_path)],
                check=True,
                capture_output=True,
                timeout=120,
            )
            pdf_path = output_dir / f"{pptx_path.stem}.pdf"
            if pdf_path.exists():
                return pdf_path
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def build(links_path: Path, output_dir: Path, skip_collect: bool = False) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "collected.json"

    if skip_collect and data_path.exists():
        data = json.loads(data_path.read_text(encoding="utf-8"))
    else:
        data = collect_all(links_path)
        data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report = data.get("report") or {}
    client = slugify(str(report.get("client_name", "Client")))
    episode = report.get("episode_number", "000")
    base_name = f"{client}_Campaign_Performance_Report_MN_{episode}_Crownsmen_Partners"

    pptx_path = output_dir / f"{base_name}.pptx"
    generate(data, pptx_path)

    pdf_path = convert_to_pdf(pptx_path, output_dir)
    if pdf_path is None:
        pdf_path = output_dir / f"{base_name}.pdf"  # expected path even if missing

    missing = output_dir / "missing_data.md"
    missing.write_text(build_missing_report(data, pdf_path.exists()), encoding="utf-8")

    outputs: dict[str, Path] = {"pptx": pptx_path, "json": data_path, "missing": missing}
    if pdf_path.exists():
        outputs["pdf"] = pdf_path

    return outputs


def build_missing_report(data: dict, pdf_ok: bool) -> str:
    lines = ["# Missing Data\n"]

    for key, label in (("youtube_full", "YouTube Full Episode"), ("youtube_highlight", "YouTube Highlight")):
        yt = data.get(key) or {}
        if yt.get("view_count") is None:
            lines.append(f"- **{label} view count** — set `YOUTUBE_API_KEY`")
        if yt.get("average_percentage_viewed") is None:
            lines.append(f"- **{label} retention/watch time/geography** — YouTube Analytics OAuth or Studio CSV export")

    email = data.get("email_marketing") or {}
    if email.get("opens") is None:
        lines.append("- **Email marketing stats** — Constant Contact API / Zapier MCP")

    conv = data.get("one_click_conversion") or {}
    if conv.get("total_clicks") is None:
        lines.append("- **Conversion clicks** — client GA4 / analytics dashboard")

    if not pdf_ok:
        lines.append("- **PDF export** — install LibreOffice (`libreoffice`) for automatic PDF conversion; `.pptx` was generated")

    if len(lines) == 1:
        lines.append("All metrics collected successfully.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Crownsmen campaign performance report (PPTX + PDF)")
    parser.add_argument("links", nargs="?", default="links.yaml", help="Path to links.yaml")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("--skip-collect", action="store_true", help="Reuse existing collected.json")
    args = parser.parse_args()

    links_path = Path(args.links)
    if not links_path.exists():
        print(f"Error: {links_path} not found. Copy templates/links.example.yaml to links.yaml", file=sys.stderr)
        sys.exit(1)

    outputs = build(links_path, Path(args.output), skip_collect=args.skip_collect)

    print("Report generated:")
    for kind, path in outputs.items():
        if path.exists():
            print(f"  {kind.upper()}: {path}")
        else:
            print(f"  {kind.upper()}: (not created)")


if __name__ == "__main__":
    main()
