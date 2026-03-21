import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# The API URL for Jules. The Commander will replace SESSION_ID with their actual session ID.
JULES_API_BASE = "https://jules.googleapis.com/v1alpha"

def send_message_to_commander(session_id: str, api_key: str, message: str):
    """
    Sends a message to the Commander's Jules session using the Jules API.
    """
    url = f"{JULES_API_BASE}/sessions/{session_id}:sendMessage"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key
    }

    payload = {
        "prompt": message
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Successfully sent message to Commander via Jules API.")
                return True
            else:
                print(f"Failed to send message. HTTP Status: {response.status}")
                return False
    except urllib.error.URLError as e:
        print(f"Error communicating with Jules API: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a message to the Commander Jules agent.")
    parser.add_argument("--message", required=True, help="The detailed message/status to send to the Commander.")

    args = parser.parse_args()

    # In a real environment, these would be set securely as environment variables
    session_id = os.environ.get("COMMANDER_SESSION_ID")
    api_key = os.environ.get("JULES_API_KEY")

    if not session_id or not api_key:
        print("ERROR: COMMANDER_SESSION_ID and JULES_API_KEY environment variables must be set.", file=sys.stderr)
        print("Commander: Please ensure you set these variables in the worker's sandbox before initializing.", file=sys.stderr)
        sys.exit(1)

    success = send_message_to_commander(session_id, api_key, args.message)
    if not success:
        sys.exit(1)
