"""
SnapshotBrowser — OpenClaw-style Snapshot-Based Playwright Wrapper

Instead of fragile CSS selectors that break when sites update,
this uses an accessibility/ARIA-based snapshot system:
  1. snapshot() → numbered element map (text-based)
  2. click(ref) → click by number
  3. type_text(ref, text) → type by number

This is what OpenClaw and Peekaboo do internally.
"""

import asyncio
import json
import os
import random
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class SnapshotBrowser:
    """Snapshot-based browser control for reliable automation."""

    def __init__(self):
        self.page: Page = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self._playwright = None
        self._element_map: dict = {}  # ref_number → element_handle
        self._last_snapshot: str = ""

    # ──────────────────────────── LIFECYCLE ────────────────────────────

    async def launch(self, headless=True):
        """Launch browser with anti-detection settings."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        self.page = await self.context.new_page()
        print("[Browser] Launched successfully")

    async def close(self):
        """Clean shutdown."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        print("[Browser] Closed")

    # ──────────────────────────── NAVIGATION ────────────────────────────

    async def nav(self, url: str, timeout=15000):
        """Navigate to URL and wait for load."""
        print(f"[Browser] Navigating to {url}")
        await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        await self.human_delay(2, 4)

    # ──────────────────────────── SNAPSHOT (CORE) ────────────────────────────

    async def snapshot(self) -> str:
        """
        Take accessibility snapshot — returns numbered element map.
        
        Like OpenClaw's `openclaw browser snapshot` or Peekaboo's `peekaboo see`.
        
        Returns text like:
            [1] BUTTON 'Send'
            [2] INPUT 'Search'
            [3] TEXTAREA 'Message...'
            [4] A 'Home'
        """
        elements = []
        counter = 1
        self._element_map = {}

        # Query all interactive + text elements
        selectors = [
            'button', 'input', 'textarea', 'a[href]',
            '[role="button"]', '[role="link"]', '[role="textbox"]',
            '[role="tab"]', '[role="menuitem"]', '[role="option"]',
            '[role="listitem"]', '[contenteditable="true"]',
        ]
        selector_string = ", ".join(selectors)

        all_elements = await self.page.query_selector_all(selector_string)

        for el in all_elements:
            try:
                visible = await el.is_visible()
                if not visible:
                    continue

                # Get identifying info
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                aria_label = await el.get_attribute("aria-label") or ""
                placeholder = await el.get_attribute("placeholder") or ""
                role = await el.get_attribute("role") or ""
                text = ""
                try:
                    text = (await el.text_content() or "").strip()
                except:
                    pass
                el_type = await el.get_attribute("type") or ""

                # Build display name (priority: aria-label → placeholder → text → type)
                name = aria_label or placeholder or text or el_type or "?"
                name = name[:60].replace("\n", " ").strip()

                if not name or name == "?":
                    continue

                # Tag display
                display_tag = tag.upper()
                if role:
                    display_tag = role.upper()

                ref = f"[{counter}]"
                elements.append(f"{ref} {display_tag} '{name}'")
                self._element_map[counter] = el
                counter += 1

                # Cap at 50 elements to keep it readable
                if counter > 50:
                    break

            except Exception:
                continue

        self._last_snapshot = "\n".join(elements)
        element_count = len(elements)
        print(f"[Snapshot] Found {element_count} interactive elements")
        return self._last_snapshot

    # ──────────────────────────── ACTIONS ────────────────────────────

    async def click(self, ref: int, force=False):
        """Click element by ref number from last snapshot."""
        el = self._element_map.get(ref)
        if not el:
            raise ValueError(
                f"[Error] Ref [{ref}] not found. Available refs: "
                f"{list(self._element_map.keys())[:10]}. "
                f"Run snapshot() first to get fresh refs."
            )
        try:
            await el.scroll_into_view_if_needed()
            await self.human_delay(0.3, 0.8)
            await el.click(force=force)
            print(f"[Click] Clicked [{ref}] (force={force})")
        except Exception as e:
            print(f"[Click] Failed on [{ref}]: {e}")
            raise

    # ──────────────────────────── SMART HELPERS ────────────────────────────

    async def js_click_aria(self, aria_label: str) -> bool:
        """
        Bypass intercepting dialogs/overlays by using native JavaScript to click an SVG
        or its closest interactive parent button by aria-label.
        """
        print(f"[SmartClick] Attempting JS click on aria-label: '{aria_label}'")
        clicked = await self.page.evaluate(f'''(label) => {{
            let svgs = document.querySelectorAll(`svg[aria-label="${{label}}"]`);
            if (svgs.length > 0) {{
                // Iterate backwards since modals/overlays are usually appended last
                for (let i = svgs.length - 1; i >= 0; i--) {{
                    let svg = svgs[i];
                    let btn = svg.closest('button') || svg.closest('div[role="button"]') || svg.closest('a');
                    if (btn) {{
                        btn.click();
                        return true;
                    }} else {{
                        // Fallback to clicking the SVG itself or its direct parent
                        (svg.parentElement || svg).click();
                        return true;
                    }}
                }}
            }}
            return false;
        }}''', aria_label)
        if clicked:
            print(f"[SmartClick] Successfully clicked '{aria_label}' via JS")
        else:
            print(f"[SmartClick] Failed to find or click '{aria_label}' via JS")
        return clicked

    async def wait_and_fill(self, placeholder: str, text: str, timeout=5000):
        """
        Smartly wait for an input with a specific placeholder to be attached and visible,
        then fill it. Handles modal latency.
        """
        print(f"[SmartFill] Looking for input with placeholder '{placeholder}'")
        try:
            # Wait for any input to attach first to handle React latency
            await self.page.locator('input').first.wait_for(state='attached', timeout=timeout)
        except Exception:
            pass

        inputs = await self.page.locator('input').all()
        for inp in inputs:
            ph = await inp.get_attribute('placeholder')
            if ph and placeholder.lower() in ph.lower():
                await inp.fill(text)
                print(f"[SmartFill] Filled '{text}' into placeholder '{ph}'")
                return True

        # If input not found, try textarea
        textareas = await self.page.locator('textarea').all()
        for ta in textareas:
            ph = await ta.get_attribute('placeholder')
            aria = await ta.get_attribute('aria-label')
            if (ph and placeholder.lower() in ph.lower()) or (aria and placeholder.lower() in aria.lower()):
                await ta.fill(text)
                print(f"[SmartFill] Filled '{text}' into textarea (placeholder/aria '{ph or aria}')")
                return True

        print(f"[SmartFill] Failed to find input/textarea matching '{placeholder}'")
        return False

    async def smart_click_text(self, text: str, exact=False, force=True, timeout=5000) -> bool:
        """
        Find a button containing exact or partial text and click it using force=True to bypass overlays.
        If multiple exist (e.g., in a block confirmation dialog), clicks the last one (usually the active modal).
        """
        print(f"[SmartClickText] Looking for button with text '{text}'")
        try:
            if exact:
                locator = self.page.locator(f'button:has-text("{text}")').last
            else:
                # Playwright's default has-text is a substring match
                locator = self.page.locator(f'button', has_text=text).last

            if await locator.is_visible(timeout=timeout):
                await locator.click(force=force)
                print(f"[SmartClickText] Clicked button '{text}'")
                return True
        except Exception as e:
            print(f"[SmartClickText] Playwright locator failed: {e}. Falling back to JS...")

        # JS fallback for stubborn overlapping buttons (like Instagram Block confirms)
        clicked = await self.page.evaluate(f'''(args) => {{
            let btns = document.querySelectorAll('button, div[role="button"]');
            for(let i = btns.length - 1; i >= 0; i--) {{
                let bText = btns[i].innerText || "";
                if (args.exact && bText.trim() === args.text) {{
                    btns[i].click(); return true;
                }} else if (!args.exact && bText.includes(args.text)) {{
                    btns[i].click(); return true;
                }}
            }}
            return false;
        }}''', {"text": text, "exact": exact})

        if clicked:
            print(f"[SmartClickText] Clicked button '{text}' via JS fallback")
        else:
            print(f"[SmartClickText] Failed to find button '{text}'")
        return clicked

    async def type_text(self, ref: int, text: str, delay_ms=80):
        """Type into element by ref number."""
        el = self._element_map.get(ref)
        if not el:
            raise ValueError(f"[Error] Ref [{ref}] not found. Run snapshot() first.")
        await el.click()
        await self.human_delay(0.5, 1)
        await el.type(text, delay=delay_ms)
        print(f"[Type] Typed {len(text)} chars into [{ref}]")

    async def human_type(self, ref: int, text: str, min_delay=80, max_delay=200):
        """Type with realistic human-like random delays between keys."""
        el = self._element_map.get(ref)
        if not el:
            raise ValueError(f"[Error] Ref [{ref}] not found. Run snapshot() first.")
        await el.click()
        await self.human_delay(0.3, 0.8)
        for char in text:
            delay = random.randint(min_delay, max_delay)
            await el.type(char, delay=delay)
        print(f"[HumanType] Typed {len(text)} chars into [{ref}]")

    async def clear_and_type(self, ref: int, text: str):
        """Clear existing text and type new text."""
        el = self._element_map.get(ref)
        if not el:
            raise ValueError(f"[Error] Ref [{ref}] not found.")
        await el.click()
        await self.page.keyboard.press("Control+A")
        await self.page.keyboard.press("Backspace")
        await self.human_delay(0.3, 0.5)
        await el.type(text, delay=random.randint(60, 150))

    # ──────────────────────────── WAITS (OpenClaw-style) ────────────────────────────

    async def wait_for_url(self, pattern: str, timeout=10000):
        """Wait for URL to match pattern. Like OpenClaw's `browser wait --url`."""
        print(f"[Wait] Waiting for URL: {pattern}")
        await self.page.wait_for_url(pattern, timeout=timeout)

    async def wait_for_idle(self, timeout=10000):
        """Wait for network to settle. Like `browser wait --load networkidle`."""
        print("[Wait] Waiting for network idle...")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            print("[Wait] Network idle timeout — continuing anyway")

    async def wait_for_element(self, selector: str, timeout=5000):
        """Wait for a specific element to appear."""
        await self.page.wait_for_selector(selector, timeout=timeout)

    # ──────────────────────────── SCROLLING ────────────────────────────

    async def human_scroll(self, direction="down", amount=3):
        """Smooth scroll with human-like pauses."""
        delta = 400 if direction == "down" else -400
        for _ in range(amount):
            await self.page.mouse.wheel(0, delta)
            await self.human_delay(0.5, 1.5)
        print(f"[Scroll] Scrolled {direction} x{amount}")

    # ──────────────────────────── SCREENSHOTS ────────────────────────────

    async def screenshot(self, path: str = "screenshot.png", full_page=False):
        """Take screenshot for evidence/proof."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        await self.page.screenshot(path=path, full_page=full_page)
        print(f"[Screenshot] Saved to {path}")

    # ──────────────────────────── COOKIES ────────────────────────────

    async def save_cookies(self, path: str):
        """Save browser cookies to file for session persistence."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        cookies = await self.context.cookies()
        with open(path, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"[Cookies] Saved {len(cookies)} cookies to {path}")

    async def load_cookies(self, path: str):
        """Load cookies from file to restore login session."""
        if not os.path.exists(path):
            print(f"[Cookies] File not found: {path}")
            return False
        with open(path, "r") as f:
            cookies = json.load(f)
        await self.context.add_cookies(cookies)
        print(f"[Cookies] Loaded {len(cookies)} cookies from {path}")
        return True

    # ──────────────────────────── UTILITIES ────────────────────────────

    async def human_delay(self, min_sec=1, max_sec=5):
        """Random delay to mimic human behavior."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def get_page_text(self) -> str:
        """Get all visible text on the page."""
        return await self.page.inner_text("body")

    async def get_current_url(self) -> str:
        """Get current page URL."""
        return self.page.url

    async def press_key(self, key: str):
        """Press a keyboard key (Enter, Tab, Escape, etc.)."""
        await self.page.keyboard.press(key)
        print(f"[Key] Pressed {key}")

    async def find_by_text(self, text: str) -> int:
        """Find element ref by text content from last snapshot."""
        for ref, el in self._element_map.items():
            try:
                el_text = await el.text_content() or ""
                if text.lower() in el_text.lower():
                    return ref
            except:
                continue
        return -1  # Not found


# ──────────────────────────── STANDALONE TEST ────────────────────────────

async def _test():
    """Quick test to verify browser works."""
    b = SnapshotBrowser()
    await b.launch()
    await b.nav("https://www.google.com")
    snap = await b.snapshot()
    print("--- Snapshot ---")
    print(snap)
    print("--- End ---")
    await b.screenshot("/tmp/test_snapshot.png")
    await b.close()

if __name__ == "__main__":
    asyncio.run(_test())
