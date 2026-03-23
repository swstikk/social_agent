import asyncio
import os
import sys

# Ensure worker package can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "worker")))
from scripts.browser import SnapshotBrowser

async def test_instagram_features():
    print("=== Testing Instagram Features - FULL LIVE DEMO ===")
    browser = SnapshotBrowser()

    try:
        await browser.launch(headless=True)

        # 1. Setup Cookies and Login Check
        cookies_dir = "worker/config/cookies"
        os.makedirs(cookies_dir, exist_ok=True)
        cookies_path = os.path.join(cookies_dir, "instagram.json")

        # Check for INSTA_SESSION_ID env var
        session_id = os.environ.get("INSTA_SESSION_ID")
        if session_id:
             import json
             cookie_data = [{
                 "name": "sessionid",
                 "value": session_id,
                 "domain": ".instagram.com",
                 "path": "/",
                 "expires": -1,
                 "httpOnly": True,
                 "secure": True,
                 "sameSite": "Lax"
             }]
             with open(cookies_path, "w") as f:
                 json.dump(cookie_data, f)
             print(f"✅ Generated {cookies_path} from INSTA_SESSION_ID")

        if not os.path.exists(cookies_path):
            print("❌ No cookies found at", cookies_path)
            print("Please set the INSTA_SESSION_ID environment variable or create the file manually.")
            return

        print("\n--- 1. Login via Cookies ---")
        await browser.load_cookies(cookies_path)
        await browser.nav("https://www.instagram.com/")
        await browser.human_delay(3, 5)

        snap = await browser.snapshot()
        if "Search" in snap or "Home" in snap or "Log In" not in snap:
            print("✅ Logged in successfully!")
            await browser.screenshot("worker/logs/screenshots/1_login_success.png")
        else:
            print("❌ Login failed. Need fresh session ID.")
            await browser.screenshot("worker/logs/screenshots/1_login_failed.png")
            return

        # Target a random user account that's normal (not a verified brand like instagram to avoid custom DOMs)
        # We will use "nasa" as an example normal verified page with stories and posts
        target_username = "nasa"
        target_post = "C-r-0XGMF9Q" # Keep random post for liking/commenting
        target_reel = "C_qf8s0sZ3f" # Random reel for sharing

        print("\n--- 2. Search Instagram ID ---")
        await browser.nav("https://www.instagram.com/")
        await browser.human_delay(3, 5)
        snap = await browser.snapshot()
        # Look for "Search" button in nav sidebar by SVG aria-label or just "Search" role
        search_ref = await browser.find_by_text("Search")
        if search_ref != -1:
            try:
                await browser.click(search_ref)
                await browser.human_delay(1, 2)
                snap = await browser.snapshot()
                input_ref = await browser.find_by_text("Search")
                if input_ref != -1:
                    await browser.human_type(input_ref, target_username)
                    await browser.human_delay(3, 5)
                    snap = await browser.snapshot()
                    user_ref = await browser.find_by_text(target_username)
                    if user_ref != -1:
                        await browser.click(user_ref)
                        await browser.human_delay(3, 5)
                        await browser.screenshot("worker/logs/screenshots/2_search_success.png")
                        print(f"✅ Searched and opened {target_username}")
                    else:
                        print("❌ Could not click search result")
                else:
                    print("❌ Search input not found")
            except Exception as e:
                 print(f"❌ Failed to click search: {e}")
        else:
            print("❌ Search icon not found")

        print("\n--- 3. Follow a User ---")
        await browser.nav(f"https://www.instagram.com/{target_username}/")
        await browser.human_delay(3, 6)
        snap = await browser.snapshot()

        # We want the actual "Follow" button, not the following list count
        # Usually it's a div with role="button" containing "Follow"
        follow_ref = -1
        for ref, el in browser._element_map.items():
            el_text = await el.text_content() or ""
            # Check for exact matches to avoid "followers" or "following"
            if el_text.strip() == "Follow":
                follow_ref = ref
                break

        if follow_ref != -1:
            try:
                await browser.click(follow_ref)
                await browser.human_delay(2, 4)
                print(f"✅ Followed {target_username}")
                await browser.screenshot("worker/logs/screenshots/3_followed.png")
            except Exception as e:
                 print(f"❌ Failed to click follow: {e}")
        else:
            print("ℹ️ Follow button not found (might already be following or requested).")

        print("\n--- 4. Like a Post ---")
        await browser.nav(f"https://www.instagram.com/p/{target_post}/")
        await browser.human_delay(3, 6)
        snap = await browser.snapshot()
        like_ref = await browser.find_by_text("Like")
        if like_ref != -1:
            try:
                await browser.click(like_ref)
                await browser.human_delay(2, 4)
                print("✅ Liked post")
                await browser.screenshot("worker/logs/screenshots/4_liked.png")
            except Exception as e:
                 print(f"❌ Failed to click like: {e}")
        else:
             print("ℹ️ Like button not found (might already be liked).")

        print("\n--- 5. Comment on a Post ---")
        comment_box_ref = await browser.find_by_text("Add a comment")
        if comment_box_ref != -1:
            try:
                 await browser.human_type(comment_box_ref, "Cool! 🔥")
                 await browser.human_delay(1, 3)
                 snap = await browser.snapshot()
                 post_ref = await browser.find_by_text("Post")
                 if post_ref != -1:
                     await browser.click(post_ref)
                     await browser.human_delay(2, 4)
                     print("✅ Commented on post")
                     await browser.screenshot("worker/logs/screenshots/5_commented.png")
                 else:
                     print("❌ Post button not found after typing comment")
            except Exception as e:
                 print(f"❌ Failed to click/type comment: {e}")
        else:
             print("❌ Comment box not found")

        print("\n--- 6. See a Story ---")
        await browser.nav(f"https://www.instagram.com/{target_username}/")
        await browser.human_delay(3, 6)
        snap = await browser.snapshot()
        story_ref = await browser.find_by_text(f"{target_username}'s profile picture")
        if story_ref != -1:
            try:
                await browser.click(story_ref)
                await browser.human_delay(5, 8)
                print("✅ Viewed story")
                await browser.screenshot("worker/logs/screenshots/6_story_viewed.png")
            except Exception as e:
                 print(f"❌ Failed to view story: {e}")
        else:
             print("ℹ️ No story found for this user right now.")

        print("\n--- 7. Chat/DM (Open Inbox & Send) ---")
        await browser.nav(f"https://www.instagram.com/direct/new/")
        await browser.human_delay(3, 6)
        snap = await browser.snapshot()

        try:
             search_ref = await browser.find_by_text("Search")
             if search_ref != -1:
                  # Fix Element not attached to DOM error by clicking first to ensure focus/attachment
                  await browser.click(search_ref)
                  await browser.human_delay(1, 2)
                  await browser.human_type(search_ref, target_username)
                  await browser.human_delay(3, 5)
                  snap = await browser.snapshot()
                  user_ref = await browser.find_by_text(target_username)
                  if user_ref != -1:
                      await browser.click(user_ref)
                      await browser.human_delay(1, 2)
                      snap = await browser.snapshot()
                      chat_btn = await browser.find_by_text("Chat")
                      if chat_btn != -1:
                          await browser.click(chat_btn)
                          await browser.human_delay(3, 5)
                          snap = await browser.snapshot()
                          msg_box = await browser.find_by_text("Message")
                          if msg_box != -1:
                              await browser.human_type(msg_box, "Hello from automated test! 👋")
                              await browser.human_delay(1, 2)
                              snap = await browser.snapshot()
                              send_btn = await browser.find_by_text("Send")
                              if send_btn != -1:
                                  await browser.click(send_btn)
                                  await browser.human_delay(2, 4)
                                  print(f"✅ Sent DM to {target_username}")
                                  await browser.screenshot("worker/logs/screenshots/7_dm_sent.png")
                              else:
                                  print("❌ Send button not found")
                          else:
                              print("❌ Message input box not found")
                      else:
                          print("❌ Chat button not found")
                  else:
                      print("❌ Target user not found in search")
             else:
                  print("❌ DM Search box not found")
        except Exception as e:
             print(f"❌ Failed to send DM: {e}")

        print("\n--- 8. Share a Reel ---")
        await browser.nav(f"https://www.instagram.com/reel/{target_reel}/")
        await browser.human_delay(3, 6)
        snap = await browser.snapshot()
        share_ref = await browser.find_by_text("Share Post")
        if share_ref == -1:
            share_ref = await browser.find_by_text("Share")

        if share_ref != -1:
            try:
                await browser.click(share_ref)
                await browser.human_delay(2, 4)
                snap = await browser.snapshot()
                search_ref = await browser.find_by_text("Search")
                if search_ref != -1:
                    await browser.human_type(search_ref, target_username)
                    await browser.human_delay(3, 5)
                    snap = await browser.snapshot()
                    user_ref = await browser.find_by_text(target_username)
                    if user_ref != -1:
                        await browser.click(user_ref)
                        await browser.human_delay(1, 2)
                        snap = await browser.snapshot()
                        send_ref = await browser.find_by_text("Send")
                        if send_ref != -1:
                            await browser.click(send_ref)
                            await browser.human_delay(2, 4)
                            print("✅ Shared Reel")
                            await browser.screenshot("worker/logs/screenshots/8_reel_shared.png")
                        else:
                            print("❌ Send button not found")
                    else:
                        print("❌ Target user not found in share list")
                else:
                     print("❌ Share search box not found")
            except Exception as e:
                 print(f"❌ Failed to share reel: {e}")
        else:
             print("❌ Share button not found")

        print("\n--- 9. Block User ---")
        await browser.nav(f"https://www.instagram.com/{target_username}/")
        await browser.human_delay(3, 6)
        snap = await browser.snapshot()
        options_ref = await browser.find_by_text("Options")
        if options_ref == -1:
            options_ref = await browser.find_by_text("More options")

        if options_ref != -1:
            try:
                 await browser.click(options_ref)
                 await browser.human_delay(2, 4)

                 # The "Block" option appears in a dropdown/modal
                 snap = await browser.snapshot()
                 block_ref = await browser.find_by_text("Block")
                 if block_ref != -1:
                     await browser.click(block_ref)
                     await browser.human_delay(2, 4)

                     # Instagram throws an overlay modal here. Playwright normal click gets intercepted.
                     # We must use force=True and target the specific dialog button.
                     # To do this safely using our SnapshotBrowser wrapper we execute standard page locator
                     print("Attempting to bypass modal interception with force=True...")
                     await browser.page.locator('div[role="dialog"] button').filter(has_text="Block").first.click(force=True)
                     await browser.human_delay(3, 5)

                     print("✅ Blocked User Confirmed")
                     await browser.screenshot("worker/logs/screenshots/9_blocked.png")

                 else:
                      print("❌ Block option not found in options menu")
            except Exception as e:
                 print(f"❌ Failed to block: {e}")
        else:
             print("❌ Options button not found on profile")

    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        await browser.close()
        print("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_instagram_features())
