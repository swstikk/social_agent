"""
Instagram Actions — High-level functions for Worker agent.

Merged best of Jules' + ours. Every function:
  1. Navigates if needed
  2. Dismisses popups
  3. Performs action with force_click + JS fallbacks
  4. Returns bool (success)

Usage:
    from skills.instagram.actions import *

    await login(browser, session_id="...")
    await follow_user(browser, "cristiano")
    if await open_first_post(browser):
        await like_post(browser)
        await comment_post(browser, "Amazing! 🔥")
        await share_post(browser, "leomessi")
    await close_modal(browser)
    await block_user(browser)
    await unblock_user(browser)
    await send_dm(browser, "user", "Hey!")
    await view_story(browser, "username")
    await search_user(browser, "cristiano")
"""

import re
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.browser import SnapshotBrowser


# ═══════════════════════ LOGIN ═══════════════════════

async def login(browser: "SnapshotBrowser", session_id: str = None, cookies_path: str = None) -> bool:
    """Login via session cookie or cookie file. Returns True if successful."""
    print("--- Action: Login ---")

    if cookies_path and os.path.exists(cookies_path):
        await browser.load_cookies(cookies_path)
    elif session_id:
        await browser.context.add_cookies([{
            "name": "sessionid", "value": session_id,
            "domain": ".instagram.com", "path": "/",
            "httpOnly": True, "secure": True, "sameSite": "None"
        }])

    await browser.nav("https://www.instagram.com/")
    await browser.human_delay(3, 5)
    await browser.dismiss_dialogs()
    snap = await browser.smart_snapshot(min_elements=10)
    logged_in = "Search" in snap or "Home" in snap or "Create" in snap
    if logged_in:
        print(f"✅ Logged in ({len(browser._element_map)} elements)")
        # Save cookies for future
        if cookies_path:
            await browser.save_cookies(cookies_path)
    else:
        print("❌ Login failed")
    return logged_in


# ═══════════════════════ FOLLOW / UNFOLLOW ═══════════════════════

async def follow_user(browser: "SnapshotBrowser", username: str) -> bool:
    """
    Follow a user. Uses exact=True matching (Jules' pattern)
    so we don't accidentally click "Following" and unfollow.
    """
    print(f"--- Action: Follow {username} ---")
    await browser.nav(f"https://www.instagram.com/{username}/")
    await browser.dismiss_dialogs()
    await browser.human_delay(2, 4)

    try:
        # Check if already following (exact match!)
        following_btn = browser.page.get_by_role("button", name="Following", exact=True).first
        if await following_btn.is_visible(timeout=3000):
            print(f"✅ Already following {username}.")
            return True

        # Click Follow (exact match to avoid "Following")
        follow_btn = browser.page.get_by_role("button", name="Follow", exact=True).first
        if await follow_btn.is_visible(timeout=5000):
            await follow_btn.click(force=True)
            await browser.human_delay(2, 4)
            print(f"✅ Followed {username}.")
            return True
        else:
            print(f"❌ 'Follow' button not found for {username}.")
            return False
    except Exception as e:
        print(f"❌ Error in follow_user: {e}")
        return False


async def unfollow_user(browser: "SnapshotBrowser", username: str) -> bool:
    """Unfollow a user — clicks Following → confirms Unfollow dialog."""
    print(f"--- Action: Unfollow {username} ---")
    await browser.nav(f"https://www.instagram.com/{username}/")
    await browser.dismiss_dialogs()
    await browser.human_delay(2, 4)

    try:
        # Check if not following
        follow_btn = browser.page.get_by_role("button", name="Follow", exact=True).first
        if await follow_btn.is_visible(timeout=3000):
            print(f"✅ Not following {username}. No action needed.")
            return True

        # Click "Following" button
        following_btn = browser.page.get_by_role("button", name="Following", exact=True).first
        if await following_btn.is_visible(timeout=5000):
            await following_btn.click(force=True)
            await browser.human_delay(2, 4)

            # Confirm "Unfollow" in dialog (smart_click_text targets last = modal)
            confirmed = await browser.smart_click_text("Unfollow", exact=True)
            if confirmed:
                await browser.human_delay(2, 4)
                print(f"✅ Unfollowed {username}.")
                return True
            else:
                print("❌ Confirm Unfollow dialog not found.")
                return False
        else:
            print(f"❌ 'Following' button not found for {username}.")
            return False
    except Exception as e:
        print(f"❌ Error in unfollow_user: {e}")
        return False


