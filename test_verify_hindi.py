import asyncio
import os
import sys
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "worker")))
from scripts.browser import SnapshotBrowser

async def run_test():
    browser = SnapshotBrowser()
    try:
        await browser.launch(headless=True)

        cookies_dir = "worker/config/cookies"
        cookies_path = os.path.join(cookies_dir, "instagram.json")
        if os.path.exists(cookies_path):
            await browser.load_cookies(cookies_path)

        await browser.nav("https://www.instagram.com/direct/inbox/")
        await browser.dismiss_dialogs()
        await browser.human_delay(5, 8)

        snap = await browser.snapshot()
        user_ref = -1
        for line in snap.splitlines():
            if "Sherly🪿" in line or ("Sherly" in line and "You" in line):
                import re
                match = re.search(r'\[(\d+)\]', line)
                if match:
                    user_ref = int(match.group(1))
                    break

        if user_ref > 0:
            print(f"Clicking Sherly chat (ref [{user_ref}])...")
            await browser.click(user_ref, force=True)
            await browser.human_delay(8, 12)

            # Scroll up to load history
            js_script = """
            () => {
                const containers = document.querySelectorAll('div[role="presentation"], div[class*="x1n2onr6"]');
                let scrolled = false;
                for (let c of containers) {
                    if (c.scrollHeight > c.clientHeight) {
                        c.scrollTop = 0;
                        scrolled = true;
                    }
                }
                return scrolled;
            }
            """
            for i in range(5):
                await browser.page.evaluate(js_script)
                await browser.page.keyboard.press("PageUp")
                await browser.human_delay(2, 4)

            html = await browser.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            messages = soup.find_all(string=lambda text: "basics" in text.lower() if text else False)
            print(f"Number of messages containing 'basics' found: {len(messages)}")

            await browser.screenshot("worker/logs/screenshots/sherly_chat_scrolled_hindi_verified.png")
            print("Chat verification snapshot saved!")

        else:
            print("Could not find Sherly in inbox list.")
            return

    except Exception as e:
        print(f"❌ Error in script: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
