"""
SystemTools — Linux-native utilities for Worker

Bash commands, file downloads, API calls (Telegram/Discord webhooks),
and ImgBB screenshot uploads.
"""

import subprocess
import json
import os
import urllib.request
import urllib.error


class SystemTools:
    """Worker's Linux-native tools (Peekaboo equivalent for Linux)."""

    @staticmethod
    def run_command(cmd: str, timeout=30) -> str:
        """Run any bash command, return stdout + stderr."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT] Command timed out after {timeout}s: {cmd}"
        except Exception as e:
            return f"[ERROR] {e}"

    @staticmethod
    def upload_screenshot(filepath: str, api_key: str = None) -> str:
        """Upload screenshot to ImgBB and return URL."""
        api_key = api_key or os.environ.get("IMGBB_API_KEY", "")
        if not api_key:
            return "[ERROR] IMGBB_API_KEY not set"
        if not os.path.exists(filepath):
            return f"[ERROR] File not found: {filepath}"

        import base64
        with open(filepath, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        url = f"https://api.imgbb.com/1/upload?key={api_key}"
        data = urllib.parse.urlencode({"image": image_data}).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("data", {}).get("url", "[ERROR] No URL in response")
        except Exception as e:
            return f"[ERROR] Upload failed: {e}"

    @staticmethod
    def download_file(url: str, path: str) -> bool:
        """Download any file from the internet."""
        try:
            urllib.request.urlretrieve(url, path)
            return True
        except Exception as e:
            print(f"[Download] Failed: {e}")
            return False

    @staticmethod
    def send_telegram(token: str, chat_id: str, message: str) -> bool:
        """Send Telegram message directly via Bot API (no library needed)."""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[Telegram] Error: {e}")
            return False

    @staticmethod
    def send_discord_webhook(webhook_url: str, message: str) -> bool:
        """Send Discord message via webhook (no library needed)."""
        data = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status in (200, 204)
        except Exception as e:
            print(f"[Discord] Error: {e}")
            return False