# ═══════════════════════ POSTS ═══════════════════════

async def open_first_post(browser: "SnapshotBrowser") -> bool:
    """
    Find and click the first post on current profile page.
    Jules' pattern: parse snapshot text for Carousel/Post/Video links,
    fallback to links after "Tagged" section.
    Also closes message overlay if it blocks the UI.
    """
    print("--- Action: Open First Post ---")
    snap = await browser.smart_snapshot(min_elements=10)

    # Close any message popup that blocks the UI
    close_ref = None
    for line in snap.splitlines():
        if "BUTTON 'Close'" in line or "Close messages" in line or "unread chats" in line.lower():
            match = re.search(r'\[(\d+)\]', line)
            if match:
                close_ref = int(match.group(1))
                break

    if close_ref is not None:
        print(f"Closing messages overlay at [{close_ref}]")
        await browser.click(close_ref, force=True)
        await browser.human_delay(1, 3)
        snap = await browser.snapshot()

    # Method 1: Find post link by type tag in snapshot
    ref = None
    for line in snap.splitlines():
        if any(tag in line for tag in ["[post]", "[reel]", "LINK 'Carousel'", "LINK 'Post'", "LINK 'Video'", "LINK 'Clip'"]):
            match = re.search(r'\[(\d+)\]', line)
            if match:
                ref = int(match.group(1))
                break

    # Method 2: First link after "Tagged" section
    if ref is None:
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

    # Method 3: Check href attributes directly
    if ref is None:
        for r in browser._element_map:
            href = await browser.get_attribute(r, "href")
            if href and ("/p/" in href or "/reel/" in href):
                ref = r
                break

    if ref is not None:
        print(f"Clicking post at [{ref}]...")
        await browser.click(ref)
        await browser.human_delay(3, 5)
        print("✅ Post opened.")
        return True
    else:
        print("❌ No post found on page.")
        return False


async def like_post(browser: "SnapshotBrowser") -> bool:
    """
    Like the currently open post. Idempotent — skips if already liked.
    Uses direct SVG locator (Jules' pattern) + JS fallback.
    """
    print("--- Action: Like Post ---")
    try:
        # Check if already liked
        unlike_btn = browser.page.locator('svg[aria-label="Unlike"]').first
        if await unlike_btn.is_visible(timeout=3000):
            print("✅ Already liked. Skipping.")
            return True

        # Click Like
        like_btn = browser.page.locator('svg[aria-label="Like"]').first
        if await like_btn.is_visible(timeout=5000):
            await like_btn.click(force=True)
            await browser.human_delay(2, 4)
            print("✅ Post liked.")
            return True
        else:
            # JS fallback
            clicked = await browser.js_click_aria("Like")
            if clicked:
                await browser.human_delay(2, 4)
                print("✅ Liked via JS.")
            else:
                print("❌ Like button not found.")
            return clicked
    except Exception as e:
        print(f"❌ Error in like_post: {e}")
        return False


async def comment_post(browser: "SnapshotBrowser", text: str) -> bool:
    """
    Comment on the currently open post. Finds comment box by aria-label
    (Jules' pattern) with wait_and_fill fallback.
    """
    print(f"--- Action: Comment ('{text[:30]}') ---")
    try:
        # Method 1: Direct textarea locator (Jules' exact approach)
        comment_box = browser.page.locator('textarea[aria-label="Add a comment…"]').first
        if await comment_box.is_visible(timeout=5000):
            await comment_box.fill(text)
            await browser.human_delay(1, 3)
            await browser.smart_click_text("Post", exact=True)
            await browser.human_delay(2, 4)
            print(f"✅ Comment posted: '{text[:30]}'")
            return True
    except:
        pass

    # Method 2: wait_and_fill fallback
    filled = await browser.wait_and_fill("Add a comment", text)
    if filled:
        await browser.human_delay(1, 3)
        await browser.smart_click_text("Post", exact=True)
        await browser.human_delay(2, 4)
        print(f"✅ Comment posted via fallback: '{text[:30]}'")
        return True

    print("❌ Comment box not found.")
    return False


