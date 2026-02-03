import os
import json
import asyncio
import requests
import websockets
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID")
REWARD_TITLE = os.getenv("REWARD_TITLE", "").lower()
TEST_WITHOUT_REDEEMS = os.getenv("TEST_WITHOUT_REDEEMS", "false").lower() in ("1", "true")

TTS_URL = "http://127.0.0.1:5005/speak"

# ------------------------------------------------------------
# OAuth token
# ------------------------------------------------------------
def get_app_token():
    r = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]

# ------------------------------------------------------------
# Subscribe to redemption events
# ------------------------------------------------------------
def subscribe(session_id, token):
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"

    body = {
        "type": "channel.channel_points_custom_reward_redemption.add",
        "version": "1",
        "condition": {
            "broadcaster_user_id": BROADCASTER_ID
        },
        "transport": {
            "method": "websocket",
            "session_id": session_id
        }
    }

    headers = {
        "Client-Id": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, headers=headers, json=body)
    r.raise_for_status()
    print("[INFO] Subscribed to channel point redemptions")

# ------------------------------------------------------------
# Send text to your Piper TTS server
# ------------------------------------------------------------
def send_to_tts(text):
    try:
        requests.post(TTS_URL, json={"text": text}, timeout=5)
    except Exception as e:
        print("[ERROR] TTS request failed:", e)

# ------------------------------------------------------------
# WebSocket listener
# ------------------------------------------------------------
async def run_twitch():
    token = get_app_token()

    async with websockets.connect("wss://eventsub.wss.twitch.tv/ws") as ws:
        print("[INFO] Connected to Twitch EventSub")

        # first message contains session id
        hello = json.loads(await ws.recv())
        session_id = hello["payload"]["session"]["id"]

        print("[INFO] Session:", session_id)

        subscribe(session_id, token)

        while True:
            msg = json.loads(await ws.recv())

            if msg["metadata"]["message_type"] != "notification":
                continue

            event = msg["payload"]["event"]

            title = event["reward"]["title"].lower()
            user = event["user_name"]
            text = event.get("user_input", "")

            if REWARD_TITLE and title != REWARD_TITLE:
                continue

            if not text:
                print(f"[INFO] {user} redeemed but no text")
                continue

            print(f"[REDEEM] {user}: {text}")
            send_to_tts(text)

# ------------------------------------------------------------
# Local debug mode
# ------------------------------------------------------------
def test_without_redeems():
    print("[DEBUG MODE] Type messages to send to TTS. Ctrl+C to exit.")
    while True:
        try:
            text = input("> ")
            if not text.strip():
                continue
            print(f"[DEBUG] Sending: {text}")
            send_to_tts(text)
        except KeyboardInterrupt:
            print("\n[DEBUG] Exiting debug mode.")
            break

# ------------------------------------------------------------
if __name__ == "__main__":
    if TEST_WITHOUT_REDEEMS:
        test_without_redeems()
    else:
        asyncio.run(run_twitch())
