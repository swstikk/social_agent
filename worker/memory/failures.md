# Failure Log — Learn From Past Mistakes

> **Read this file BEFORE every task.** It prevents repeating the same mistakes.

## Format
```
## DATE — Short title
- Problem: what went wrong
- Fix: what solved it
- Prevention: how to avoid it next time
```

## Known Issues

### Instagram Login
- Instagram sometimes shows "Suspicious Login" popup when logging from new location
- Fix: use cookies FIRST, credential login only as fallback
- 2FA may be triggered — ask Commander for code via API

### Selector Changes
- Instagram/Reddit change their CSS classes frequently
- Fix: NEVER use raw CSS selectors. Use snapshot-based control (scripts/browser.py)
- Always re-snapshot after navigation — refs change

### Rate Limiting
- Instagram blocks after too many actions in short time
- Fix: Follow anti-ban rules in skills/instagram/SKILL.md
- If "Action Blocked" appears → STOP everything for 24 hours → report to Commander