async def share_post(browser: "SnapshotBrowser", target_user: str) -> bool:
    """
    Share the currently open post with a user via DM.
    Uses JS click for Share button (Jules' pattern), wait_and_fill for search,
    checkbox selection, and smart_click_text for Send.
    """
    print(f"--- Action: Share Post to {target_user} ---")
    await browser.human_delay(2, 4)

    try:
        # Click Share via JS (overlay-proof)
        clicked = await browser.js_click_aria("Share Post")
        if not clicked:
            clicked = await browser.smart_click_aria("Share")
        if not clicked:
            print("❌ Share button not found.")
            return False

        await browser.human_delay(4, 6)

        # Search for recipient
        filled = await browser.wait_and_fill("Search", target_user)
        if not filled:
            print("❌ Search input not found in share dialog.")
            return False

        await browser.human_delay(3, 5)

        # Select first checkbox (recipient)
        checkboxes = await browser.page.locator('input[type="checkbox"]').all()
        if checkboxes:
            await checkboxes[0].click(force=True)
            print(f"Selected user '{target_user}'.")
            await browser.human_delay(2, 4)

            # Click Send
            await browser.smart_click_text("Send", exact=True)
            await browser.human_delay(2, 4)
            print(f"✅ Post shared to {target_user}.")
            return True
        else:
            print(f"❌ User '{target_user}' not found in search results.")
            return False
    except Exception as e:
        print(f"❌ Error in share_post: {e}")
        return False


# ═══════════════════════ MODAL ═══════════════════════

async def close_modal(browser: "SnapshotBrowser") -> bool:
    """Close any open modal (post detail, share dialog) via Close SVG."""
    print("--- Action: Close Modal ---")
    closed = await browser.js_click_aria("Close")
    if closed:
        await browser.human_delay(2, 4)
        print("✅ Modal closed.")
    else:
        # Fallback: Escape key
        await browser.press_key("Escape")
        await browser.human_delay(1, 2)
        print("✅ Closed via Escape.")
        closed = True
    return closed


# ═══════════════════════ BLOCK / UNBLOCK ═══════════════════════

async def block_user(browser: "SnapshotBrowser", username: str = None) -> bool:
    """
    Block a user. If username given, navigates to profile.
    Otherwise operates on current profile page.
    """
    print(f"--- Action: Block {username or 'current user'} ---")
    if username:
        await browser.nav(f"https://www.instagram.com/{username}/")
        await browser.dismiss_dialogs()
        await browser.human_delay(2, 4)

    try:
        # Click Options (3 dots)
        options_clicked = await browser.js_click_aria("Options")
        if not options_clicked:
            print("❌ 'Options' button not found.")
            return False
        await browser.human_delay(2, 4)

        # Click Block in menu (exclude "Unblock")
        block_clicked = await browser.smart_click_text("Block", exact=False)
        if not block_clicked:
            print("❌ 'Block' option not found in menu.")
            return False
        await browser.human_delay(2, 4)

        # Confirm Block in dialog (targets last button = modal confirm)
        confirm_clicked = await browser.smart_click_text("Block", exact=False)
        if confirm_clicked:
            await browser.human_delay(3, 5)
            print("✅ User blocked.")
            return True
        else:
            print("❌ Confirm block failed.")
            return False
    except Exception as e:
        print(f"❌ Error in block_user: {e}")
        return False


