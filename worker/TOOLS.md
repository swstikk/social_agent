# Your Toolbox — Available Tools Reference

## 1. Browser Control — `scripts/browser.py`

Your primary tool. **Snapshot-based** — never use raw CSS selectors.

```python
from scripts.browser import SnapshotBrowser

browser = SnapshotBrowser()
await browser.launch()                         # Start browser
await browser.nav("https://instagram.com")     # Navigate
snap = await browser.snapshot()                # Get numbered element map
await browser.click(5)                         # Click element #5
await browser.type_text(3, "hello 🥺")         # Type into element #3
await browser.screenshot("proof.png")          # Screenshot for evidence
await browser.wait_for_idle()                  # Wait for network idle
await browser.wait_for_url("**/inbox")         # Wait for URL change
```

### Snapshot Output Example
```
[1] INPUT 'Search'
[2] BUTTON 'Send'
[3] TEXTAREA 'Message...'
[4] A 'Home'
[5] DIV 'Username — last message preview'
```
- Numbers change every snapshot — **always re-snapshot after navigation**
- If element not found by number → re-snapshot → try again

### Human-Like Behavior
```python
await browser.human_type(3, "hello", min_delay=80, max_delay=200)  # Realistic typing
await browser.human_delay(5, 15)               # Random pause 5-15 sec
await browser.human_scroll(direction="down", amount=3)  # Smooth scroll
```

### Cookie/Session Management
```python
await browser.save_cookies("config/cookies/instagram.json")    # Save login state
await browser.load_cookies("config/cookies/instagram.json")    # Restore login
```

---

## 2. Commander Communication — `worker_to_commander.py`

**⚠️ RULE ZERO: ALL communication with Commander goes through this. NEVER chat.**

```bash
# Simple message
python3 worker_to_commander.py --message "[REPORT] status: DM sent to @user. confidence: 92%"

# With screenshot proof
python3 worker_to_commander.py --message "[REPORT] status: Liked 3 posts." --screenshot proof.png

# Asking for permission
python3 worker_to_commander.py --message "[NEED_PERMISSION] Want to follow @randomuser. Approve?"
```

All messages auto-prefixed with "Worker says: ".

---

## 3. Memory System

### `memory/failures.md` — Learn from mistakes
```markdown
## 2026-03-23 — Instagram selector broke
- Problem: 'div[role="textbox"]' stopped working
- Fix: Use snapshot → find TEXTAREA → type by ref number
- Prevention: Always snapshot first, never hardcode selectors
```
**Read this BEFORE every task!**

### `memory/scratchpad.md` — Notes between sessions
```markdown
## Instagram Notes
- Login requires 2FA every ~48 hours
- Rate limit: max 5 DMs per hour
- Best time to check DMs: every 3-5 minutes
```

---

## 4. Skills — `skills/<platform>/SKILL.md`

Before working on any platform, **read its SKILL.md first**:
```bash
cat skills/instagram/SKILL.md    # Instagram playbook
cat skills/reddit/SKILL.md       # Reddit playbook
cat skills/whatsapp/SKILL.md     # WhatsApp playbook
```

---

## 5. System Tools — `scripts/system.py`

```python
from scripts.system import SystemTools

# Run any bash command
output = SystemTools.run_command("ls -la /app")

# Upload screenshot to ImgBB (get shareable URL)
url = SystemTools.upload_screenshot("proof.png")

# Download a file
SystemTools.download_file("https://example.com/file.zip", "/tmp/file.zip")
```

---

## 6. Heartbeat — `heartbeat.py`

**Your first action on every startup:**
```bash
# Kill any old heartbeat
pkill -f heartbeat.py 2>/dev/null

# Launch new heartbeat in background
export JULES_API_KEY="..."
export COMMANDER_SESSION_ID="..."
nohup python3 heartbeat.py > /tmp/heartbeat.log 2>&1 &
```
This survives after your session ends and keeps pinging Commander every 5 min.

---

## 7. State Management

### `state/current_task.json`
```json
{
  "task": "Check Instagram DMs",
  "started_at": "2026-03-23T03:00:00",
  "status": "in_progress",
  "platform": "instagram"
}
```

### `state/schedule.json`
```json
{
  "recurring": [
    {"id": "check_insta_dms", "every_minutes": 3, "skill": "instagram"},
    {"id": "check_whatsapp", "every_minutes": 5, "skill": "whatsapp"}
  ]
}
```
