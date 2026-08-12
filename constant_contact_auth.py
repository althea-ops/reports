#!/usr/bin/env python3
"""One-time Constant Contact OAuth setup — saves tokens to constant_contact_token.json.

Before running:
1. Create an app at https://app.constantcontact.com/pages/dma/portal/
2. Choose Authorization Code Flow + Long Lived Refresh Tokens
3. Add redirect URI: http://localhost:8888/callback
4. Copy API Key + Client Secret into constant_contact_credentials.json (see example file)
"""

from __future__ import annotations

import json
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

APP_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = APP_DIR / "constant_contact_credentials.json"
TOKEN_FILE = APP_DIR / "constant_contact_token.json"
REDIRECT_URI = "http://localhost:8888/callback"
AUTH_URL = "https://authz.constantcontact.com/oauth2/default/v1/authorize"
TOKEN_URL = "https://authz.constantcontact.com/oauth2/default/v1/token"
SCOPES = "contact_data campaign_data offline_access"


def load_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Missing {CREDENTIALS_FILE.name}. "
            f"Copy constant_contact_credentials.example.json and fill in your API Key and Client Secret."
        )
    return json.loads(CREDENTIALS_FILE.read_text())


def build_auth_url(client_id: str, state: str = "crownsmen-reports") -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    credentials = load_credentials()
    client_id = credentials["client_id"]
    client_secret = credentials["client_secret"]

    auth_code: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if "code" in params:
                auth_code["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Success!</h2><p>You can close this tab and return to the terminal.</p>"
                )
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed.")

        def log_message(self, format, *args):  # noqa: A003
            return

    auth_url = build_auth_url(client_id)
    print("\n=== Constant Contact OAuth Setup ===\n")
    print("1. A browser window will open.")
    print("2. Log in with your Constant Contact account and click Allow.")
    print("3. Tokens will be saved automatically.\n")
    print(f"If the browser does not open, paste this URL:\n{auth_url}\n")

    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8888), CallbackHandler)
    print("Waiting for authorization...")
    server.handle_request()

    if "code" not in auth_code:
        raise RuntimeError("No authorization code received. Try again.")

    tokens = exchange_code_for_tokens(client_id, client_secret, auth_code["code"])
    TOKEN_FILE.write_text(json.dumps(tokens, indent=2))

    print(f"\nTokens saved to: {TOKEN_FILE}")
    print("\nWhat you got:")
    print(f"  access_token  (expires in ~24 hours)")
    print(f"  refresh_token (use this long-term — do not lose it!)")
    print("\nKeep both files private — never commit them to GitHub.")


if __name__ == "__main__":
    main()
