---
name: instagram
description: 'Automate Instagram via Playwright browser. Use for: login, DMs (read/send), posts, stories, likes, follow/unfollow, notifications. Always use snapshot-based control. Read this BEFORE any Instagram task.'
---

# Instagram Skill

## Platform URL
`https://www.instagram.com`

## ⚡ Smart High-Level Actions (USE THESE FIRST)

For complex interactions (Follow, Like, Comment, Share, Block), **ALWAYS** use `actions.py`.
These functions handle overlays, popups, JS injection, and force-clicks automatically.

```python
from skills.instagram.actions import *

# Login (cookie or session_id)
await login(browser, session_id="...")
await login(browser, cookies_path="config/cookies/instagram.json")

# Follow / Unfollow (Idempotent — safe to call repeatedly)
await follow_user(browser, "cristiano")    # exact=True prevents "Following" misclick
await unfollow_user(browser, "cristiano")  # handles confirm dialog

# Posts — Like, Comment, Share
if await open_first_post(browser):         # finds Carousel/Post/Reel on profile
    await like_post(browser)               # skips if already liked
    await comment_post(browser, "🔥")     # finds textarea, clicks Post
    await share_post(browser, "leomessi")  # JS click Share → search → Send
    await close_modal(browser)             # closes post detail

# Stories
await view_story(browser, "cristiano")     # ring detection + URL verify

# Block / Unblock
await block_user(browser, "username")      # Options → Block → confirm
await unblock_user(browser, "username")    # Unblock → confirm dialog

# DMs
await send_dm(browser, "user", "Hey!")     # compose flow

# Search
found, results = await search_user(browser, "cristiano")
```

> **IMPORTANT:** For the actions above, ALWAYS use these smart functions instead of manual `click()`/`snapshot()`. Instagram's UI blocks standard clicks with invisible `<div role="dialog">` overlays.

---

## Manual Flows (when actions.py doesn't cover it)

### Login Flow

#### Cookie Login (ALWAYS try first)
```python
cookies_path = "config/cookies/instagram.json"
if os.path.exists(cookies_path):
    await browser.load_cookies(cookies_path)
    await browser.nav("https://www.instagram.com/")
    await browser.dismiss_dialogs()
    snap = await browser.smart_snapshot(min_elements=10)
    if "Search" in snap or "Home" in snap:
        # Logged in!
```

#### Credential Login (if cookies expired)
```python
await browser.nav("https://www.instagram.com/accounts/login/")
snap = await browser.snapshot()
await browser.type_text(username_ref, USERNAME)
await browser.type_text(password_ref, PASSWORD)
await browser.click(login_button_ref)
await browser.wait_for_idle()
await browser.save_cookies("config/cookies/instagram.json")
```

#### 2FA Handling
If 2FA screen appears → **STOP and ask Commander:**
```python
worker_to_commander.py --message "[NEED_PERMISSION] Instagram asking for 2FA code."
```

---

### Read DMs
```python
await browser.nav("https://www.instagram.com/direct/inbox/")
await browser.dismiss_dialogs()
snap = await browser.smart_snapshot(min_elements=5)
# Click on thread, snapshot messages
await browser.click(thread_ref)
snap = await browser.snapshot()
```

### Send DM (manual — for existing threads)
```python
await browser.click(thread_ref)
snap = await browser.snapshot()
await browser.human_type(msg_input_ref, message_text)
await browser.click(send_button_ref)
await browser.screenshot("logs/dm_sent.png")
```

---

### Post Content
```python
snap = await browser.snapshot()
await browser.click(create_ref)  # "+" button
# Upload, caption, hashtags, Share
```

---

## browser.py Smart Helpers Reference

| Method | When to Use |
|---|---|
| `js_click_aria("Share Post")` | SVG icon behind overlay |
| `smart_click_text("Block")` | Button in menu/dialog (targets last=modal) |
| `smart_click_aria("Like")` | Multiple same-label elements |
| `wait_and_fill("Search", text)` | Lazy-loading modal inputs |
| `click_in_dialog("Unblock")` | Confirm button inside role=dialog |
| `dismiss_dialogs()` | "Not Now" / notification popups |
| `force_click(ref)` | Any overlay interception |
| `smart_snapshot(min_elements=10)` | Lazy-loaded pages (Instagram) |

---

## Anti-Ban Rules ⚠️

| Action | Rate Limit | Cool Down |
|---|---|---|
| DM sends | Max 5 per hour | 30-120 sec between each |
| Follows | Max 10 per hour | 60-180 sec between each |
| Likes | Max 20 per hour | 15-60 sec between each |
| Story views | Max 30 per hour | 5-15 sec between each |
| Login attempts | Max 3 per hour | Wait 30 min after 3 failures |
| Comments | Max 10 per hour | 30-60 sec between each |
| Blocks | Max 5 per hour | 60 sec between each |

### Human Behavior Patterns
- **Vary actions** — don't do 5 DMs in a row. Mix: DM, scroll, like, DM, story
- **Natural timing** — use `human_delay(5, 20)` between actions
- **Session length** — 5-15 min per "visit", not 60 min straight
- **Scroll before acting** — humans browse before sending DMs

### Red Flags to Avoid
- ❌ Identical messages to multiple people
- ❌ Following 50 accounts in 5 minutes
- ❌ Liking every post on someone's profile
- ❌ Same message text every time

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| "Login required" popup | → Load cookies first. If expired, credential login |
| Element not found | → Re-snapshot. Refs change after navigation |
| "Action Blocked" | → STOP all actions 24hrs. Report to Commander |
| 2FA screen | → Ask Commander for code |
| "Suspicious Login" | → Report to Commander |
| Overlay blocks click | → Use `js_click_aria()` or `force_click()` |
| Slow page load | → `wait_for_idle()` or `smart_snapshot()` |
| Screenshot timeout | → Already handled (animations=disabled + try-catch) |
