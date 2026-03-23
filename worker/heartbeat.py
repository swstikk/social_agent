#!/usr/bin/env python3
"""
NEVER-DYING HEARTBEAT — Background Survival Script

Run with: nohup python3 heartbeat.py > /tmp/heartbeat.log 2>&1 &

This script survives after Jules session ends (up to ~2 hours).
It pings Commander every 5 minutes via Jules API.
When Commander receives the ping, it wakes up and sends a new command,
which revives the Worker session.

This is what makes our system truly 24/7.
"""

import time
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

# ──────────────────────── CONFIG ────────────────────────

API_BASE = "https://jules.googleapis.com/v1alpha"
API_KEY = os.environ.get("JULES_API_KEY", "")
COMMANDER_SESSION_ID = os.environ.get("COMMANDER_SESSION_ID", "")
PING_INTERVAL = int(os.environ.get("PING_INTERVAL", "300"))  # default 5 min


# ──────────────────────── FUNCTIONS ────────────────────────

def log(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def send_ping(message: str) -> bool:
    """Send message to Commander via Jules API."""
    if not API_KEY or not COMMANDER_SESSION_ID:
        log("ERROR: JULES_API_KEY or COMMANDER_SESSION_ID not set!")
        return False

    url = f"{API_BASE}/sessions/{COMMANDER_SESSION_ID}:sendMessage"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
    }
    payload = {
        "prompt": f"Worker says: {message}"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                log(f"Ping sent successfully (HTTP {resp.status})")
                return True
            else:
                log(f"Ping got unexpected status: {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        log(f"Ping HTTP error: {e.code} — {e.reason}")
        return False
    except urllib.error.URLError as e:
        log(f"Ping URL error: {e.reason}")
        return False
    except Exception as e:
        log(f"Ping unexpected error: {e}")
        return False


# ──────────────────────── MAIN LOOP ────────────────────────

def main():
    log("=" * 50)
    log("HEARTBEAT STARTED")
    log(f"Commander Session: {COMMANDER_SESSION_ID[:20]}...")
    log(f"Ping Interval: {PING_INTERVAL} seconds")
    log("=" * 50)

    if not API_KEY:
        log("FATAL: JULES_API_KEY not set. Exiting.")
        sys.exit(1)
    if not COMMANDER_SESSION_ID:
        log("FATAL: COMMANDER_SESSION_ID not set. Exiting.")
        sys.exit(1)

    cycle = 0
    consecutive_failures = 0

    while True:
        cycle += 1

        message = (
            f"[HEARTBEAT] cycle: {cycle}. "
            f"Worker sandbox alive. "
            f"Awaiting commands. "
            f"time: {datetime.now().isoformat()}"
        )

        success = send_ping(message)

        if success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            log(f"Consecutive failures: {consecutive_failures}")

            # If 10 consecutive failures, something is very wrong
            if consecutive_failures >= 10:
                log("10 consecutive failures. API likely dead. Sleeping longer.")
                time.sleep(PING_INTERVAL * 3)  # Triple the wait
                consecutive_failures = 0  # Reset and try again

        time.sleep(PING_INTERVAL)


if __name__ == "__main__":
    main()
