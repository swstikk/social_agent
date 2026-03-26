import asyncio
import os
import sys

# Ensure worker package can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "worker")))
from scripts.browser import SnapshotBrowser
from skills.instagram.actions import follow_user

async def run_step():
    browser = SnapshotBrowser()
    try:
        await browser.launch(headless=True)

        # Load environment variables (simulate `.env`)
        from dotenv import load_dotenv
        load_dotenv()

        session_id = os.environ.get("INSTA_SESSION_ID")
        if session_id:
            print(f"--- Loading INSTA_SESSION_ID from environment ---")
            cookies_dir = "worker/config/cookies"
            os.makedirs(cookies_dir, exist_ok=True)
            cookies_path = os.path.join(cookies_dir, "instagram.json")

            # Simple cookie format for playwright
            cookies = [
                {
                    "name": "sessionid",
                    "value": session_id,
                    "domain": ".instagram.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "Lax"
                }
            ]
            import json
            with open(cookies_path, "w") as f:
                json.dump(cookies, f, indent=2)

            await browser.load_cookies(cookies_path)

        else:
            print("Warning: INSTA_SESSION_ID environment variable not found. Running without cookies.")

        # We just test the follow function here
        target_username = "cristiano"
        await follow_user(browser, target_username)

        snap2 = await browser.snapshot()
        with open("worker/logs/snapshots/snapshot_2.txt", "w", encoding="utf-8") as f:
            f.write(snap2)
        await browser.screenshot("worker/logs/screenshots/screenshot_2.png")
        print("✅ Saved snapshot_2 and screenshot_2.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_step())