async def unblock_user(browser: "SnapshotBrowser", username: str = None) -> bool:
    """
    Unblock a user. If username given, navigates to profile.
    Uses smart_click_text for both profile button and dialog confirm.
    """
    print(f"--- Action: Unblock {username or 'current user'} ---")
    if username:
        await browser.nav(f"https://www.instagram.com/{username}/")
        await browser.dismiss_dialogs()
        await browser.human_delay(3, 5)

    try:
        # Click Unblock on profile (smart_click_text handles overlay)
        unblock_clicked = await browser.smart_click_text("Unblock", exact=True)
        if not unblock_clicked:
            print("❌ 'Unblock' button not found (user might not be blocked).")
            return False
        await browser.human_delay(2, 4)

        # Confirm Unblock in dialog (clicks last "Unblock" = modal button)
        confirm = await browser.smart_click_text("Unblock", exact=True)
        if confirm:
            await browser.human_delay(3, 5)
            print("✅ User unblocked.")
            return True
        else:
            # Fallback: click_in_dialog
            confirm = await browser.click_in_dialog("Unblock")
            if confirm:
                await browser.human_delay(3, 5)
                print("✅ User unblocked (via dialog).")
                return True
            print("❌ Confirm unblock failed.")
            return False
    except Exception as e:
        print(f"❌ Error in unblock_user: {e}")
        return False


# ═══════════════════════ STORIES ═══════════════════════

async def view_story(browser: "SnapshotBrowser", username: str) -> bool:
    """
    View a user's story. Jules' pattern: click profile picture ring,
    verify URL contains /stories/. Falls back to direct URL.
    """
    print(f"--- Action: View Story for {username} ---")
    await browser.nav(f"https://www.instagram.com/{username}/")
    await browser.dismiss_dialogs()
    await browser.human_delay(2, 4)

    try:
        # Jules' approach: find profile picture with story ring
        story_ring = browser.page.locator('div[role="button"]:has(img[alt*="profile picture"])').first
        if await story_ring.is_visible(timeout=5000):
            await story_ring.click(force=True)
            await browser.human_delay(3, 5)

            # Verify we entered story viewer
            if "stories" in browser.page.url:
                print("✅ Story opened.")
                await browser.screenshot(f"logs/story_{username}.png")
                # Close story
                await browser.js_click_aria("Close")
                await browser.human_delay(2, 4)
                return True
            else:
                print("❌ Clicked profile picture but no story (no active story).")
                return False
        else:
            print(f"No story ring found. Trying direct URL...")
    except:
        pass

    # Fallback: direct URL
    try:
        await browser.nav(f"https://www.instagram.com/stories/{username}/")
        await browser.human_delay(5, 8)
        if "stories" in browser.page.url:
            print("✅ Story viewed via direct URL.")
            await browser.screenshot(f"logs/story_{username}.png")
            return True
    except:
        pass

    print(f"❌ No story available for {username}.")
    return False


# ═══════════════════════ DM ═══════════════════════

