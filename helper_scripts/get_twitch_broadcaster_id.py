import os
import requests
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "../.env")

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
ACCESS_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
USERNAME = os.getenv("TWITCH_CHANNEL_NAME")


def get_broadcaster_id():
    url = "https://api.twitch.tv/helix/users"

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    params = {
        "login": USERNAME,
    }

    res = requests.get(url, headers=headers, params=params, timeout=10)

    if not res.ok:
        print("Failed:", res.status_code, res.text)
        return None

    data = res.json()

    if data.get("data"):
        broadcaster_id = data["data"][0]["id"]
        print("Broadcaster ID:", broadcaster_id)
        return broadcaster_id
    else:
        print("User not found")
        return None


if __name__ == "__main__":
    get_broadcaster_id()
