#!/usr/bin/env python3
"""Check which credentials are configured for automated report builds."""

import os

CHECKS = [
    ("Constant Contact", ["CONSTANT_CONTACT_ACCESS_TOKEN"]),
    ("Google Ads", [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CUSTOMER_ID",
    ]),
    ("YouTube Analytics", [
        "YOUTUBE_REFRESH_TOKEN",
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
    ]),
    ("YouTube Data API (optional)", ["YOUTUBE_API_KEY"]),
]

def main():
    print("Credential check for automated report builds\n")
    all_ok = True
    for name, vars in CHECKS:
        missing = [v for v in vars if not os.environ.get(v)]
        if missing:
            all_ok = False
            print(f"❌ {name}: missing {', '.join(missing)}")
        else:
            print(f"✅ {name}: configured")
    print()
    if all_ok:
        print("All credentials set — run: python3 scripts/build_report.py links.yaml -o output")
    else:
        print("Add missing secrets at:")
        print("  • Cursor Cloud: https://cursor.com/dashboard/cloud-agents → Secrets")
        print("  • GitHub: https://github.com/althea-ops/reports/settings/secrets/actions")
        print("\nSee SECRETS_SETUP.md for how to get each token.")

if __name__ == "__main__":
    main()
