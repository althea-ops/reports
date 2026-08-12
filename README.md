# reports

Shareable campaign performance reports for clients.

## Quick start (shareable link)

```bash
pip install -r requirements.txt

# 1. Publish a report (creates a shareable link)
python publish_report.py --slug prospex-mn360 --data-json templates/report_data.example.json

# 2. Start the web server
python web_app.py

# 3. Open in browser
#    http://localhost:5000/report/prospex-mn360
```

Send that link to your client — they click it and see all metrics in their browser.

## Deploy online (get a real link, not localhost)

Deploy `web_app.py` to [Render](https://render.com) or [Railway](https://railway.app) (free tiers available).
Set the start command to: `python web_app.py`

Then publish with your public URL:

```bash
python publish_report.py --slug prospex-mn360 --base-url https://your-app.onrender.com
```
