# Crownsmen Campaign Report

## Easiest way (2 steps)

### Step 1 — Open this folder in Cursor on your computer
- Download from GitHub: https://github.com/althea-ops/reports
- In Cursor: **File → Open Folder** → select the `reports` folder

### Step 2 — Tell the agent one sentence
Open the **Agent** chat (make sure you're NOT using Cloud Agent) and type:

```
build my report
```

That's it. The agent will:
1. Pull Constant Contact, Google Ads, and YouTube Analytics via your Zapier connection
2. Build the PowerPoint and PDF
3. Tell you where to find them

Your finished files will be in the **`output/`** folder:
- `Crownsmen_Partners_Campaign_Performance_Report__CS_67_-_Equify_Financial.pptx`
- `Crownsmen_Partners_Campaign_Performance_Report__CS_67_-_Equify_Financial.pdf`

---

## Don't have the repo yet?

Open **Terminal** on your Mac and paste this one line:

```bash
git clone https://github.com/althea-ops/reports.git ~/reports && cd ~/reports && git checkout cursor/equify-cs67-campaign-report-13d4
```

Then in Cursor: **File → Open Folder** → choose `reports` (in your home folder).

---

## What's already done (no action needed)

The report template is built. YouTube video views are already filled in:
- Main episode: **52,895 views**
- 10-slide deck matching the Crownsmen format

What's left (email, Google Ads, YouTube analytics) gets pulled automatically when you say **"build my report"** in Desktop Cursor with Zapier connected.

---

## Zapier not connected?

In Cursor: **Settings → Tools & MCP → Connect** next to Zapier. Then say **"build my report"** again.
