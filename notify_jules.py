import os
import json
import urllib.request
import urllib.error

# Default Configuration
DEFAULT_SESSION_ID = os.environ.get("JULES_SESSION_ID")
DEFAULT_API_KEY = os.environ.get("JULES_API_KEY")
DEFAULT_MESSAGE = "hello"

def notify_jules_agent(session_id=None, api_key=None, message=DEFAULT_MESSAGE):
    session_id = session_id or DEFAULT_SESSION_ID
    api_key = api_key or DEFAULT_API_KEY

    if not session_id or not api_key:
        print("Error: Missing required environment variables or arguments.")
        print("Please provide or set JULES_SESSION_ID and JULES_API_KEY.")
        return False

    url = f"https://jules.googleapis.com/v1alpha/sessions/{session_id}:sendMessage"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key
    }
    data = json.dumps({"prompt": message}).encode("utf-8")

    print(f"Sending message to Jules API session {session_id}...")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Successfully sent message to Jules agent!")
                return True
            else:
                print(f"Failed to send message. Status: {response.status}")
                print(response.read().decode())
                return False
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
        return False
    except urllib.error.URLError as e:
         print(f"URL Error: {e.reason}")
         return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    notify_jules_agent()
