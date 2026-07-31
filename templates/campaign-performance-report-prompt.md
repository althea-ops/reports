# Cursor Prompt: Crownsmen Partners Campaign Performance Report

Copy everything below the line into Cursor each time you generate a new client episode report. Fill in the `[INPUTS]` section first, attach your reference PDF if needed, and run.

---

## PROMPT START — copy from here

You are generating a **Crownsmen Partners Campaign Performance Report** for a client episode promotion. Match the structure, tone, and layout of the attached sample report exactly:

**Reference format:** `@Crownsmen_Partners_Campaign_Performance_Report__MN_360_-_Prospex_Group-compressed.pdf`

---

### CLIENT & EPISODE INPUTS (I will fill these in each time)

```
Report year: [e.g. 2026]
Date created: [MM/DD/YYYY]
Client name: [e.g. ProspEx Group]
Episode show: [e.g. Mining NOW / MN 360]
Episode number: [e.g. #360]
Episode title: [Full episode title]
Highlight title: [YouTube highlight video title]

--- Promotional Links: Episode Launch (Platform → URL) ---
YouTube (Full Episode):
YouTube (Highlight):
LinkedIn – Crownsmen Partners:
LinkedIn – Mining Now:
Facebook:
Instagram:
Threads:
X (Twitter):
Spotify:
Rumble:
Crownsmen Website:
Apple Podcasts:
LinkedIn Newsletter:
Email:

--- Promotional Links: Event (Content Type → Link → Remarks) ---
Email (Filming Schedule): [URL] | [remarks or —]
Post (Filming Schedule): [URL] | [where else it was posted]
Behind-the-Scenes Images: [URL] | [where else it was posted]
Coming Soon Reel: [URL] | [where else it was posted]

--- YouTube: Full Episode Statistics ---
Video Views:
Average Percentage Viewed:
Average View Duration: [M:SS]
Watch Time Hours:
% of viewers watching 25% or more:
% of viewers watching 50% or more:
% of viewers watching 90% or more:

--- YouTube: Highlight Episode Statistics ---
Video Views:
Average Percentage Viewed:
Average View Duration: [M:SS]
% of viewers watching 25% or more:
% of viewers watching 50% or more:
% of viewers watching 90% or more:

--- YouTube Geography ---
[Paste top countries/regions and view counts, or attach screenshot/export from YouTube Studio]

--- Email Marketing ---
Successful Deliveries:
Opens:
Open Rate:
Clicks:

--- One-Click Conversion ---
Tracking URL used:
Total # Clicks to Website:
```

---

### OUTPUT REQUIREMENTS

Produce a **10-slide presentation** (PowerPoint `.pptx` preferred; if not possible, provide slide-by-slide markdown + a Python script using `python-pptx` to generate the file).

Use this **exact slide order and content structure**:

| Slide | Title | Content |
|-------|-------|---------|
| 1 | Cover | "Campaign Performance Report [YEAR]" · © 2018 Crownsmen Partners \| www.crownsmen.com \| info@crownsmen.com · Date Created [date] |
| 2 | Report Content | "Episode Performance 01" (table of contents style) |
| 3 | Promotional Links - Episode Launch | Two-column table: **Platform Name** \| **URL** (all 14 platforms listed above) |
| 4 | Promotional Links - Event | Three-column table: **Content Type** \| **Link** \| **Remarks** |
| 5 | Episode Performance | Section divider — "Episode Performance" with episode number |
| 6 | YouTube \| Full Episode Statistics | Episode title as subtitle · Metrics table: Video Views, Average Percentage Viewed, Average View Duration, Watch Time Hours, % watching 25%+/50%+/90%+ |
| 7 | YouTube \| Highlight Episode Statistics | Highlight title as subtitle · Same metrics except no Watch Time Hours |
| 8 | YouTube \| Geography | Bar chart or table of top viewing countries/regions from the geography input |
| 9 | Email Marketing + One-Click Conversion | Two sections on one slide: Email stats (Successful Deliveries, Opens, Open Rate, Clicks) · One-Click Conversion (URL Used, Total # Clicks to Website) |
| 10 | Thank You | © 2018 Crownsmen Partners \| www.crownsmen.com \| info@crownsmen.com |

---

### DESIGN & FORMATTING RULES

- **Brand:** Crownsmen Partners — professional, clean, minimal. Match the sample deck's layout hierarchy (large section titles, metric labels left / values right).
- **Tables:** Use clear headers. URLs must be full clickable links (not truncated in the source data file; truncate visually in slides only if needed).
- **Numbers:** Use comma separators for thousands (e.g. 25,385). Percentages include the % symbol.
- **Durations:** Format as `M:SS` (e.g. 5:34).
- **Do not invent data.** If any input above is missing, leave a clearly marked `[TBD]` placeholder and list what's still needed at the end.
- **File naming:** `[ClientName]_Campaign_Performance_Report_[ShowAbbrev]_[EpisodeNumber]_Crownsmen_Partners.pptx`

---

### DELIVERABLES

1. The completed `.pptx` file (or generation script + instructions to build it).
2. A brief checklist of any `[TBD]` fields I still need to provide.
3. Optional: export a PDF version if the toolchain supports it.

Generate the report now using the inputs I provided above.

## PROMPT END