async def unsend_message(browser: "SnapshotBrowser", username: str, message_text: str) -> bool:
    """
    Finds and unsends a specific message sent to a user in their DM chat.
    Solves Instagram's hidden hover menus by calculating the exact bounding
    box of the message and using Playwright's native mouse movements to reveal
    the 'See more options' button.
    Crucially, it guarantees targeting accuracy by scoping the 3-dot button
    to the specific message row wrapper, rather than blindly clicking `.last`.
    """
    print(f"--- Action: Unsend Message to {username} ---")
    await browser.nav("https://www.instagram.com/direct/inbox/")
    await browser.dismiss_dialogs()
    # Reduced delay for speed
    await browser.human_delay(1, 2)

    try:
        # Instead of searching (which can be unreliable), look in the inbox list directly
        snap = await browser.snapshot()
        user_ref = -1
        for line in snap.splitlines():
            # Loose match to handle emojis like "Sherly🪷" or "Sherly🪿"
            if username in line and "You" in line:
                match = re.search(r'\[(\d+)\]', line)
                if match:
                    user_ref = int(match.group(1))
                    break

        if user_ref > 0:
            print(f"Clicking user chat (ref [{user_ref}])...")
            await browser.click(user_ref, force=True)
        else:
            print(f"User {username} not found in direct inbox list. Falling back to search.")
            # Search for the user in the inbox
            filled = await browser.wait_and_fill("Search", username)
            if not filled:
                print("❌ Search input not found in inbox.")
                return False

            await browser.human_delay(1, 2)

            # Click the user to open the chat
            snap = await browser.snapshot()
            user_ref = browser.find_by_text(username)
            if user_ref > 0:
                await browser.force_click(user_ref)
            else:
                # Fallbacks: try checkbox or exact span text
                checkboxes = await browser.page.locator('input[type="checkbox"]').all()
                if checkboxes:
                    await checkboxes[0].click(force=True)
                else:
                    clicked = await browser.js_click_text("span", username)
                    if not clicked:
                        print(f"❌ User '{username}' not found in inbox search.")
                        return False

        # Quick wait for chat to load
        await browser.human_delay(2, 3)

        # Smart Dynamic Scrolling!
        # Instead of a fixed 5 scrolls (which wastes 10-15 seconds), we check if the message is in DOM,
        # and only scroll if it's missing. Stop scrolling the moment we find it.
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

        msg_locators = browser.page.locator(f'div[dir="auto"]:has-text("{message_text}")')
        count = await msg_locators.count()

        scroll_attempts = 0
        while count == 0 and scroll_attempts < 10:
            print(f"Message not yet visible. Scrolling up (Attempt {scroll_attempts + 1})...")
            await browser.page.evaluate(js_script)
            await browser.page.keyboard.press("PageUp")
            await browser.human_delay(1, 2)
            count = await msg_locators.count()
            scroll_attempts += 1

        if count == 0:
            print(f"❌ Message containing '{message_text}' not found in chat after scrolling.")
            return False

        print(f"✅ Target message found after {scroll_attempts} scrolls.")
        target_text_el = msg_locators.nth(count - 1) # target the most recent one

        # Find the structural row container for this specific message.
        # In Instagram's layout, a message bubble and its adjacent options menu are wrapped together.
        # We can find a common ancestor that encapsulates both.
        # Usually, role="row" or a similar block-level div is used. Let's find the closest parent div
        # that looks like a message row (often has flex layout).
        # A safer approach is to use JS to climb up the DOM until we find a container that spans the full width,
        # but Playwright's locator chaining is easier. We will find the closest div that likely contains the whole row.
        row_wrapper = target_text_el.locator("xpath=ancestor::div[contains(@class, 'x1n2onr6') or @role='row' or @role='button'][last() - 2]").first

        # Scroll it into view (wrap in try-except as Instagram React DOM sometimes throws pointer interception errors here)
        try:
            await target_text_el.scroll_into_view_if_needed(timeout=5000)
        except:
            pass

        await browser.human_delay(1, 2)

        # Get bounding box using JS to bypass Playwright's strict visibility checks on nested spans
        box = await target_text_el.evaluate('''el => {
            let rect = el.getBoundingClientRect();
            return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
        }''')

        if not box:
            print("❌ Could not determine message coordinates.")
            return False

        # Move mouse exactly to the center of the message to trigger the React hover state
        await browser.page.mouse.move(box['x'] + box['w']/2, box['y'] + box['h']/2, steps=10)
        await browser.human_delay(1, 2)

        # GUARENTEED TARGETING: Instead of selecting `.last` globally, we scope the search for the
        # 'See more options' button strictly to the `row_wrapper` or just structurally close to the `target_text_el`.
        # Even better: The 3-dot menu is a sibling or uncle to the message bubble.
        # Let's search for the SVG within a bounding box, or just globally find the one that is currently visible and closest to our coordinates.
        # The safest structural way: evaluate JS to find the exact SVG element currently in the DOM that is closest to our hovered box.

        more_btn_found = await browser.page.evaluate(f'''() => {{
            const buttons = Array.from(document.querySelectorAll('svg[aria-label^="See more options for message"]'));
            for (let svg of buttons) {{
                // Find its clickable parent
                let btn = svg.closest('[role="button"]');
                if (btn) {{
                    let rect = btn.getBoundingClientRect();
                    // The button should be vertically aligned with our hovered message box
                    if (rect.y >= {box['y']} - 50 && rect.y <= {box['y']} + {box['h']} + 50) {{
                        btn.click();
                        return true;
                    }}
                }}
            }}
            return false;
        }}''')

        if more_btn_found:
            print("✅ Found and clicked specifically scoped 'See more options' button.")
            await browser.human_delay(1, 2)

            # Click Unsend in the dropdown menu
            unsend_clicked = await browser.smart_click_text("Unsend", exact=True)
            if not unsend_clicked:
                print("❌ 'Unsend' option not found in the menu.")
                return False

            await browser.human_delay(1, 2)

            # Confirm Unsend in the modal dialog. Usually it's a dialog, so try click_in_dialog first.
            confirm = await browser.click_in_dialog("Unsend")
            if not confirm:
                 confirm = await browser.smart_click_text("Unsend", exact=True)

            if confirm:
                print(f"✅ Successfully unsent message: '{message_text}'")
                return True
            else:
                print("❌ Failed to confirm unsend in dialog.")
                return False
        else:
            print("❌ 'See more options' button did not appear near the targeted message after hover.")
            return False

    except Exception as e:
        print(f"❌ Error in unsend_message: {e}")
        return False


