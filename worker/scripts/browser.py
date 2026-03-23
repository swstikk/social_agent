"""
SnapshotBrowser v4 — Merged Best-of-Both (Ours + Jules)

Snapshot-based Playwright wrapper for Instagram/React automation.
Uses accessibility snapshots instead of fragile CSS selectors.

FROM OURS:
  - SVG/span/div aria-label capture in snapshot
  - smart_snapshot() retry for lazy-loaded content
  - find_by_text/find_by_aria/find_all_by_text/get_element_info
  - Screenshot with animations='disabled' + try-catch
  - nav() with networkidle wait
  - dismiss_dialogs(), click_in_dialog()
  - Playwright fallbacks: click_text, click_role, fill_placeholder, type_into_focused

FROM JULES:
  - scroll_into_view before every click
  - click(ref, force) with force parameter
  - js_click_aria() with REVERSE iteration (modals are last in DOM)
  - smart_click_text() with .last locator (targets modal buttons)
  - wait_and_fill() with input iteration fallback
"""

import asyncio
import json
import os
import random
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class SnapshotBrowser:
    """Snapshot-based browser control — hardened for Instagram/React."""

    def __init__(self):
        self.page: Page = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self._playwright = None
        self._element_map: dict = {}     # ref_number → element_handle
        self._element_info: dict = {}    # ref_number → {tag, aria, text, role, placeholder, href}
        self._last_snapshot: str = ""

    # ═══════════════════════ LIFECYCLE ═══════════════════════

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

    # ═══════════════════════ NAVIGATION ═══════════════════════

    async def nav(self, url: str, timeout=30000):
        """Navigate to URL, wait for DOM + network idle."""
        print(f"[Nav] {url}")
        await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        # Wait for React/Instagram to finish rendering
        try:
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass  # Instagram never truly idles, continue anyway
        await self.human_delay(2, 4)

    # ═══════════════════════ SNAPSHOT (CORE) ═══════════════════════

    async def snapshot(self) -> str:
        """
        Take accessibility snapshot — returns numbered element map.

        Captures: buttons, inputs, links, textboxes, SVG icons with aria-labels,
        and React/Instagram divs with role="button".

        Returns text like:
            [1] BUTTON 'Send'
            [2] SVG 'Like'  (aria-label on SVG icon)
            [3] LINK 'cristiano' [post]
        """
        elements = []
        counter = 1
        self._element_map = {}
        self._element_info = {}

        # WIDE selector — covers Instagram's React components + SVGs
        selectors = [
            'button', 'input', 'textarea', 'a[href]', 'select',
            '[role="button"]', '[role="link"]', '[role="textbox"]',
            '[role="tab"]', '[role="menuitem"]', '[role="option"]',
            '[role="dialog"] button', '[role="dialog"] [role="button"]',
            '[contenteditable="true"]',
            'svg[aria-label]',           # Instagram's icon buttons (Like, Share, etc.)
            'span[aria-label]',          # Instagram spans with labels
            'div[aria-label]',           # Various labeled divs
        ]
        selector_string = ", ".join(selectors)

        try:
            all_elements = await self.page.query_selector_all(selector_string)
        except Exception as e:
            print(f"[Snapshot] Query failed: {e}")
            return ""

        seen_labels = set()  # Deduplicate

        for el in all_elements:
            try:
                visible = await el.is_visible()
                if not visible:
                    continue

                # Get ALL identifying info
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                aria_label = (await el.get_attribute("aria-label") or "").strip()
                placeholder = (await el.get_attribute("placeholder") or "").strip()
                role = (await el.get_attribute("role") or "").strip()
                el_type = (await el.get_attribute("type") or "").strip()
                href = (await el.get_attribute("href") or "").strip()

                text = ""
                try:
                    raw = await el.text_content()
                    if raw:
                        text = raw.strip()[:60].replace("\n", " ")
                except:
                    pass

                # Build display name (priority order)
                name = aria_label or placeholder or text or el_type or ""
                name = name[:60].strip()

                if not name:
                    continue

                # Deduplicate — skip if same tag:label seen
                dedup_key = f"{tag}:{name}"
                if dedup_key in seen_labels:
                    continue
                seen_labels.add(dedup_key)

                # Display tag
                if tag == "svg":
                    display_tag = "SVG"
                elif role:
                    display_tag = role.upper()
                else:
                    display_tag = tag.upper()

                # Extra info for links
                extra = ""
                if href and "/p/" in href:
                    extra = " [post]"
                elif href and "/reel/" in href:
                    extra = " [reel]"
                elif href and "/stories/" in href:
                    extra = " [story]"

                ref = f"[{counter}]"
                line = f"{ref} {display_tag} '{name}'{extra}"
                elements.append(line)
                self._element_map[counter] = el
                self._element_info[counter] = {
                    "tag": tag, "aria": aria_label, "text": text,
                    "role": role, "placeholder": placeholder, "href": href
                }
                counter += 1

                if counter > 80:
                    break

            except Exception:
                continue

        self._last_snapshot = "\n".join(elements)
        print(f"[Snapshot] Found {len(elements)} elements")
        return self._last_snapshot

    async def smart_snapshot(self, min_elements=5, max_retries=3) -> str:
        """
        Snapshot with retry — waits for React lazy-loading.

        Instagram lazy-loads content, so the first snapshot often finds
        very few elements. Retries with increasing delays until
        min_elements are found.
        """
        for attempt in range(max_retries):
            snap = await self.snapshot()
            count = len(self._element_map)
            if count >= min_elements:
                return snap
            wait = (attempt + 1) * 2  # 2s, 4s, 6s
            print(f"[SmartSnap] Only {count} elements, waiting {wait}s (attempt {attempt+1}/{max_retries})")
            await self.human_delay(wait, wait + 1)
        return self._last_snapshot

    # ═══════════════════════ ELEMENT FINDING ═══════════════════════

    def find_by_text(self, text: str) -> int:
        """Find element ref by text, aria-label, or placeholder (from cached snapshot)."""
        text_lower = text.lower()
        for ref, info in self._element_info.items():
            if (text_lower in (info.get("text", "")).lower() or
                text_lower in (info.get("aria", "")).lower() or
                text_lower in (info.get("placeholder", "")).lower()):
                return ref
        return -1

    def find_by_aria(self, aria_text: str) -> int:
        """Find element ref specifically by aria-label."""
        aria_lower = aria_text.lower()
        for ref, info in self._element_info.items():
            if aria_lower in (info.get("aria", "")).lower():
                return ref
        return -1

    def find_all_by_text(self, text: str) -> list:
        """Find ALL element refs matching text or aria-label."""
        text_lower = text.lower()
        matches = []
        for ref, info in self._element_info.items():
            if (text_lower in (info.get("text", "")).lower() or
                text_lower in (info.get("aria", "")).lower()):
                matches.append(ref)
        return matches

    def get_element_info(self, ref: int) -> dict:
        """Get full debug info about an element."""
        return self._element_info.get(ref, {})

    # ═══════════════════════ CLICK ACTIONS ═══════════════════════

    async def click(self, ref: int, force=False):
        """Click element by ref number. Scrolls into view first (Jules' pattern)."""
        el = self._element_map.get(ref)
        if not el:
            available = list(self._element_map.keys())[:15]
            raise ValueError(
                f"[Error] Ref [{ref}] not found. Available: {available}. "
                f"Run snapshot() to get fresh refs."
            )
        try:
            await el.scroll_into_view_if_needed()
            await self.human_delay(0.3, 0.8)
            await el.click(force=force)
            info = self._element_info.get(ref, {})
            print(f"[Click] [{ref}] {info.get('aria', '') or info.get('text', '')}")
        except Exception as e:
            print(f"[Click] Failed [{ref}]: {e}")
            raise

    async def force_click(self, ref: int):
        """Click with force=True — bypasses overlay interception."""
        await self.click(ref, force=True)

    async def click_text(self, text: str, exact=False):
        """Playwright fallback — click by visible text."""
        try:
            if exact:
                await self.page.get_by_text(text, exact=True).first.click()
            else:
                await self.page.get_by_text(text).first.click()
            print(f"[Click] Text '{text}'")
        except Exception as e:
            print(f"[Click] Text '{text}' failed: {e}")
            raise

    async def click_aria(self, label: str):
        """Playwright fallback — click by aria-label."""
        try:
            await self.page.get_by_label(label).first.click()
            print(f"[Click] Aria '{label}'")
        except Exception as e:
            print(f"[Click] Aria '{label}' failed: {e}")
            raise

    async def click_role(self, role: str, name: str = None, exact=False):
        """Playwright fallback — click by ARIA role."""
        try:
            if name:
                await self.page.get_by_role(role, name=name, exact=exact).first.click()
            else:
                await self.page.get_by_role(role).first.click()
            print(f"[Click] Role '{role}' name='{name}'")
        except Exception as e:
            print(f"[Click] Role '{role}' failed: {e}")
            raise

    async def click_selector(self, selector: str):
        """Last resort — click by CSS selector."""
        try:
            await self.page.click(selector, timeout=5000)
            print(f"[Click] Selector '{selector}'")
        except Exception as e:
            print(f"[Click] Selector '{selector}' failed: {e}")
            raise

    # ═══════════════════════ SMART HELPERS ═══════════════════════
    # Combined from Jules' + ours — these bypass Instagram's overlays

    async def js_click_aria(self, aria_label: str) -> bool:
        """
        JS injection click by aria-label — bypasses ALL overlay interception.
        REVERSE iterates (Jules' pattern) — modals are appended LAST in DOM.

        Use for: Share Post, Options, Close, Like (when blocked by overlay).
        """
        clicked = await self.page.evaluate('''(label) => {
            let svgs = document.querySelectorAll(`svg[aria-label="${label}"]`);
            if (svgs.length > 0) {
                // Reverse: modals/overlays are appended last
                for (let i = svgs.length - 1; i >= 0; i--) {
                    let svg = svgs[i];
                    let btn = svg.closest('button') || svg.closest('div[role="button"]') || svg.closest('a');
                    if (btn) {
                        btn.click();
                        return true;
                    } else {
                        (svg.parentElement || svg).click();
                        return true;
                    }
                }
            }
            // Also check non-SVG elements with aria-label
            let others = document.querySelectorAll(`[aria-label="${label}"]`);
            for (let i = others.length - 1; i >= 0; i--) {
                let el = others[i];
                let btn = el.closest('button') || el.closest('div[role="button"]') || el;
                btn.click();
                return true;
            }
            return false;
        }''', aria_label)
        if clicked:
            print(f"[JSClickAria] Clicked '{aria_label}'")
        else:
            print(f"[JSClickAria] NOT FOUND: '{aria_label}'")
        return clicked

    async def smart_click_text(self, text: str, exact=False, force=True, timeout=5000) -> bool:
        """
        Find button by text and click — targets LAST match (modal buttons).
        Jules' pattern: .last locator + force=True + JS fallback.
        """
        try:
            if exact:
                locator = self.page.locator('button', has_text=text).last
            else:
                locator = self.page.locator('button', has_text=text).last
            if await locator.is_visible(timeout=timeout):
                await locator.click(force=force)
                print(f"[SmartClickText] Clicked '{text}'")
                return True
        except:
            pass

        # JS fallback — reverse iterate all buttons (Jules' pattern)
        clicked = await self.page.evaluate('''(args) => {
            let btns = document.querySelectorAll('button, div[role="button"]');
            for (let i = btns.length - 1; i >= 0; i--) {
                let bText = (btns[i].innerText || "").trim();
                if (args.exact && bText === args.text) {
                    btns[i].click(); return true;
                } else if (!args.exact && bText.includes(args.text)) {
                    btns[i].click(); return true;
                }
            }
            return false;
        }''', {"text": text, "exact": exact})
        if clicked:
            print(f"[SmartClickText] JS clicked '{text}'")
        else:
            print(f"[SmartClickText] NOT FOUND: '{text}'")
        return clicked

    async def smart_click_aria(self, label: str) -> bool:
        """
        Find ALL elements with aria-label, click the visible one.
        Instagram has multiple "Like"/"Share" buttons — this picks the right one.
        Tries Playwright first, falls back to JS injection.
        """
        try:
            elements = await self.page.locator(f'[aria-label="{label}"]').all()
            for el in elements:
                try:
                    if await el.is_visible():
                        await el.click(force=True, timeout=3000)
                        print(f"[SmartAria] Clicked '{label}'")
                        return True
                except:
                    continue
        except:
            pass
        # Fallback to JS
        return await self.js_click_aria(label)

    async def js_click(self, selector: str) -> bool:
        """JS click by CSS selector — bypasses overlays."""
        clicked = await self.page.evaluate(f'''() => {{
            let el = document.querySelector('{selector}');
            if (el) {{
                let btn = el.closest('button') || el.closest('div[role="button"]') || el;
                btn.click();
                return true;
            }}
            return false;
        }}''')
        if clicked:
            print(f"[JSClick] {selector}")
        else:
            print(f"[JSClick] NOT FOUND: {selector}")
        return clicked

    async def js_click_text(self, tag: str, text: str, exclude_text: str = None) -> bool:
        """
        Click element by tag + inner text via JS.
        Use for: Block, Send, Post, Unfollow buttons.
        """
        exclude_check = ""
        if exclude_text:
            exclude_check = f"&& !el.innerText.includes('{exclude_text}')"

        clicked = await self.page.evaluate(f'''() => {{
            let els = document.querySelectorAll('{tag}');
            for (let i = els.length - 1; i >= 0; i--) {{
                let el = els[i];
                if (el.innerText.includes('{text}') {exclude_check}) {{
                    el.click();
                    return true;
                }}
            }}
            return false;
        }}''')
        if clicked:
            print(f"[JSClickText] {tag} containing '{text}'")
        else:
            print(f"[JSClickText] NOT FOUND: {tag} with '{text}'")
        return clicked

    async def wait_and_fill(self, placeholder: str, text: str, timeout=5000) -> bool:
        """
        Wait for input to appear in DOM, then fill it.
        Iterates all inputs/textareas (Jules' pattern for modal latency).
        """
        # Wait for any input to attach first (React latency)
        try:
            await self.page.locator('input').first.wait_for(state='attached', timeout=timeout)
        except:
            pass

        # Search all inputs
        inputs = await self.page.locator('input').all()
        for inp in inputs:
            ph = await inp.get_attribute('placeholder')
            if ph and placeholder.lower() in ph.lower():
                await inp.fill(text)
                print(f"[WaitFill] Filled '{text[:30]}' into input '{ph}'")
                return True

        # Search all textareas (comment box on Instagram)
        textareas = await self.page.locator('textarea').all()
        for ta in textareas:
            ph = await ta.get_attribute('placeholder')
            aria = await ta.get_attribute('aria-label')
            if (ph and placeholder.lower() in ph.lower()) or \
               (aria and placeholder.lower() in aria.lower()):
                await ta.fill(text)
                print(f"[WaitFill] Filled '{text[:30]}' into textarea '{ph or aria}'")
                return True

        # Try aria-label on any element
        try:
            locator = self.page.locator(f'[aria-label="{placeholder}"]').first
            await locator.wait_for(state='attached', timeout=3000)
            await locator.fill(text)
            print(f"[WaitFill] Filled '{text[:30]}' via aria '{placeholder}'")
            return True
        except:
            pass

        print(f"[WaitFill] NOT FOUND: '{placeholder}'")
        return False

    async def click_in_dialog(self, text: str) -> bool:
        """
        Click button inside [role='dialog'] modal.
        For: Unblock confirm, Block confirm, Unfollow confirm.
        """
        try:
            dialog = self.page.locator('[role="dialog"]')
            btn = dialog.get_by_text(text, exact=True).first
            await btn.click(timeout=5000)
            print(f"[Dialog] Clicked '{text}'")
            return True
        except:
            # JS fallback — reverse iterate dialog buttons
            clicked = await self.page.evaluate(f'''() => {{
                let btns = document.querySelectorAll('[role="dialog"] button');
                for (let i = btns.length - 1; i >= 0; i--) {{
                    if (btns[i].innerText.includes('{text}')) {{
                        btns[i].click();
                        return true;
                    }}
                }}
                return false;
            }}''')
            if clicked:
                print(f"[Dialog] JS clicked '{text}'")
            else:
                print(f"[Dialog] '{text}' not found in dialog")
            return clicked

    async def dismiss_dialogs(self):
        """
        Auto-dismiss common Instagram popups.
        'Turn on Notifications', 'Not Now', 'Cancel', etc.
        Call after every nav() to clear overlays before interacting.
        """
        dismissed = 0
        for text in ["Not Now", "Not now"]:
            try:
                btn = self.page.get_by_text(text, exact=True).first
                if await btn.is_visible(timeout=2000):
                    await btn.click(timeout=3000)
                    dismissed += 1
                    await self.human_delay(0.5, 1)
            except:
                continue
        if dismissed:
            print(f"[Dismiss] Cleared {dismissed} dialog(s)")
        return dismissed

    # ═══════════════════════ TYPE ACTIONS ═══════════════════════

    async def type_text(self, ref: int, text: str, delay_ms=80):
        """Type into element by ref number."""
        el = self._element_map.get(ref)
        if not el:
            raise ValueError(f"[Error] Ref [{ref}] not found. Run snapshot() first.")
        await el.click()
        await self.human_delay(0.5, 1)
        await el.type(text, delay=delay_ms)
        print(f"[Type] {len(text)} chars into [{ref}]")

    async def human_type(self, ref: int, text: str, min_delay=80, max_delay=200):
        """Type with human-like random delays per character."""
        el = self._element_map.get(ref)
        if not el:
            raise ValueError(f"[Error] Ref [{ref}] not found. Run snapshot() first.")
        await el.click()
        await self.human_delay(0.3, 0.8)
        for char in text:
            delay = random.randint(min_delay, max_delay)
            await el.type(char, delay=delay)
        print(f"[HumanType] {len(text)} chars into [{ref}]")

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
        print(f"[ClearType] {len(text)} chars into [{ref}]")

    async def type_into_focused(self, text: str, delay_ms=80):
        """Type into whatever element currently has focus."""
        await self.page.keyboard.type(text, delay=delay_ms)
        print(f"[Type] {len(text)} chars into focused element")

    async def fill_placeholder(self, placeholder: str, text: str):
        """Playwright fallback — fill input by placeholder."""
        try:
            await self.page.get_by_placeholder(placeholder).first.fill(text)
            print(f"[Fill] Placeholder '{placeholder}' with '{text[:30]}'")
        except Exception as e:
            print(f"[Fill] Placeholder '{placeholder}' failed: {e}")
            raise

    # ═══════════════════════ WAITS ═══════════════════════

    async def wait_for_url(self, pattern: str, timeout=10000):
        """Wait for URL to match pattern."""
        print(f"[Wait] URL: {pattern}")
        await self.page.wait_for_url(pattern, timeout=timeout)

    async def wait_for_idle(self, timeout=10000):
        """Wait for network to settle."""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            pass

    async def wait_for_element(self, selector: str, timeout=5000):
        """Wait for element to appear."""
        await self.page.wait_for_selector(selector, timeout=timeout)

    async def wait_for_text(self, text: str, timeout=5000):
        """Wait for specific text to appear on page."""
        await self.page.wait_for_function(
            f'document.body.innerText.includes("{text}")',
            timeout=timeout
        )

    # ═══════════════════════ SCROLLING ═══════════════════════

    async def human_scroll(self, direction="down", amount=3):
        """Smooth scroll with human-like pauses."""
        delta = 400 if direction == "down" else -400
        for _ in range(amount):
            await self.page.mouse.wheel(0, delta)
            await self.human_delay(0.5, 1.5)
        print(f"[Scroll] {direction} x{amount}")

    # ═══════════════════════ SCREENSHOTS ═══════════════════════

    async def screenshot(self, path: str = "screenshot.png", full_page=False):
        """Take screenshot — handles Instagram animation timeouts."""
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        try:
            await self.page.screenshot(
                path=path, full_page=full_page,
                animations="disabled", timeout=10000
            )
            print(f"[Screenshot] {path}")
        except Exception:
            print(f"[Screenshot] Timeout on {path} — continuing")

    # ═══════════════════════ COOKIES ═══════════════════════

    async def save_cookies(self, path: str):
        """Save browser cookies for session persistence."""
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        cookies = await self.context.cookies()
        with open(path, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"[Cookies] Saved {len(cookies)} to {path}")

    async def load_cookies(self, path: str) -> bool:
        """Load cookies from file to restore login."""
        if not os.path.exists(path):
            print(f"[Cookies] File not found: {path}")
            return False
        with open(path, "r") as f:
            cookies = json.load(f)
        await self.context.add_cookies(cookies)
        print(f"[Cookies] Loaded {len(cookies)} from {path}")
        return True

    # ═══════════════════════ UTILITIES ═══════════════════════

    async def human_delay(self, min_sec=1, max_sec=5):
        """Random delay to mimic human."""
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def get_page_text(self) -> str:
        """Get all visible text on page."""
        return await self.page.inner_text("body")

    async def get_current_url(self) -> str:
        """Get current URL."""
        return self.page.url

    async def press_key(self, key: str):
        """Press keyboard key (Enter, Escape, Tab, etc.)."""
        await self.page.keyboard.press(key)
        print(f"[Key] {key}")

    async def hover(self, ref: int):
        """Hover over element by ref."""
        el = self._element_map.get(ref)
        if el:
            await el.hover()
            print(f"[Hover] [{ref}]")

    async def get_attribute(self, ref: int, attr: str) -> str:
        """Get attribute of element by ref."""
        el = self._element_map.get(ref)
        if el:
            return await el.get_attribute(attr) or ""
        return ""


# ═══════════════════════ STANDALONE TEST ═══════════════════════

async def _test():
    """Quick test to verify browser works."""
    b = SnapshotBrowser()
    await b.launch()
    await b.nav("https://www.google.com")
    snap = await b.snapshot()
    print("--- Snapshot ---")
    print(snap)
    print("--- End ---")
    await b.screenshot("test_snapshot.png")
    await b.close()

if __name__ == "__main__":
    asyncio.run(_test())
