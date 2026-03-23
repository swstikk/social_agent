---
name: reddit
description: 'Automate Reddit via Playwright browser. Use for: login, read posts, comment, upvote/downvote, send DMs, create posts, search subreddits, find coding partners. Always use snapshot-based control.'
---

# Reddit Skill

## Platform URL
`https://www.reddit.com` (use old.reddit.com for simpler DOM if new reddit is problematic)

## Login Flow

### Step 1 — Try Cookie Login
```python
cookies_path = "config/cookies/reddit.json"
if os.path.exists(cookies_path):
    await browser.load_cookies(cookies_path)
    await browser.nav("https://www.reddit.com/")
    await browser.human_delay(3, 5)
    snap = await browser.snapshot()
    if "Create Post" in snap or "u/" in snap:
        return True  # Logged in
```

### Step 2 — Credential Login
```python
await browser.nav("https://www.reddit.com/login/")
await browser.human_delay(3, 5)
snap = await browser.snapshot()
# Find username and password inputs
await browser.type_text(user_ref, USERNAME)
await browser.type_text(pass_ref, PASSWORD)
await browser.click(login_ref)
await browser.wait_for_idle()
await browser.save_cookies("config/cookies/reddit.json")
```

---

## Search Subreddits
```python
await browser.nav("https://www.reddit.com/search/?q=coding+partner&type=sr")
await browser.human_delay(3, 5)
snap = await browser.snapshot()
# List subreddit results
```

## Browse a Subreddit
```python
await browser.nav("https://www.reddit.com/r/learnprogramming/new/")
await browser.human_delay(3, 6)
snap = await browser.snapshot()
# Read post titles and authors
```

## Read a Post
```python
await browser.click(post_ref)  # From subreddit listing
await browser.wait_for_idle()
snap = await browser.snapshot()
# Read post content and comments
```

---

## Create a Post
```python
await browser.nav("https://www.reddit.com/r/{subreddit}/submit")
await browser.human_delay(3, 5)
snap = await browser.snapshot()
# Find title input
await browser.type_text(title_ref, post_title)
# Find body textarea
await browser.type_text(body_ref, post_body)
await browser.human_delay(2, 4)
# Click "Post" button
await browser.click(post_button_ref)
await browser.wait_for_idle()
await browser.screenshot("logs/reddit_post.png")
```

---

## Comment on a Post
```python
# Navigate to the post first
snap = await browser.snapshot()
# Find comment box
await browser.type_text(comment_ref, comment_text)
await browser.human_delay(2, 5)
await browser.click(submit_comment_ref)
await browser.screenshot("logs/reddit_comment.png")
```

---

## Send DM
```python
await browser.nav(f"https://www.reddit.com/message/compose/?to={username}")
await browser.human_delay(3, 5)
snap = await browser.snapshot()
# Find subject input
await browser.type_text(subject_ref, subject_text)
# Find message body
await browser.type_text(body_ref, message_text)
await browser.click(send_ref)
await browser.screenshot("logs/reddit_dm.png")
```

---

## Upvote
```python
snap = await browser.snapshot()
# Find upvote button (arrow icon)
await browser.click(upvote_ref)
```

---

## Anti-Ban Rules ⚠️

| Action | Rate Limit | Cool Down |
|---|---|---|
| Posts | Max 1 per 10 min per subreddit | Varies by subreddit |
| Comments | Max 3 per 10 min | 60-120 sec between |
| DMs | Max 5 per hour | 120-300 sec between |
| Upvotes | Max 20 per hour | 10-30 sec between |

### Red Flags
- ❌ Posting same content in multiple subreddits rapidly (detected as spam)
- ❌ Commenting the same text on different posts
- ❌ Mass upvoting posts from one user
- ❌ Creating account and immediately posting (need account age)

---

## Common Errors & Fixes

| Error | Fix |
|---|---|
| "You are doing that too much" | → Wait 10 min. Reduce action frequency |
| Account suspended | → Report to Commander immediately. Don't retry |
| CAPTCHA/reCAPTCHA | → Try screenshot + report to Commander |
| Post removed by mods | → Note in scratchpad.md, try different subreddit |