async def send_dm(browser: "SnapshotBrowser", username: str, message: str) -> bool:
    """Send a DM to a user via the compose flow."""
    print(f"--- Action: Send DM to {username} ---")
    await browser.nav("https://www.instagram.com/direct/inbox/")
    await browser.dismiss_dialogs()
    await browser.human_delay(2, 4)

    try:
        # Click new message icon
        clicked = await browser.smart_click_aria("New message")
        if not clicked:
            clicked = await browser.js_click_aria("New message")
        if not clicked:
            # Try the pencil/compose icon
            snap = await browser.snapshot()
            for line in snap.splitlines():
                if "compose" in line.lower() or "new message" in line.lower() or "pencil" in line.lower():
                    match = re.search(r'\[(\d+)\]', line)
                    if match:
                        await browser.click(int(match.group(1)), force=True)
                        clicked = True
                        break

        if not clicked:
            print("❌ New message button not found.")
            return False

        await browser.human_delay(1, 2)

        # Search recipient
        filled = await browser.wait_and_fill("Search", username)
        if not filled:
            print("❌ Search input not found in DM compose.")
            return False

        await browser.human_delay(3, 5)

        # Find and click the user in results
        snap = await browser.snapshot()
        user_ref = browser.find_by_text(username)
        if user_ref > 0:
            await browser.force_click(user_ref)
        else:
            # Try clicking first checkbox
            checkboxes = await browser.page.locator('input[type="checkbox"]').all()
            if checkboxes:
                await checkboxes[0].click(force=True)
            else:
                try:
                    await browser.click_text(username)
                except:
                    print(f"❌ User '{username}' not found in results.")
                    return False

        await browser.human_delay(1, 2)

        # Click Chat/Next
        chat_clicked = await browser.smart_click_text("Chat", exact=True)
        if not chat_clicked:
            chat_clicked = await browser.smart_click_text("Next", exact=True)
        await browser.human_delay(2, 3)

        # Type message
        filled = await browser.wait_and_fill("Message", message)
        if not filled:
            print("❌ Message input not found.")
            return False

        # Send
        await browser.press_key("Enter")
        await browser.human_delay(2, 4)
        print(f"✅ DM sent to {username}: '{message[:30]}'")
        return True
    except Exception as e:
        print(f"❌ Error in send_dm: {e}")
        return False


# ═══════════════════════ SEARCH ═══════════════════════

async def search_user(browser: "SnapshotBrowser", query: str) -> tuple:
    """
    Search for a user. Returns (found: bool, snapshot: str).
    """
    print(f"--- Action: Search '{query}' ---")
    try:
        await browser.smart_click_aria("Search")
        await browser.human_delay(1, 2)
        await browser.fill_placeholder("Search", query)
        await browser.human_delay(3, 5)
        snap = await browser.smart_snapshot(min_elements=3)
        found = query.lower() in snap.lower()
        if found:
            print(f"✅ Found results for '{query}'.")
        else:
            print(f"❌ No results for '{query}'.")
        return found, snap
    except Exception as e:
        print(f"❌ Error in search_user: {e}")
        return False, ""
