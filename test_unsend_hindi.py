import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "worker")))
from scripts.browser import SnapshotBrowser
from skills.instagram.actions import unsend_message

async def run_test():
    browser = SnapshotBrowser()
    try:
        await browser.launch(headless=True)

        cookies_dir = "worker/config/cookies"
        cookies_path = os.path.join(cookies_dir, "instagram.json")
        if os.path.exists(cookies_path):
            await browser.load_cookies(cookies_path)

        target_text = "sahi hai, basics par pakad zaroori hai"
        # We need to give username. Based on our snapshot matching, "Sherly" is what we search for
        username = "Sherly"

        result = await unsend_message(browser, username, target_text)
        print(f"Final unsend_message result: {result}")

    except Exception as e:
        print(f"❌ Error in script: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
