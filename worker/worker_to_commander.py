import argparse
import json
import os
import sys
import urllib.request
import urllib.error

JULES_API_BASE = "https://jules.googleapis.com/v1alpha"

def send_message_to_commander(session_id: str, api_key: str, message: str):
    """
    Sends a message to the Commander's Jules session using the Jules API.
    AUTOMATICALLY prefixes every message with 'Worker says: ' so the Commander
    always knows who is talking.
    """
    # CRITICAL: Always prefix with "Worker says: "
    prefixed_message = f"Worker says: {message}"
    
    url = f"{JULES_API_BASE}/sessions/{session_id}:sendMessage"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key
    }
    
    payload = {
        "prompt": prefixed_message
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Successfully sent message to Commander via Jules API.")
                print(f"Message sent: {prefixed_message[:100]}...")
                return True
            else:
                print(f"Failed to send message. HTTP Status: {response.status}")
                return False
    except urllib.error.URLError as e:
        print(f"Error communicating with Jules API: {e}")
        return False

def upload_screenshot(image_path: str) -> str:
    """
    Uploads a screenshot to ImgBB (free image hosting) and returns the URL.
    Falls back to returning the local path if upload fails.
    
    Usage: url = upload_screenshot("/path/to/screenshot.png")
    Then include the URL in your [REPORT] message to the Commander.
    """
    imgbb_key = os.environ.get("IMGBB_API_KEY", "")
    
    if not imgbb_key:
        print("WARNING: IMGBB_API_KEY not set. Returning local path instead.")
        return f"[LOCAL FILE: {image_path}]"
    
    import base64
    
    with open(image_path, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")
    
    upload_url = f"https://api.imgbb.com/1/upload?key={imgbb_key}"
    
    payload = urllib.parse.urlencode({"image": b64_image}).encode("utf-8")
    req = urllib.request.Request(upload_url, data=payload, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            url = result["data"]["url"]
            print(f"Screenshot uploaded: {url}")
            return url
    except Exception as e:
        print(f"ImgBB upload failed: {e}. Returning local path.")
        return f"[LOCAL FILE: {image_path}]"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Worker → Commander communication bridge.")
    parser.add_argument("--message", required=True, help="Message to send to Commander.")
    parser.add_argument("--screenshot", required=False, help="Path to screenshot to upload and include in message.")
    
    args = parser.parse_args()
    
    session_id = os.environ.get("COMMANDER_SESSION_ID")
    api_key = os.environ.get("JULES_API_KEY")
    
    if not session_id or not api_key:
        print("ERROR: COMMANDER_SESSION_ID and JULES_API_KEY must be set.", file=sys.stderr)
        sys.exit(1)
    
    message = args.message
    
    # If screenshot provided, upload it and append URL to message
    if args.screenshot:
        url = upload_screenshot(args.screenshot)
        message += f"\nscreenshot_url: {url}"
    
    success = send_message_to_commander(session_id, api_key, message)
    if not success:
        sys.exit(1)
