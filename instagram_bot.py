import os
import time
import random
import json
import urllib.request
from playwright.sync_api import sync_playwright

def human_delay(min_ms=500, max_ms=2500):
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)

def fetch_and_format_cookies():
    url = "https://api.github.com/repos/swstikk/social_agent/contents/cookies.json"
    print(f"Fetching cookies from {url}...")
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3.raw"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            session_cookie = data.get("instagram")
            if session_cookie:
                pw_cookies = {
                    "cookies": [
                        {
                            "name": "sessionid",
                            "value": session_cookie.strip(),
                            "domain": ".instagram.com",
                            "path": "/",
                            "httpOnly": True,
                            "secure": True,
                            "sameSite": "None"
                        }
                    ],
                    "origins": []
                }
                with open("pw_state.json", "w") as out_f:
                    json.dump(pw_cookies, out_f, indent=4)
                print("Successfully fetched and formatted cookies.")
                return "pw_state.json"
            else:
                print("Error: Could not find 'instagram' key in downloaded cookies.json")
                return None
    except Exception as e:
        print(f"Error downloading or parsing cookies: {e}")
        return None

def run(playwright):
    storage_state_path = fetch_and_format_cookies()
    if not storage_state_path:
        print("Failed to prepare storage state. Exiting.")
        exit(1)

    browser = playwright.chromium.launch(headless=True, slow_mo=50)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720},
        storage_state=storage_state_path
    )
    page = context.new_page()

    try:
        print("Navigating to Instagram Inbox directly using cookies...")
        page.goto("https://www.instagram.com/direct/inbox/")

        try:
             page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
             pass

        human_delay(3000, 5000)

        page.screenshot(path="inbox_direct.png")
        print("Saved screenshot of inbox to inbox_direct.png")

        # Check if we were redirected back to login meaning the session cookie was invalid or expired
        if "/accounts/login/" in page.url:
             print("Session cookie seems invalid or expired. Redirected to login page.")
             page.screenshot(path="redirected_login.png")
             return

        # Check if inbox loaded successfully
        try:
            # Wait for search icon or home icon as indicator of successful page load
            page.wait_for_selector("svg[aria-label='Home'], svg[aria-label='Search']", timeout=15000)
            print("Successfully reached the inbox!")

            # Handle "Not Now" for notifications
            try:
                 not_now_btn = page.wait_for_selector("button:has-text('Not Now')", timeout=5000)
                 if not_now_btn:
                     not_now_btn.click()
                     human_delay()
            except Exception:
                 pass

            page.screenshot(path="inbox.png")
            print("Saved screenshot of inbox to inbox.png")

            print("Searching for chat with @yrrr_swstik...")

            # Let's wait for an element that indicates the chat list is rendered
            # Instagram often uses a generic role="listbox" or "none" for the chats container.
            # We can also wait for 'Requests' text which is usually next to 'Messages'
            page.wait_for_selector("span:has-text('Requests')", timeout=15000)

            # Look for the chat using the specific preview text snippet "Aur batao"
            # as it's the most reliable unique string for this exact chat in the inbox
            # given the stylised name is hard to target via plain text queries.
            chat_locator = page.locator("span[dir='auto']:has-text('Aur batao')").first

            if not chat_locator.is_visible():
                print("Could not find the chat via 'Aur batao', trying to click the element below 'Requests'")
                # If we really can't find it, we try clicking based on coordinate proximity to 'Requests' or nth item
                chat_locator = page.locator("a[href^='/direct/t/']").nth(0) # Click the topmost a-tag link to a chat thread

            chat_locator.click()
            human_delay(3000, 5000)

            print("Reading chat messages...")
            page.screenshot(path="chat.png")
            print("Saved screenshot of chat to chat.png")

            # Extract messages. We can look for dir='auto' which contains text
            messages = page.locator("div[dir='auto']").all_text_contents()
            print("\n--- Recent Chat Messages ---")

            summary_msgs = []
            # The last few dir='auto' elements inside the message window are usually the text bubbles
            # Let's filter out common UI strings
            ignore_list = ['Message...', 'View profile', 'ruhikaa_malhotra']
            for msg in messages:
                clean_msg = msg.strip()
                if clean_msg and clean_msg not in ignore_list and len(clean_msg) > 1:
                    print(clean_msg)
                    summary_msgs.append(clean_msg)
            print("----------------------------\n")

            # Save to file
            with open("chat_summary.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(summary_msgs[-10:]))
            print("Saved chat summary to chat_summary.txt")

        except Exception as e:
            print(f"Login failed, blocked, or timed out looking for elements. Error: {e}")
            page.screenshot(path="login_attempt_error.png")

    except Exception as e:
        print(f"A critical error occurred: {e}")
        page.screenshot(path="error_state.png")
        print("Saved screenshot of error state to error_state.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
