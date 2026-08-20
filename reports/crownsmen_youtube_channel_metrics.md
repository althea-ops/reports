# Crownsmen Partners YouTube channel snapshot

**As of 2026-08-20** · [@CrownsmenPartners](https://www.youtube.com/@CrownsmenPartners) · 26.4K subscribers

Pulled from public YouTube data (channel listings + watch pages). This is **not** YouTube Studio / Analytics.

## Direct answers

### 1. Avg engagement on long form across the episodes

**0.045% pooled like-rate** across **816** long-form episodes (≥8 minutes).

| | All episodes | Episodes with ≥1,000 views |
|---|---:|---:|
| Videos | 816 | 736 |
| Avg views | 27,913 | 30,926 |
| Median views | 30,109 | 30,291 |
| Avg duration | 38.6 min | 40.9 min |
| Avg likes | 12.5 | 13.3 |
| Median like-rate | 0.038% | 0.034% |
| Pooled like-rate (likes ÷ views) | 0.045% | 0.043% |

Like-rate is the public engagement proxy: likes ÷ views. Crownsmen campaign decks use **average % viewed** from Studio (e.g. MN 360 full episode 39%). That number is **not** in public data.

### 2. Avg engagement on long form across the highlights (the ones we promote)

Promoted highlights are the 1–5 minute long-form clips that break ~1,000 views. Organic highlight cuts on this channel mostly stay under 100 views; the 1.2k–3.5k cluster matches past paid clips (Equify CS 67 clips ~1.6k–2.1k, ProspEx highlight 2,566).

| | All 1–5 min highlights | Promoted (≥1,000 views) | Tight paid cluster (1.2k–3.5k) |
|---|---:|---:|---:|
| Videos | 911 | 186 | 145 |
| Avg views | 765 | 3,348 | 1,866 |
| Median views | 78 | 1,896 | 1,739 |
| Avg duration | 3.1 min | 2.8 min | 2.8 min |
| Avg likes | 1.6 | 1.7 | 1.4 |
| Median like-rate | 0.042% | 0.000% | 0.000% |
| Pooled like-rate | 0.205% | 0.052% | 0.074% |

**Promoted highlights: 0.052% pooled like-rate**, median **0.000%** (many paid-view clips have 0 public likes). Studio average % viewed on highlights is typically much higher (MN 360 highlight was 79%) because the videos are short — that metric still needs Analytics.

### 3. Avg views on the 50k ones — yes, about **50.6k**

YouTube rounds these to 50K / 50.5K on the surface. Exact public counts:

| Band | Videos | Exact avg views | Median |
|---|---:|---:|---:|
| **50,000–50,999** (the 50.5K bucket) | 18 | **50,569** | 50,644 |
| 49,000–51,999 | 31 | 50,916 | 50,884 |
| 45,000–54,999 | 69 | 49,998 | 50,691 |

The 50,000–50,999 group averages **50.6k**. Like-rate on that band is very low (0.017% pooled), which is consistent with paid view volume.

The Crownsmen Show long-form set (40 TCS episodes) has median views **50,256** — same 50k neighborhood.

## Channel totals (public)

- **1,924** videos on the Videos tab · **23,661,850** exact views · **12,417** likes
- **402** Shorts · ~391,862 views (rounded listing counts)
- Long-form episodes account for **22,776,728** of those views

## All public data this snapshot includes

- Exact views, likes, duration, title, URL, premiere date text
- Episode vs highlight vs mid-clip vs short, classified by duration
- CSV of every Videos-tab video: `data/crownsmen_youtube_videos.csv`
- Machine-readable summary: `data/crownsmen_youtube_summary.json`

## What we cannot get without YouTube Analytics (Studio OAuth)

These are the metrics in Crownsmen campaign reports, and they are **not** public:

- Average percentage viewed / average view duration / watch time hours
- Retention at 25% / 50% / 90%
- Impressions, CTR, traffic sources (including ads)
- Geography
- Unique viewers, subscribers gained, shares, engaged views, revenue
- Comment counts (not present in the public watch payload)
- A confirmed paid-promotion flag (inferred here from the view clusters)

To fill Studio engagement, connect YouTube Analytics on Desktop Cursor (`credentials.json` / `token.json` as in `youtube_video_report.py` on PR #4) or authenticate Zapier with a YouTube Analytics action.
