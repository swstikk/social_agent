import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from worker.scripts.browser import SnapshotBrowser

async def follow_user(browser: "SnapshotBrowser", username: str):
    """Navigates to the user's profile and clicks Follow if not already following."""
    print(f"--- Action: Follow {username} ---")
    await browser.nav(f"https://www.instagram.com/{username}/")
    await browser.human_delay(2, 4)

    try:
        # Use exact match so we don't accidentally click "Following" and unfollow them
        follow_btn = browser.page.get_by_role("button", name="Follow", exact=True).first
        if await follow_btn.is_visible(timeout=5000):
            print(f"Clicking 'Follow' button for {username}...")
            await follow_btn.click(force=True)
            await browser.human_delay(2, 4)
            print("✅ Successfully Followed.")
        else:
            print(f"✅ Already following or 'Follow' not found for {username}.")
    except Exception as e:
        print(f"❌ Error in follow_user: {e}")

async def open_first_post(browser: "SnapshotBrowser"):
    """Takes a snapshot and clicks the first available post link."""
    print("--- Action: Open First Post ---")
    snap = await browser.snapshot()
    import re

    # Close any message popups that block the UI first
    close_ref = None
    for line in snap.splitlines():
        if "BUTTON 'Close'" in line or "Close messages" in line or "unread chats" in line.lower():
            match = re.search(r'\[(\d+)\]', line)
            if match:
                close_ref = int(match.group(1))
                break

    if close_ref is not None:
        print(f"Closing messages overlay at ref [{close_ref}]")
        await browser.click(close_ref)
        await browser.human_delay(1, 3)
        snap = await browser.snapshot()

    # Find the post link
    ref = None
    for line in snap.splitlines():
        if "LINK 'Carousel'" in line or "LINK 'Post'" in line or "LINK 'Video'" in line:
            match = re.search(r'\[(\d+)\]', line)
            if match:
                ref = int(match.group(1))
                break

    if ref is None:
        # Fallback to after 'Tagged'
        tagged_found = False
        for line in snap.splitlines():
            if "LINK 'Tagged'" in line:
                tagged_found = True
                continue
            if tagged_found and "LINK" in line:
                match = re.search(r'\[(\d+)\]', line)
                if match:
                    ref = int(match.group(1))
                    break

    if ref is not None:
        print(f"Clicking first post at ref [{ref}]...")
        await browser.click(ref)
        await browser.human_delay(3, 5)
        print("✅ Post opened.")
        return True
    else:
        print("❌ Could not find a post to click.")
        return False

async def like_post(browser: "SnapshotBrowser"):
    """Clicks the like button (heart) on an open post."""
    print("--- Action: Like Post ---")
    try:
        like_button = browser.page.locator('svg[aria-label="Like"]').first
        if await like_button.is_visible(timeout=5000):
            print("Found 'Like' button. Clicking...")
            await like_button.click(force=True)
            await browser.human_delay(2, 4)
            print("✅ Post liked.")
        else:
            unlike_button = browser.page.locator('svg[aria-label="Unlike"]').first
            if await unlike_button.is_visible(timeout=5000):
                print("✅ Post is already liked.")
            else:
                print("❌ Could not find Like or Unlike button.")
    except Exception as e:
        print(f"❌ Error in like_post: {e}")

async def comment_post(browser: "SnapshotBrowser", text: str):
    """Writes a comment on an open post and clicks Post."""
    print(f"--- Action: Comment Post ('{text}') ---")
    try:
        comment_box = browser.page.locator('textarea[aria-label="Add a comment…"]').first
        if await comment_box.is_visible(timeout=5000):
            print("Writing comment...")
            await comment_box.fill(text)
            await browser.human_delay(1, 3)

            # Use smart helper to click Post button to ensure reliability
            await browser.smart_click_text("Post", exact=True)
            await browser.human_delay(2, 4)
            print("✅ Comment posted.")
        else:
            print("❌ Could not find comment box.")
    except Exception as e:
        print(f"❌ Error in comment_post: {e}")

async def share_post(browser: "SnapshotBrowser", target_user: str):
    """Opens the share modal, searches for target_user, and shares the post."""
    print(f"--- Action: Share Post to {target_user} ---")
    # Wait for comments to settle
    await browser.human_delay(2, 4)

    try:
        # Use smart helper to click the "Share Post" SVG
        clicked = await browser.js_click_aria("Share Post")
        if clicked:
            await browser.human_delay(4, 6)

            # Use smart helper to wait for the search input and fill it
            filled = await browser.wait_and_fill("Search", target_user)

            if filled:
                await browser.human_delay(3, 5)

                # Check checkboxes for the user
                checkboxes = await browser.page.locator('input[type="checkbox"]').all()
                if checkboxes:
                    await checkboxes[0].click(force=True)
                    print(f"Selected user '{target_user}'.")
                    await browser.human_delay(2, 4)

                    # Use smart click text for the 'Send' button
                    await browser.smart_click_text("Send", exact=True)
                    await browser.human_delay(2, 4)
                    print("✅ Post shared.")
                else:
                    print(f"❌ User '{target_user}' not found in share search results.")
            else:
                 print("❌ Search input not found in share modal.")
        else:
            print("❌ Could not click Share Post button.")
    except Exception as e:
        print(f"❌ Error in share_post: {e}")

async def close_modal(browser: "SnapshotBrowser"):
    """Closes any open modal (like post detail or share) by clicking the close SVG."""
    print("--- Action: Close Modal ---")
    try:
        closed = await browser.js_click_aria("Close")
        if closed:
            await browser.human_delay(2, 4)
            print("✅ Modal closed.")
        else:
            print("❌ Could not find 'Close' button.")
    except Exception as e:
         print(f"❌ Error closing modal: {e}")

async def block_user(browser: "SnapshotBrowser"):
    """Clicks Options on profile and clicks Block, confirming the dialog."""
    print("--- Action: Block User ---")
    try:
        # Click the 3 dots 'Options'
        options_clicked = await browser.js_click_aria("Options")
        if options_clicked:
            await browser.human_delay(2, 4)

            # Click Block in the menu
            block_clicked = await browser.smart_click_text("Block", exact=False)
            if block_clicked:
                await browser.human_delay(2, 4)

                # Click Block in the confirm dialog
                confirm_clicked = await browser.smart_click_text("Block", exact=False)
                if confirm_clicked:
                     await browser.human_delay(3, 5)
                     print("✅ User blocked successfully.")
                else:
                     print("❌ Confirm block failed.")
            else:
                 print("❌ 'Block' option not found in menu.")
        else:
            print("❌ 'Options' button not found.")
    except Exception as e:
        print(f"❌ Error in block_user: {e}")
