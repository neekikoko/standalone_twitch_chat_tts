import webbrowser
import http.server
import socketserver
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

PORT = 8787
REDIRECT_PATH = "/callback"

token_value = None


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global token_value

        parsed = urllib.parse.urlparse(self.path)

        # -----------------------------------------
        # Step 2: JS sends token here
        # -----------------------------------------
        if parsed.path == "/token":
            qs = urllib.parse.parse_qs(parsed.query)
            token_value = qs.get("access_token", [None])[0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Token received. You can close this window.")
            return

        # -----------------------------------------
        # Step 1: Twitch redirects here
        # We serve JS to extract fragment (#token)
        # -----------------------------------------
        if parsed.path == REDIRECT_PATH:
            html = """
            <html>
            <body>
            Logging in...
            <script>
                const hash = location.hash.substring(1);
                fetch("/token?" + hash);
            </script>
            </body>
            </html>
            """

            self.send_response(200)
            self.end_headers()
            self.wfile.write(html.encode())
            return

        self.send_response(404)
        self.end_headers()


def main():
    if not CLIENT_ID:
        print("TWITCH_CLIENT_ID missing in .env")
        return

    scopes = "chat:read+chat:edit+channel:bot"

    auth_url = (
        "https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri=http://localhost:{PORT}{REDIRECT_PATH}"
        "&response_type=token"
        f"&scope={scopes}"
    )

    print("Opening browser for Twitch login...")
    webbrowser.open(auth_url)

    with socketserver.TCPServer(("localhost", PORT), OAuthHandler) as httpd:
        print("Waiting for OAuth callback...")
        while token_value is None:
            httpd.handle_request()

    print("\nAccess Token:")
    print(token_value)


if __name__ == "__main__":
    main()
