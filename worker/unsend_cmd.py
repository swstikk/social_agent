#!/usr/bin/env python3
import asyncio
import os
import sys
import argparse
from scripts.browser import SnapshotBrowser
from skills.instagram.actions import unsend_message

async def main():
    parser = argparse.ArgumentParser(description="Instantly unsend an Instagram message from a specific chat.")
    parser.add_argument("username", help="The username or exact display name of the person (e.g. Sherly)")
    parser.add_argument("message_text", help="The exact text of the message to unsend")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in background")
    parser.add_argument("--show", action="store_false", dest="headless", help="Show browser window")
    args = parser.parse_args()

    browser = SnapshotBrowser()
    try:
        # Launching with minimal options for speed
        await browser.launch(headless=args.headless)

        # Quick auth using session cookies
        cookies_dir = os.path.join(os.path.dirname(__file__), "config", "cookies")
        cookies_path = os.path.join(cookies_dir, "instagram.json")
        if os.path.exists(cookies_path):
            await browser.load_cookies(cookies_path)
        else:
            print("❌ No Instagram cookies found. Please run a login script first.")
            return

        print(f"🚀 Targeting message: '{args.message_text}' to '{args.username}'")

        # Execute the optimized fast unsend function
        result = await unsend_message(browser, args.username, args.message_text)

        if result:
            print("\n✅ SUCCESS: Message was unsent successfully!")
        else:
            print("\n❌ FAILED: Could not unsend the message. Check logs above.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
