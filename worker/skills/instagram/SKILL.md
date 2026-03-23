---
name: instagram
description: 'Automate Instagram via Playwright browser. Use for: login, DMs (read/send), posts, stories, likes, follow/unfollow, notifications. Always use snapshot-based control. Read this BEFORE any Instagram task.'
---

# Instagram Skill

## Platform URL
`https://www.instagram.com`

## Login Flow

### Step 1 — Try Cookie Login First (ALWAYS)
```python
cookies_path = "config/cookies/instagram.json"
if os.path.exists(cookies_path):
    await browser.load_cookies(cookies_path)
    await browser.nav("https://www.instagram.com/")
    await browser.human_delay(3, 5)
    snap = await browser.snapshot()
    if "Search" in snap or "Home" in snap:
        # Logged in!
        return True
```

### Step 2 — Credential Login (if cookies expired)
```python
await browser.nav("https://www.instagram.com/accounts/login/")
await browser.human_delay(3, 5)
snap = await browser.snapshot()
# Find username input, password input
await browser.type_text(username_ref, USERNAME)
await browser.type_text(password_ref, PASSWORD)
await browser.click(login_button_ref)
await browser.wait_for_idle()
```

### Step 3 — 2FA Handling
If 2FA screen appears → **STOP and ask Commander:**
```python
worker_to_commander.py --message "[NEED_PERMISSION] Instagram asking for 2FA code. Platform: instagram. Provide code or approve skip."
```

### Step 4 — Save Cookies After Login
```python
await browser.save_cookies("config/cookies/instagram.json")
```

---

## Read DMs

### Navigate
```python
await browser.nav("https://www.instagram.com/direct/inbox/")
await browser.human_delay(3, 6)
```

### Find Unread Messages
```python
snap = await browser.snapshot()
# Unread DMs appear with bold text / blue dot
# Look for elements with unread indicators
# Report each: sender name, message preview, timestamp
```

### Read a Specific Thread
```python
# Click on thread from snapshot
await browser.click(thread_ref)
await browser.wait_for_idle()
await browser.human_delay(2, 4)

# Snapshot the conversation
snap = await browser.snapshot()
# Extract visible messages
```

---

## Send DM

### To Existing Thread
```python
await browser.nav("https://www.instagram.com/direct/inbox/")
snap = await browser.snapshot()
# Click the target thread
await browser.click(thread_ref)
await browser.wait_for_idle()

# Snapshot to find message input
snap = await browser.snapshot()
# Find TEXTAREA or INPUT with "Message..." placeholder
await browser.human_type(msg_input_ref, message_text)
await browser.human_delay(1, 3)

# Find and click Send
snap = await browser.snapshot()
await browser.click(send_button_ref)
await browser.human_delay(2, 4)

# Screenshot for proof
await browser.screenshot("logs/dm_sent.png")
```

### To New Person
```python
await browser.nav("https://www.instagram.com/direct/inbox/")
snap = await browser.snapshot()
# Click "New Message" or compose icon
await browser.click(new_msg_ref)

# Search for recipient
snap = await browser.snapshot()
await browser.human_type(search_ref, recipient_username)
await browser.human_delay(3, 5)

# Select from results
snap = await browser.snapshot()
await browser.click(result_ref)
# Click "Chat" or "Next"
await browser.click(next_ref)

# Now type and send (same as existing thread)
```

---

## Smart High-Level Actions (NEW API)

Instead of manually navigating and using snapshots for complex interactions (like Share, Block, Follow), you MUST use the provided high-level actions in `worker/skills/instagram/actions.py`. These functions utilize JS evaluation and exact locators to bypass Instagram's complex overlays and intercepting dialogs. They are also idempotent (e.g., skip liking if already liked).

```python
from skills.instagram.actions import follow_user, unfollow_user, watch_story, like_post, comment_post, share_post, block_user, unblock_user, open_first_post

# Follow / Unfollow (Idempotent - safe to call repeatedly)
await follow_user(browser, "cristiano")
await unfollow_user(browser, "cristiano")

# Story Viewing (Captures screenshot proof automatically)
await watch_story(browser, "cristiano")

# Posts (Like, Comment, Share)
if await open_first_post(browser):
    await like_post(browser) # Skips if already liked
    await comment_post(browser, "Great post! 🔥")
    await share_post(browser, "leomessi") # Searches leomessi and sends via DM modal

# Block / Unblock (Handles confirm dialogs dynamically)
await block_user(browser)
await unblock_user(browser)
```

**Important Note:** For the actions listed above, ALWAYS use the smart high-level functions instead of writing manual `browser.click()` or `snapshot()` logic. Instagram's UI often blocks standard Playwright clicks with invisible `<div role="dialog">` elements, which the `actions.py` functions handle automatically via smart JS injection.

---

## Post Content (Manual)
```python
# Click "+" or create new post icon
snap = await browser.snapshot()
await browser.click(create_ref)
await browser.human_delay(2, 4)

# Upload image (if file exists in sandbox)
# Type caption
# Add hashtags
# Click "Share"
```

---

## Share a Reel
```python
await browser.nav(f"https://www.instagram.com/reel/{reel_id}/")
await browser.human_delay(3, 6)
snap = await browser.snapshot()
# Find the Share button
await browser.click(share_ref)
await browser.human_delay(2, 4)

snap = await browser.snapshot()
# Find the recipient search box and type their name
await browser.type_text(search_ref, recipient_username)
await browser.human_delay(2, 4)

snap = await browser.snapshot()
# Select the user from the list
await browser.click(user_ref)

snap = await browser.snapshot()
# Click 'Send'
await browser.click(send_ref)
await browser.screenshot("logs/reel_shared.png")
```

---

## Comment on a Post
```python
await browser.nav(f"https://www.instagram.com/p/{post_id}/")
await browser.human_delay(3, 6)
snap = await browser.snapshot()
# Find the comment input box (often placeholder "Add a comment...")
await browser.type_text(comment_box_ref, comment_text)
await browser.human_delay(1, 3)

snap = await browser.snapshot()
# Find the Post button (or press Enter)
await browser.click(post_button_ref)
await browser.screenshot("logs/commented.png")
```

---

## Anti-Ban Rules ⚠️

| Action | Rate Limit | Cool Down |
|---|---|---|
| DM sends | Max 5 per hour | 30-120 sec between each |
| Follows | Max 10 per hour | 60-180 sec between each |
| Likes | Max 20 per hour | 15-60 sec between each |
| Story views | Max 30 per hour | 5-15 sec between each |
| Login attempts | Max 3 per hour | Wait 30 min after 3 failures |

### Human Behavior Patterns
- **Vary action types** — don't do 5 DMs in a row. Mix: DM, scroll, like, DM, story, DM
- **Natural timing** — humans don't click every 2 seconds. Use `human_delay(5, 20)`
- **Session length** — browse for 5-15 min per "visit", not 60 min straight
- **Scroll before acting** — humans scroll/browse before sending DMs, not go directly

### Red Flags to Avoid
- ❌ Sending identical messages to multiple people
- ❌ Following 50 accounts in 5 minutes
- ❌ Liking every post on someone's profile
- ❌ Logging in from very different geolocations rapidly
- ❌ Using the exact same message text every time

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| "Login required" popup | → Load cookies first. If expired, credential login |
| Element not found after click | → Re-snapshot. Element refs change after navigation |
| "Action Blocked" | → STOP all actions for 24hrs. Report to Commander |
| 2FA screen | → Ask Commander for code via API |
| "Suspicious Login" | → Report to Commander. May need manual verification |
| Slow page load | → `wait_for_idle()` before snapshot |
