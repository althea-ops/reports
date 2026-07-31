#!/usr/bin/env python3
"""Build Crownsmen Partners Campaign Performance Report (PPTX + PDF)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_metrics import CampaignMetrics, fetch_all, metrics_to_dict

NAVY = RGBColor(0x1A, 0x2B, 0x4A)
GOLD = RGBColor(0xC9, 0xA2, 0x27)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
MID_GRAY = RGBColor(0x66, 0x66, 0x66)
ACCENT_BLUE = RGBColor(0x2E, 0x6B, 0xA4)


def val(v: int | float | None, suffix: str = "") -> str:
    if v is None:
        return "[TBD]"
    if isinstance(v, float):
        return f"{v:,.1f}{suffix}" if v != int(v) else f"{int(v):,}{suffix}"
    return f"{v:,}{suffix}"


def pct(v: float | None) -> str:
    if v is None:
        return "[TBD]"
    return f"{v:.1f}%"


def money(v: float | None) -> str:
    if v is None:
        return "[TBD]"
    return f"${v:,.2f}"


def set_slide_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header_bar(slide, title: str, subtitle: str = "") -> None:
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(9), Inches(0.6))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE
    if subtitle:
        tb2 = slide.shapes.add_textbox(Inches(0.5), Inches(0.65), Inches(9), Inches(0.35))
        p2 = tb2.text_frame.paragraphs[0]
        p2.text = subtitle
        p2.font.size = Pt(14)
        p2.font.color.rgb = GOLD


def add_footer(slide, text: str) -> None:
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(9), Inches(0.4))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(9)
    p.font.color.rgb = MID_GRAY
    p.alignment = PP_ALIGN.RIGHT


def add_metric_box(slide, left, top, width, height, label: str, value: str, highlight: bool = False) -> None:
    box = slide.shapes.add_shape(1, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = GOLD if highlight else LIGHT_GRAY
    box.line.color.rgb = GOLD if highlight else RGBColor(0xDD, 0xDD, 0xDD)
    tb = slide.shapes.add_textbox(left + Inches(0.12), top + Inches(0.08), width - Inches(0.24), height - Inches(0.16))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = label
    p1.font.size = Pt(10)
    p1.font.color.rgb = MID_GRAY if not highlight else NAVY
    p2 = tf.add_paragraph()
    p2.text = value
    p2.font.size = Pt(20 if highlight else 16)
    p2.font.bold = True
    p2.font.color.rgb = NAVY


def add_table(slide, left, top, width, rows: list[list[str]], col_widths: list[float] | None = None, row_height: float = 0.32) -> None:
    if not rows:
        return
    n_rows, n_cols = len(rows), len(rows[0])
    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, Inches(row_height * n_rows))
    table = table_shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)
    for r, row in enumerate(rows):
        for c, cell_text in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(cell_text)
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(9)
                paragraph.font.color.rgb = WHITE if r == 0 else DARK_GRAY
                if r == 0:
                    paragraph.font.bold = True
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
            elif r % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT_GRAY


def _main_video_id(metrics: CampaignMetrics) -> str | None:
    for y in metrics.youtube:
        if y.extra.get("type") == "main":
            return y.extra.get("video_id")
    return metrics.youtube[0].extra.get("video_id") if metrics.youtube else None


def _email_val(email: dict, *keys: str):
    for k in keys:
        if email.get(k) is not None:
            return email[k]
    return None


def build_presentation(metrics: CampaignMetrics) -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    campaign = metrics.campaign
    client = campaign.get("client", "Client")
    episode = campaign.get("episode", "")
    title = campaign.get("title", "")
    series = campaign.get("series", "")
    report_date = campaign.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    footer = f"Crownsmen Partners | Confidential | {report_date}"

    main_yt = next((y for y in metrics.youtube if y.extra.get("type") == "main"), metrics.youtube[0] if metrics.youtube else None)
    main_vid = _main_video_id(metrics)
    ya = metrics.youtube_analytics.get(main_vid, {}) if main_vid else {}
    total_yt_views = sum(y.views or 0 for y in metrics.youtube)
    total_li_reactions = sum(s.reactions or 0 for s in metrics.social if s.platform == "LinkedIn")
    email = metrics.email
    ads = metrics.google_ads

    # Slide 1: Cover
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY)
    tb = slide.shapes.add_textbox(Inches(0.75), Inches(1.5), Inches(8.5), Inches(1.2))
    p = tb.text_frame.paragraphs[0]
    p.text = "Campaign Performance Report"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    tb2 = slide.shapes.add_textbox(Inches(0.75), Inches(2.8), Inches(8.5), Inches(1.5))
    tf2 = tb2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = f"{episode}. {client}"
    p2.font.size = Pt(28)
    p2.font.color.rgb = GOLD
    p3 = tf2.add_paragraph()
    p3.text = title
    p3.font.size = Pt(20)
    p3.font.color.rgb = WHITE
    tb3 = slide.shapes.add_textbox(Inches(0.75), Inches(4.8), Inches(8.5), Inches(1.0))
    tf3 = tb3.text_frame
    p4 = tf3.paragraphs[0]
    p4.text = series
    p4.font.size = Pt(16)
    p4.font.color.rgb = RGBColor(0xAA, 0xBB, 0xCC)
    p5 = tf3.add_paragraph()
    p5.text = f"Report Date: {report_date}"
    p5.font.size = Pt(14)
    p5.font.color.rgb = RGBColor(0xAA, 0xBB, 0xCC)

    # Slide 2: Executive Summary
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "Executive Summary", f"{episode} — {client}")
    add_metric_box(slide, Inches(0.5), Inches(1.4), Inches(2.1), Inches(1.0), "Video Views", val(ya.get("video_views") or (main_yt.views if main_yt else None)), True)
    add_metric_box(slide, Inches(2.8), Inches(1.4), Inches(2.1), Inches(1.0), "Watch Time (hrs)", val(ya.get("watch_time_hours")))
    add_metric_box(slide, Inches(5.1), Inches(1.4), Inches(2.1), Inches(1.0), "Avg % Viewed", pct(ya.get("average_percentage_viewed")))
    add_metric_box(slide, Inches(7.4), Inches(1.4), Inches(2.1), Inches(1.0), "Email Open Rate", pct(_email_val(email, "open_rate")))
    add_metric_box(slide, Inches(0.5), Inches(2.6), Inches(2.1), Inches(1.0), "Email Opens", val(_email_val(email, "opens", "unique_opens")))
    add_metric_box(slide, Inches(2.8), Inches(2.6), Inches(2.1), Inches(1.0), "Email Clicks", val(_email_val(email, "clicks", "unique_clicks")))
    add_metric_box(slide, Inches(5.1), Inches(2.6), Inches(2.1), Inches(1.0), "LinkedIn Reactions", val(total_li_reactions))
    add_metric_box(slide, Inches(7.4), Inches(2.6), Inches(2.1), Inches(1.0), "Google Ads Clicks", val(ads.get("clicks")))
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(3.9), Inches(9), Inches(2.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Campaign Overview"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY
    for line in [
        "• Full episode + clips on YouTube; syndicated to podcast and social channels",
        "• Email via Constant Contact; paid promotion via Google Ads",
        f"• Landing page: crownsmen.com/equify-financial-construction-equipment-financing/",
    ]:
        bp = tf.add_paragraph()
        bp.text = line
        bp.font.size = Pt(11)
        bp.font.color.rgb = DARK_GRAY
    add_footer(slide, footer)

    # Slide 3: YouTube — Video Views
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "YouTube — Video Views", "Crownsmen Partners Channel")
    yt_rows = [["Video", "Type", "Video Views"]]
    for yt in metrics.youtube:
        short = (yt.title or "Untitled")[:50]
        yt_rows.append([short, yt.extra.get("type", "").title(), val(yt.views)])
    add_table(slide, Inches(0.4), Inches(1.3), Inches(9.2), yt_rows, [5.5, 1.2, 1.5])
    add_metric_box(slide, Inches(0.5), Inches(4.2), Inches(2.8), Inches(1.0), "Main Episode Views", val(main_yt.views if main_yt else None), True)
    add_metric_box(slide, Inches(3.5), Inches(4.2), Inches(2.8), Inches(1.0), "Total YouTube Views", val(total_yt_views))
    add_footer(slide, footer)

    # Slide 4: YouTube Analytics & Retention
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "YouTube Analytics & Retention", main_yt.title[:60] if main_yt and main_yt.title else "Main Episode")
    add_metric_box(slide, Inches(0.4), Inches(1.3), Inches(2.2), Inches(1.0), "Video Views", val(ya.get("video_views") or (main_yt.views if main_yt else None)), True)
    add_metric_box(slide, Inches(2.8), Inches(1.3), Inches(2.2), Inches(1.0), "Avg % Viewed", pct(ya.get("average_percentage_viewed")))
    add_metric_box(slide, Inches(5.2), Inches(1.3), Inches(2.2), Inches(1.0), "Avg View Duration", ya.get("average_view_duration") or "[TBD]")
    add_metric_box(slide, Inches(7.6), Inches(1.3), Inches(2.0), Inches(1.0), "Watch Time (hrs)", val(ya.get("watch_time_hours")))
    add_metric_box(slide, Inches(0.4), Inches(2.5), Inches(2.8), Inches(1.0), "≥25% Watched", pct(ya.get("pct_watched_25")))
    add_metric_box(slide, Inches(3.4), Inches(2.5), Inches(2.8), Inches(1.0), "≥50% Watched", pct(ya.get("pct_watched_50")))
    add_metric_box(slide, Inches(6.4), Inches(2.5), Inches(2.8), Inches(1.0), "≥90% Watched", pct(ya.get("pct_watched_90")))
    ret_rows = [["Retention Threshold", "Value"]]
    for label, key in [("25% or more of video", "pct_watched_25"), ("50% or more of video", "pct_watched_50"), ("90% or more of video", "pct_watched_90")]:
        ret_rows.append([label, pct(ya.get(key))])
    add_table(slide, Inches(0.4), Inches(3.8), Inches(5.5), ret_rows, [3.5, 1.5])
    add_footer(slide, footer)

    # Slide 5: YouTube Geography
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "YouTube Geography", "Views by Country")
    geo = ya.get("geography", [])
    geo_rows = [["Country", "Views", "Avg View Duration", "Watch Time (hrs)"]]
    for g in geo[:12]:
        geo_rows.append([
            g.get("country", "—"),
            val(g.get("views")),
            g.get("average_view_duration") or "[TBD]",
            val(g.get("watch_time_hours")),
        ])
    if len(geo_rows) == 1:
        geo_rows.append(["[TBD]", "[TBD]", "[TBD]", "[TBD]"])
    totals = ya.get("geography_totals", {})
    geo_rows.append([
        "TOTAL",
        val(totals.get("views")),
        totals.get("average_view_duration") or "[TBD]",
        val(totals.get("watch_time_hours")),
    ])
    add_table(slide, Inches(0.4), Inches(1.3), Inches(9.2), geo_rows, [2.0, 1.5, 2.5, 2.0], row_height=0.30)
    add_footer(slide, footer)

    # Slide 6: LinkedIn
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "Social Media — LinkedIn", "Organic Posts")
    li_rows = [["Account", "Reactions", "Comments", "Impressions", "Clicks"]]
    for s in metrics.social:
        if s.platform == "LinkedIn":
            li_rows.append([s.account or "LinkedIn", val(s.reactions), val(s.comments), val(s.impressions), val(s.clicks)])
    add_table(slide, Inches(0.4), Inches(1.5), Inches(9.2), li_rows, [3.0, 1.5, 1.5, 1.5, 1.2])
    add_footer(slide, footer)

    # Slide 7: Other Social + Podcast
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "Social & Podcast Distribution", "Facebook | Instagram | Threads | X | Podcast")
    soc_rows = [["Platform", "Account", "Engagement", "Comments"]]
    for s in metrics.social:
        if s.platform != "LinkedIn":
            eng = s.likes or s.reactions or s.views
            soc_rows.append([s.platform, s.account or "—", val(eng), val(s.comments)])
    add_table(slide, Inches(0.4), Inches(1.3), Inches(4.4), soc_rows, [1.2, 1.2, 1.0, 0.8], row_height=0.28)
    pod_rows = [["Platform", "Episode", "Plays"]]
    for p in metrics.podcast:
        pod_rows.append([p.platform, (p.title or "CS 67")[:28], val(p.plays or p.views)])
    add_table(slide, Inches(5.0), Inches(1.3), Inches(4.4), pod_rows, [1.2, 2.0, 0.8], row_height=0.28)
    add_footer(slide, footer)

    # Slide 8: Constant Contact (exact fields requested)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "Email Marketing", "Constant Contact via Zapier")
    deliveries = _email_val(email, "successful_deliveries", "delivered")
    opens = _email_val(email, "opens", "unique_opens")
    clicks = _email_val(email, "clicks", "unique_clicks")
    open_rate = _email_val(email, "open_rate")
    add_metric_box(slide, Inches(0.5), Inches(1.5), Inches(2.1), Inches(1.3), "Successful Deliveries", val(deliveries), True)
    add_metric_box(slide, Inches(2.8), Inches(1.5), Inches(2.1), Inches(1.3), "Opens", val(opens))
    add_metric_box(slide, Inches(5.1), Inches(1.5), Inches(2.1), Inches(1.3), "Open Rate", pct(open_rate))
    add_metric_box(slide, Inches(7.4), Inches(1.5), Inches(2.1), Inches(1.3), "Clicks", val(clicks))
    cc_rows = [["Metric", "Value"]]
    for label, v in [
        ("Successful Deliveries", val(deliveries)),
        ("Opens", val(opens)),
        ("Open Rate", pct(open_rate)),
        ("Clicks", val(clicks)),
        ("Campaign Name", email.get("campaign_name") or "[TBD]"),
        ("Subject Line", (email.get("subject_line") or "[TBD]")[:50]),
    ]:
        cc_rows.append([label, str(v)])
    add_table(slide, Inches(0.5), Inches(3.2), Inches(6), cc_rows, [2.5, 3.0])
    add_footer(slide, footer)

    # Slide 9: Google Ads (Clicks to URL, Landing Page URL)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "Google Ads", "Paid Media via Zapier")
    ads_list = ads.get("ads") or ads.get("url_clicks") or []
    if isinstance(ads_list, dict):
        ads_list = [ads_list]
    ads_rows = [["Ad / Campaign", "Clicks to URL", "Landing Page URL"]]
    if ads_list:
        for row in ads_list:
            ads_rows.append([
                row.get("name") or row.get("campaign") or "—",
                val(row.get("clicks") or row.get("clicks_to_url")),
                (row.get("landing_page_url") or row.get("final_url") or "[TBD]")[:45],
            ])
    elif ads.get("clicks") is not None:
        ads_rows.append([
            ads.get("campaign_name") or "Campaign",
            val(ads.get("clicks")),
            ads.get("landing_page_url") or campaign.get("landing_page") or "[TBD]",
        ])
    else:
        ads_rows.append(["[TBD]", "[TBD]", campaign.get("landing_page", "[TBD]")[:45]])
    add_table(slide, Inches(0.4), Inches(1.4), Inches(9.2), ads_rows, [2.5, 1.5, 4.5], row_height=0.35)
    add_metric_box(slide, Inches(0.5), Inches(4.5), Inches(2.2), Inches(1.0), "Total Clicks", val(ads.get("clicks")), True)
    add_metric_box(slide, Inches(2.9), Inches(4.5), Inches(2.2), Inches(1.0), "Impressions", val(ads.get("impressions")))
    add_metric_box(slide, Inches(5.3), Inches(4.5), Inches(2.2), Inches(1.0), "CTR", pct(ads.get("ctr")))
    add_metric_box(slide, Inches(7.7), Inches(4.5), Inches(1.8), Inches(1.0), "Cost", money(ads.get("cost")))
    add_footer(slide, footer)

    # Slide 10: Summary
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_header_bar(slide, "Summary & Key Takeaways", f"{client} — {episode}")
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(5.5), Inches(5.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Performance Highlights"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY
    highlights = []
    if main_yt and main_yt.views:
        highlights.append(f"Main episode: {main_yt.views:,} video views")
    if ya.get("watch_time_hours"):
        highlights.append(f"Watch time: {ya['watch_time_hours']:,.1f} hours")
    if ya.get("average_percentage_viewed"):
        highlights.append(f"Average % viewed: {ya['average_percentage_viewed']:.1f}%")
    if opens:
        highlights.append(f"Email opens: {opens:,} ({pct(open_rate)})")
    if total_li_reactions:
        highlights.append(f"LinkedIn reactions: {total_li_reactions}")
    if not highlights:
        highlights.append("Campaign distributed across YouTube, email, social, and paid channels")
    for h in highlights:
        hp = tf.add_paragraph()
        hp.text = f"✓  {h}"
        hp.font.size = Pt(12)
        hp.font.color.rgb = DARK_GRAY
        hp.space_before = Pt(4)
    p2 = tf.add_paragraph()
    p2.text = "\nData Gaps"
    p2.font.size = Pt(13)
    p2.font.bold = True
    p2.font.color.rgb = NAVY
    for gap in (metrics.missing[:6] or ["All key metrics collected"]):
        gp = tf.add_paragraph()
        gp.text = f"• {gap[:75]}{'...' if len(gap) > 75 else ''}"
        gp.font.size = Pt(9)
        gp.font.color.rgb = MID_GRAY
    add_metric_box(slide, Inches(6.3), Inches(1.6), Inches(3.2), Inches(0.9), "Video Views", val(ya.get("video_views") or (main_yt.views if main_yt else None)), True)
    add_metric_box(slide, Inches(6.3), Inches(2.7), Inches(3.2), Inches(0.9), "Watch Time (hrs)", val(ya.get("watch_time_hours")))
    add_metric_box(slide, Inches(6.3), Inches(3.8), Inches(3.2), Inches(0.9), "Email Opens", val(opens))
    add_metric_box(slide, Inches(6.3), Inches(4.9), Inches(3.2), Inches(0.9), "Google Ads Clicks", val(ads.get("clicks")))
    add_footer(slide, footer)

    return prs


def write_missing_data(metrics: CampaignMetrics, output_path: Path) -> None:
    lines = [
        "# Missing Data Report",
        "",
        f"Generated: {metrics.fetched_at}",
        f"Campaign: {metrics.campaign.get('episode', '')} — {metrics.campaign.get('client', '')}",
        "",
        "## Required Metrics",
        "",
        "### YouTube Analytics",
        "- Video Views",
        "- Average Percentage Viewed",
        "- Average View Duration",
        "- Watch Time Hours",
        "- % viewers watching 25% / 50% / 90% or more",
        "- Geography: country, views, avg duration, watch time + totals",
        "",
        "### Constant Contact (via Zapier)",
        "- Successful Deliveries",
        "- Opens",
        "- Open Rate",
        "- Clicks",
        "",
        "### Google Ads (via Zapier)",
        "- Clicks to URL",
        "- Landing Page URL",
        "",
    ]
    if metrics.missing:
        lines.extend(["## Still Missing", ""])
        for i, item in enumerate(metrics.missing, 1):
            lines.append(f"{i}. {item}")
        lines.append("")
    lines.extend([
        "## Pull via Desktop Cursor + Zapier",
        "",
        "1. Open repo in Desktop Cursor (Zapier MCP connected)",
        "2. Run agent with prompt from `output/zapier/README.md`",
        "3. Save to `output/zapier/*.json` and rebuild",
        "",
    ])
    output_path.write_text("\n".join(lines) + "\n")


def export_pdf(pptx_path: Path, pdf_path: Path) -> bool:
    try:
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", str(pdf_path.parent), str(pptx_path)],
            check=True, capture_output=True, timeout=120,
        )
        generated = pptx_path.with_suffix(".pdf")
        if generated.exists() and generated != pdf_path:
            generated.rename(pdf_path)
        return pdf_path.exists()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"PDF export failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Crownsmen Campaign Performance Report")
    parser.add_argument("config", nargs="?", default="links.yaml")
    parser.add_argument("-o", "--output", default="output")
    parser.add_argument("--metrics-file", help="Use pre-fetched metrics JSON")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.metrics_file:
        from fetch_metrics import MetricResult
        data = json.loads(Path(args.metrics_file).read_text())
        metrics = CampaignMetrics(
            fetched_at=data["fetched_at"],
            campaign=data["campaign"],
            youtube=[MetricResult(**y) for y in data.get("youtube", [])],
            youtube_analytics=data.get("youtube_analytics", {}),
            social=[MetricResult(**s) for s in data.get("social", [])],
            podcast=[MetricResult(**p) for p in data.get("podcast", [])],
            email=data.get("email", {}),
            google_ads=data.get("google_ads", {}),
            analytics=data.get("analytics", {}),
            missing=data.get("missing", []),
        )
    else:
        print("Fetching metrics from all URLs...")
        metrics = fetch_all(args.config)

    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics_to_dict(metrics), indent=2))

    campaign = metrics.campaign
    slug = f"Crownsmen_Partners_Campaign_Performance_Report__{campaign.get('episode', 'CS').replace(' ', '_')}_-_{campaign.get('client', 'Client').replace(' ', '_')}"
    pptx_path = output_dir / f"{slug}.pptx"
    pdf_path = output_dir / f"{slug}.pdf"

    print("Building PowerPoint presentation...")
    prs = build_presentation(metrics)
    prs.save(str(pptx_path))
    print(f"Presentation saved to {pptx_path}")

    write_missing_data(metrics, output_dir / "missing_data.md")

    print("Exporting PDF...")
    if export_pdf(pptx_path, pdf_path):
        print(f"PDF saved to {pdf_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
