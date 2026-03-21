import os
import time
import random
from playwright.sync_api import sync_playwright

# Credentials
USERNAME = os.environ.get("IG_USERNAME", "")
PASSWORD = os.environ.get("IG_PASSWORD", "")
TARGET_CHAT = os.environ.get("IG_TARGET_CHAT", "")

if not USERNAME or not PASSWORD or not TARGET_CHAT:
    print("Please set IG_USERNAME, IG_PASSWORD, and IG_TARGET_CHAT environment variables.")
    exit(1)

def human_delay(min_ms=500, max_ms=2500):
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)

def type_human_like(page, selector, text):
    for char in text:
        page.locator(selector).type(char, delay=random.randint(50, 150))
    human_delay()

def run(playwright):
    browser = playwright.chromium.launch(headless=True, slow_mo=50)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720}
    )
    page = context.new_page()

    try:
        print("Navigate to Instagram login page...")
        page.goto("https://www.instagram.com/accounts/login/")
        # Wait a bit longer for potential redirects or bot challenges
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass # ignore timeout and proceed to check selector
        human_delay(3000, 5000)

        page.screenshot(path="pre_login.png")
        print("Saved pre-login screenshot to pre_login.png")

        # Sometime instagram redirects to a root page where we need to click "Log in" first
        if page.locator("a[href='/accounts/login/?source=auth_switcher']").is_visible():
             page.locator("a[href='/accounts/login/?source=auth_switcher']").click()
             human_delay(2000, 3000)

        # Handle cookie consent if it appears
        if page.locator("button:has-text('Allow all cookies')").is_visible():
            page.locator("button:has-text('Allow all cookies')").click()
            human_delay()
        elif page.locator("button:has-text('Decline optional cookies')").is_visible():
            page.locator("button:has-text('Decline optional cookies')").click()
            human_delay()

        print("Entering credentials...")
        try:
             page.wait_for_selector("input[name='username']", timeout=15000)
             type_human_like(page, "input[name='username']", USERNAME)
             type_human_like(page, "input[name='password']", PASSWORD)

             print("Clicking login...")
             page.locator("button[type='submit']").click()
        except Exception as e:
             print("Could not find username input. Bot protection active.")
             page.screenshot(path="blocked_state.png")
             print("Saved blocked screenshot to blocked_state.png")
             return

        # Wait for either successful login or an error
        page.wait_for_timeout(5000)
        page.screenshot(path="login_attempt.png")
        print("Saved screenshot of login attempt to login_attempt.png")

        # Check if login was successful by looking for a common element on the home page (like the nav bar)
        if page.locator("svg[aria-label='Home']").is_visible() or page.locator("svg[aria-label='Search']").is_visible():
            print("Login successful! Navigating to Inbox...")

            # Save login state if needed for later
            context.storage_state(path="state.json")

            # Go to direct messages
            page.goto("https://www.instagram.com/direct/inbox/")
            human_delay(3000, 5000)

            # Handle "Not Now" for notifications
            if page.locator("button:has-text('Not Now')").is_visible():
                page.locator("button:has-text('Not Now')").click()
                human_delay()

            page.screenshot(path="inbox.png")
            print("Saved screenshot of inbox to inbox.png")

            print(f"Searching for chat with {TARGET_CHAT}...")
            # We look for the user's name in the chat list. Instagram DOM is complex, so we use text.
            chat_locator = page.locator(f"span:has-text('{TARGET_CHAT}')").first
            if chat_locator.is_visible():
                chat_locator.click()
                human_delay(2000, 4000)

                print("Reading chat messages...")
                page.screenshot(path="chat.png")
                print("Saved screenshot of chat to chat.png")

                # Try to extract the last few messages. Again, relying on common Instagram DOM structures
                # Usually messages have a specific generic role or div structure. Let's try to get text from visible divs
                # A more robust way would need real DOM inspection.
                # Just as an experiment, let's grab the text content of the message list area.
                messages = page.locator("div[role='row']").all_text_contents()
                print("\n--- Recent Chat Messages ---")
                for msg in messages[-10:]: # print last 10 roles
                    print(msg.strip())
                print("----------------------------\n")

                # Save to file
                with open("chat_summary.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(messages[-10:]))
                print("Saved chat summary to chat_summary.txt")

            else:
                print(f"Could not find chat with {TARGET_CHAT} in the visible list.")

        else:
            print("Login failed or blocked. Check login_attempt.png.")
            error_message = page.locator("div[data-testid='login-error-message']").text_content() if page.locator("div[data-testid='login-error-message']").is_visible() else "Unknown error"
            print(f"Error: {error_message}")

    except Exception as e:
        print(f"An error occurred: {e}")
        page.screenshot(path="error_state.png")
        print("Saved screenshot of error state to error_state.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
