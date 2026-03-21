#!/usr/bin/env python3
import requests
import json
import os
import sys
import argparse

# --- Security & Config ---
# The Commander AI must set this environment variable before running.
# Example: export JULES_API_KEY="AQ.Ab..."
API_KEY = os.environ.get("JULES_API_KEY")

if not API_KEY:
    print("FATAL ERROR: JULES_API_KEY environment variable is not set.", file=sys.stderr)
    print("As a Commander Agent, you MUST set this before orchestrating the Worker.", file=sys.stderr)
    print("Command: export JULES_API_KEY='<provided_key>'", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://jules.googleapis.com/v1alpha"

headers = {
    "X-Goog-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

# --- Core API Functions ---

def _format_session(session_id):
    """Ensures the session ID is in the correct API format."""
    return session_id if session_id.startswith('sessions/') else f"sessions/{session_id}"

def get_status(session_id):
    """Function 4: Fetch activities to determine the current state of the Worker."""
    session_name = _format_session(session_id)
    url = f"{BASE_URL}/{session_name}/activities?pageSize=10"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f"--- STATUS REPORT FOR WORKER: {session_name} ---")
        if not data or 'activities' not in data:
            print("No activities found. The worker might be idle or the session is empty.")
            return

        # Print the last 3 activities for context
        print("Recent Activity Log (Latest First):")
        activities = data['activities']
        # The API usually returns newest first if paginated, but let's just show top 3
        for idx, act in enumerate(activities[:3]):
            time = act.get('createTime', 'Unknown Time')
            originator = act.get('originator', 'Unknown')
            print(f"\n[{idx+1}] Time: {time} | Originator: {originator}")

            if 'planGenerated' in act:
                print(">>> WARNING: A Plan has been generated and is PENDING APPROVAL. You MUST run the 'approve' command to unblock the worker.")
            elif 'planApproved' in act:
                print(">>> State: Plan is approved. Worker is executing.")
            elif 'progressUpdated' in act:
                title = act['progressUpdated'].get('title', 'No title')
                desc = act['progressUpdated'].get('description', '')
                print(f">>> Progress: {title}")
                if desc:
                    print(f"    Details: {desc}")
            elif 'sessionCompleted' in act:
                print(">>> State: Worker has completed the session.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"API Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def approve_worker_plan(session_id):
    """Function 5: Approves a pending plan so the Worker can continue."""
    session_name = _format_session(session_id)
    url = f"{BASE_URL}/{session_name}:approvePlan"

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        print(f"SUCCESS: Plan approved for worker {session_name}. They will now proceed.")
    except requests.exceptions.RequestException as e:
        print(f"Error approving plan: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"API Response: {e.response.text}", file=sys.stderr)
            if "FAILED_PRECONDITION" in e.response.text or "no plan to approve" in e.response.text.lower():
                print("\nNote: It seems there is no plan currently waiting for approval.")
        sys.exit(1)

def send_worker_message(session_id, message):
    """Function 6: Sends a command/message to the Worker."""
    session_name = _format_session(session_id)
    url = f"{BASE_URL}/{session_name}:sendMessage"
    payload = {"prompt": message}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"SUCCESS: Command sent to worker {session_name}.")
        print(f"Payload: '{message}'")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"API Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

# --- CLI Setup ---

def main():
    parser = argparse.ArgumentParser(
        description="Jules Commander CLI: A tool for an AI to orchestrate and control a Worker AI session."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available Commander actions", required=True)

    # 1. Status Command
    status_parser = subparsers.add_parser("status", help="Check the current activities and state of the Worker.")
    status_parser.add_argument("session_id", help="The ID of the Worker's session.")

    # 2. Approve Command
    approve_parser = subparsers.add_parser("approve", help="Approve a pending plan so the Worker can continue executing.")
    approve_parser.add_argument("session_id", help="The ID of the Worker's session.")

    # 3. Message Command
    msg_parser = subparsers.add_parser("message", help="Send a new command or feedback to the Worker.")
    msg_parser.add_argument("session_id", help="The ID of the Worker's session.")
    msg_parser.add_argument("text", help="The message/prompt to send to the Worker. (Enclose in quotes)")

    args = parser.parse_args()

    if args.command == "status":
        get_status(args.session_id)
    elif args.command == "approve":
        approve_worker_plan(args.session_id)
    elif args.command == "message":
        send_worker_message(args.session_id, args.text)

if __name__ == "__main__":
    main()
