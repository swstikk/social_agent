import asyncio
import os
import sys

# Ensure worker package can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "worker")))
from scripts.browser import SnapshotBrowser
from skills.instagram.actions import follow_user, open_first_post, like_post, comment_post, share_post, close_modal, block_user

async def run_step():
    browser = SnapshotBrowser()
    try:
        await browser.launch(headless=True)

        cookies_dir = "worker/config/cookies"
        cookies_path = os.path.join(cookies_dir, "instagram.json")
        if os.path.exists(cookies_path):
            await browser.load_cookies(cookies_path)
        else:
            print(f"Warning: Cookies file {cookies_path} not found. Running without cookies.")

        target_username = "cristiano"

        # 1. Navigate & Follow
        await follow_user(browser, target_username)
        await browser.screenshot("worker/logs/screenshots/step1_follow.png")

        # 2. Open Post & Like
        if await open_first_post(browser):
            await like_post(browser)
            await browser.screenshot("worker/logs/screenshots/step2_like.png")

            # 3. Comment
            await comment_post(browser, "Great post! 🔥")
            await browser.screenshot("worker/logs/screenshots/step3_comment.png")

            # 4. Share
            await share_post(browser, "leomessi")
            await browser.screenshot("worker/logs/screenshots/step4_share.png")

            # 5. Close Post
            await close_modal(browser)

            # 6. Block User
            await block_user(browser)
            await browser.screenshot("worker/logs/screenshots/step5_block.png")

            snap_final = await browser.snapshot()
            with open("worker/logs/screenshots/snapshot_final.txt", "w", encoding="utf-8") as f:
                f.write(snap_final)
            print("✅ Process completed. Final states saved.")

    except Exception as e:
        print(f"❌ Error in script: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_step())
