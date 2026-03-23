import asyncio
import os
import sys
import re

# Ensure worker package can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "worker")))
from scripts.browser import SnapshotBrowser

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
        print(f"--- Navigating to {target_username} ---")
        await browser.nav(f"https://www.instagram.com/{target_username}/")
        await browser.human_delay(3, 5)

        # Follow the user
        try:
            follow_btn = browser.page.locator('button', has_text="Follow").first
            if await follow_btn.is_visible(timeout=5000):
                print(f"Found 'Follow' button. Clicking to follow {target_username}...")
                await follow_btn.click(force=True)
                await browser.human_delay(2, 4)
                print("✅ Followed user.")
            else:
                print("✅ Already following or 'Follow' button not found.")
        except Exception as ex:
            print(f"❌ Error following user: {ex}")

        # Screenshot after follow
        await browser.screenshot("worker/logs/screenshots/step1_follow.png")

        snap2 = await browser.snapshot()

        # If there is a Close button for messages, close it
        close_ref = None
        for line in snap2.splitlines():
            if "BUTTON 'Close'" in line or "Close messages" in line or "7 unread chats" in line:
                match = re.search(r'\[(\d+)\]', line)
                if match:
                    close_ref = int(match.group(1))
                    break

        if close_ref is not None:
            print(f"Closing messages overlay at [{close_ref}]")
            await browser.click(close_ref)
            await browser.human_delay(2, 3)
            snap2 = await browser.snapshot()

        # We want to click the first post
        # The first 'Carousel' or 'Image' or post link
        ref = None
        for line in snap2.splitlines():
            # Look for LINK 'Carousel' or anything that looks like a post
            if "LINK 'Carousel'" in line or "LINK 'Post'" in line or "LINK 'Video'" in line:
                match = re.search(r'\[(\d+)\]', line)
                if match:
                    ref = int(match.group(1))
                    break

        if ref is None:
            # Let's just find the first link after 'Tagged'
            tagged_found = False
            for line in snap2.splitlines():
                if "LINK 'Tagged'" in line:
                    tagged_found = True
                    continue
                if tagged_found and "LINK" in line:
                    match = re.search(r'\[(\d+)\]', line)
                    if match:
                        ref = int(match.group(1))
                        break

        if ref is not None:
            print(f"Found post at ref [{ref}]. Clicking...")
            await browser.click(ref)
            await browser.human_delay(3, 6)

            try:
                like_button = browser.page.locator('svg[aria-label="Like"]').first
                if await like_button.is_visible(timeout=5000):
                    print("Found 'Like' button. Clicking to like the post...")
                    await like_button.click()
                    await browser.human_delay(2, 4)
                    print("✅ Post liked successfully.")
                else:
                    unlike_button = browser.page.locator('svg[aria-label="Unlike"]').first
                    if await unlike_button.is_visible(timeout=5000):
                        print("✅ Post is already liked.")
                    else:
                        print("❌ Could not find Like or Unlike button.")
            except Exception as ex:
                print(f"❌ Error interacting with Like button: {ex}")

            # Screenshot after like
            await browser.screenshot("worker/logs/screenshots/step2_like.png")

            # Now let's try to comment
            try:
                comment_box = browser.page.locator('textarea[aria-label="Add a comment…"]').first
                if await comment_box.is_visible(timeout=5000):
                    print("Found comment box. Writing a comment...")
                    await comment_box.fill('Great post! 🔥')
                    await browser.human_delay(1, 3)

                    # Find and click the 'Post' button
                    post_btn = browser.page.locator('div[role="button"]:has-text("Post")').first
                    if await post_btn.is_visible(timeout=5000):
                        print("Found 'Post' button. Clicking to publish comment...")
                        await post_btn.click()
                        await browser.human_delay(2, 4)
                        print("✅ Comment posted successfully.")
                    else:
                        print("❌ Could not find 'Post' button after typing comment.")
                else:
                    print("❌ Could not find comment box.")
            except Exception as ex:
                print(f"❌ Error interacting with comment box: {ex}")

            # Screenshot after comment
            await browser.screenshot("worker/logs/screenshots/step3_comment.png")

            # Now let's try to share
            try:
                # Let comment finish loading out completely and avoid any floating element interception
                await browser.human_delay(2, 4)

                # Use javascript to safely click the share button inside the complex post modal
                print("Found 'Share Post' button. Clicking to open share menu via JS...")
                clicked = await browser.page.evaluate('''() => {
                    let svgs = document.querySelectorAll('svg[aria-label="Share Post"]');
                    if (svgs.length > 0) {
                        for (let svg of svgs) {
                            let btn = svg.closest('button') || svg.closest('div[role="button"]');
                            if (btn) {
                                btn.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }''')

                if clicked:
                    await browser.human_delay(4, 6)
                    # Explicitly wait for inputs to attach to DOM
                    try:
                        await browser.page.locator('input[placeholder="Search"]').first.wait_for(state='attached', timeout=5000)
                    except Exception:
                        pass
                    try:
                        await browser.page.locator('input[placeholder="Search..."]').first.wait_for(state='attached', timeout=5000)
                    except Exception:
                        pass

                    # The search input might not be immediately visible, so iterate to find it
                    inputs = await browser.page.locator('input').all()
                    search_filled = False
                    for inp in inputs:
                        ph = await inp.get_attribute('placeholder')
                        if ph in ['Search', 'Search...']:
                            print(f"Found share search input with placeholder '{ph}'. Searching for 'leomessi'...")
                            await inp.fill('leomessi')
                            await browser.human_delay(3, 5)
                            search_filled = True
                            break

                    if search_filled:
                        # Find checkboxes to select users
                        checkboxes = await browser.page.locator('input[type="checkbox"]').all()
                        if len(checkboxes) > 0:
                            # Select the first user (which should be the searched one)
                            await checkboxes[0].click(force=True)
                            print("✅ Selected user to share with.")
                            await browser.human_delay(2, 4)

                            # Find and click 'Send' button
                            send_btn = browser.page.locator('div[role="button"]:has-text("Send")').first
                            if await send_btn.is_visible(timeout=5000):
                                print("Found 'Send' button. Clicking to share post...")
                                await send_btn.click()
                                await browser.human_delay(2, 4)
                                print("✅ Post shared successfully.")
                            else:
                                print("❌ Could not find 'Send' button after selecting user.")
                        else:
                            print("❌ No users found in search results.")
                    else:
                        print("❌ Could not find 'Search...' input in share menu.")
                else:
                    print("❌ Could not click 'Share Post' button via JS.")
            except Exception as ex:
                print(f"❌ Error interacting with share menu: {ex}")

            # Screenshot after share
            await browser.screenshot("worker/logs/screenshots/step4_share.png")

            # Now let's close the post modal
            try:
                close_btn = browser.page.locator('svg[aria-label="Close"]').first
                if await close_btn.is_visible(timeout=5000):
                    print("Found 'Close' button. Closing post modal...")
                    await close_btn.click(force=True)
                    await browser.human_delay(2, 4)
                else:
                    print("❌ Could not find 'Close' button for post modal.")
            except Exception as ex:
                print(f"❌ Error closing post modal: {ex}")

            # Now let's block the user
            try:
                options_btns = await browser.page.locator('svg[aria-label="Options"]').all()
                found_options = False
                for opt_btn in options_btns:
                    if await opt_btn.is_visible():
                        print("Found 'Options' button on profile. Clicking...")
                        await opt_btn.click(force=True)
                        await browser.human_delay(2, 4)
                        found_options = True
                        break

                if found_options:
                    # Look for Block option and click it via JS for robustness
                    block_clicked = await browser.page.evaluate('''() => {
                        let btns = document.querySelectorAll('button');
                        for(let b of btns) {
                            if(b.innerText.includes('Block') && !b.innerText.includes('Unblock')) {
                                b.click();
                                return true;
                            }
                        }
                        return false;
                    }''')

                    if block_clicked:
                        print("Found 'Block' option. Clicking...")
                        await browser.human_delay(2, 4)

                        # Confirm block dialog via JS
                        confirm_clicked = await browser.page.evaluate('''() => {
                            let btns = document.querySelectorAll('button');
                            // Reverse loop to get the modal confirm button (which is typically the last one added)
                            for(let i=btns.length-1; i>=0; i--) {
                                if(btns[i].innerText.includes('Block') && !btns[i].innerText.includes('Unblock')) {
                                    btns[i].click();
                                    return true;
                                }
                            }
                            return false;
                        }''')

                        if confirm_clicked:
                            print("Found Confirm 'Block' button. Clicking to block user...")
                            await browser.human_delay(3, 5)
                            print("✅ User blocked successfully.")
                        else:
                            print("❌ Could not find Confirm 'Block' button.")
                    else:
                        print("❌ Could not find 'Block' option in menu.")
                else:
                    print("❌ Could not find 'Options' button on profile.")
            except Exception as ex:
                print(f"❌ Error blocking user: {ex}")

            # Final screenshot after block
            await browser.screenshot("worker/logs/screenshots/step5_block.png")

            snap3 = await browser.snapshot()
            with open("worker/logs/screenshots/snapshot_3.txt", "w", encoding="utf-8") as f:
                f.write(snap3)
            print("✅ Process completed. Final states saved.")
        else:
            print("❌ Post not found.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_step())
