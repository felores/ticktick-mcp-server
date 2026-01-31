"""
TickTick OAuth authentication module.

This module handles the OAuth 2.0 flow for authenticating with TickTick,
allowing users to authorize the application and obtain access tokens.
"""

import os
import webbrowser
import json
import time
import base64
import http.server
import socketserver
import urllib.parse
import requests
import logging
from typing import Optional

from .credentials import save_credentials, get_credentials_path

logger = logging.getLogger(__name__)

DEFAULT_SCOPES = ["tasks:read", "tasks:write"]


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle OAuth callback requests."""

    auth_code = None
    expected_state = None

    def do_GET(self):
        """Handle GET requests to the callback URL."""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        # Validate state parameter for CSRF protection
        if OAuthCallbackHandler.expected_state:
            received_state = params.get('state', [None])[0]
            if received_state != OAuthCallbackHandler.expected_state:
                logger.warning("CSRF attack detected: state parameter mismatch")
                self.send_response(403)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Security Error</h1><p>Invalid state parameter.</p>")
                return

        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = """
            <html>
            <head>
                <title>TickTick MCP - Success</title>
                <style>
                    body { font-family: system-ui; max-width: 500px; margin: 50px auto; text-align: center; }
                    h1 { color: #4CAF50; }
                    .box { border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>Authentication Successful!</h1>
                <div class="box">
                    <p>You can close this window and return to your terminal.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed</h1><p>No authorization code received.</p>")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class TickTickAuth:
    """TickTick OAuth authentication manager."""

    def __init__(self, client_id: str = None, client_secret: str = None,
                 redirect_uri: str = "http://localhost:8080/callback",
                 port: int = 8080):
        """
        Initialize the authentication manager.

        Args:
            client_id: TickTick client ID (from environment if not provided)
            client_secret: TickTick client secret (from environment if not provided)
            redirect_uri: OAuth redirect URI
            port: Port for callback server
        """
        self.client_id = client_id or os.getenv("TICKTICK_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("TICKTICK_CLIENT_SECRET")
        self.redirect_uri = redirect_uri
        self.port = port

        self.auth_url = os.getenv("TICKTICK_AUTH_URL", "https://ticktick.com/oauth/authorize")
        self.token_url = os.getenv("TICKTICK_TOKEN_URL", "https://ticktick.com/oauth/token")

        self.auth_code = None
        self.tokens = None

    def get_authorization_url(self, scopes: list = None, state: str = None) -> str:
        """Generate the TickTick authorization URL."""
        if not scopes:
            scopes = DEFAULT_SCOPES

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes)
        }

        if state:
            params["state"] = state

        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"

    def start_auth_flow(self, scopes: list = None) -> str:
        """
        Start the OAuth flow by opening the browser and waiting for callback.

        Returns:
            Success or error message
        """
        if not self.client_id or not self.client_secret:
            return "Error: TICKTICK_CLIENT_ID and TICKTICK_CLIENT_SECRET must be set."

        # Clear previous state
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.expected_state = None

        # Generate CSRF protection state
        state = base64.urlsafe_b64encode(os.urandom(30)).decode('utf-8')
        OAuthCallbackHandler.expected_state = state

        auth_url = self.get_authorization_url(scopes, state)

        print("\nOpening browser for TickTick authorization...")
        print(f"If browser doesn't open, visit: {auth_url}\n")

        webbrowser.open(auth_url)

        httpd = None
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", self.port), OAuthCallbackHandler)

            print(f"Waiting for callback on port {self.port}...")

            timeout = 300
            start_time = time.time()
            max_requests = 100
            request_count = 0

            while not OAuthCallbackHandler.auth_code:
                httpd.timeout = 1.0
                httpd.handle_request()
                request_count += 1

                if request_count > max_requests:
                    return "Error: Too many requests. Authentication aborted."

                if time.time() - start_time > timeout:
                    return "Error: Authentication timed out."

            self.auth_code = OAuthCallbackHandler.auth_code
            return self.exchange_code_for_token()

        except Exception as e:
            logger.error(f"OAuth flow error: {e}")
            return f"Error: {str(e)}"
        finally:
            if httpd:
                httpd.server_close()

    def exchange_code_for_token(self) -> str:
        """Exchange authorization code for access token."""
        if not self.auth_code:
            return "Error: No authorization code available."

        token_data = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(DEFAULT_SCOPES)
        }

        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ticktick-mcp-server"
        }

        try:
            response = requests.post(self.token_url, data=token_data, headers=headers, verify=True)
            response.raise_for_status()

            self.tokens = response.json()

            # Save to persistent storage
            save_credentials({
                'access_token': self.tokens.get('access_token'),
                'refresh_token': self.tokens.get('refresh_token')
            })

            creds_path = get_credentials_path()
            return f"Authentication successful!\nCredentials saved to: {creds_path}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error_description',
                                               error_data.get('error', 'Unknown error'))
                    return f"Authentication failed: {error_msg}"
                except (ValueError, json.JSONDecodeError):
                    pass
            return "Authentication failed. Check your credentials and try again."


def run_auth_flow():
    """Run the authentication flow interactively."""
    print("\n" + "=" * 50)
    print("  TickTick MCP Server - Authentication")
    print("=" * 50)

    client_id = os.getenv("TICKTICK_CLIENT_ID")
    client_secret = os.getenv("TICKTICK_CLIENT_SECRET")

    if not client_id:
        print("\nEnter your TickTick Client ID")
        print("(Get it from https://developer.ticktick.com/manage)")
        client_id = input("> ").strip()

    if not client_secret:
        print("\nEnter your TickTick Client Secret:")
        client_secret = input("> ").strip()

    if not client_id or not client_secret:
        print("\nError: Client ID and Client Secret are required.")
        return 1

    auth = TickTickAuth(client_id=client_id, client_secret=client_secret)
    result = auth.start_auth_flow()
    print(f"\n{result}\n")

    return 0 if "successful" in result.lower() else 1
