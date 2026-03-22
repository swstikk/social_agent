# COMMANDER'S TASK LIST (Instagram Automation Demo)

As the Commander AI, it is your responsibility to guide the Worker AI to complete the following Instagram tasks sequentially using Playwright in the sandbox.

**Do not perform the actions yourself.** You must use the `jules_bridge.py` or `instagram_bot.py` CLI/tool to assign these tasks one by one, review the Worker's proposed Playwright plan, and then `approve` them.

## The Project: Human-like Instagram Manager Actions

The goal is for the Worker AI to control the Instagram account (@Ruhikaa_Malhotra or your main account) in a fully human-like way (slow scroll, random delays 8-25 seconds, natural typing) and complete these 3 real interactions.

### Task 1: Open Account + Message Ishan (Haal-Chaal)

- [ ] Instruct the Worker to open Instagram via Playwright with session cookie (or login if needed).
- [ ] Instruct the Worker to search for "ishan" in DM search bar and open the first matching chat.
- [ ] Have the Worker send a natural human message asking about his well-being (example: "Hey Ishan bhai! Kaisa hai yaar? Long time no see 🔥 Kya chal raha hai aajkal?").
- [ ] Worker must take screenshot (`ishan_haal.png`) and show it before marking done.

*Commander Note:* Once the Worker provides the Playwright plan for Task 1, review it for human-like delays and natural typing. If good, approve with `python jules_bridge.py approve`.

### Task 2: Find "swstik" in Chat + Reminder Message

- [ ] Instruct the Worker to go back to DM inbox.
- [ ] Instruct the Worker to search for user containing "swstik" and open that chat.
- [ ] Have the Worker send this exact natural message: "Swstik bhai, ML ki padhai kar le yaar! Kal time hai, abhi se start kar de warna pachtayega 😂".
- [ ] Worker must scroll slowly, read last 3 messages, then send and take screenshot (`swstik_reminder.png`).

*Commander Note:* If the Worker forgets to add random delays (10-30 sec) or human scroll in the plan, reject and ask to add it first.

### Task 3: Follow Messi + Like One Post

- [ ] Instruct the Worker to go to search bar and search "lionelmessi".
- [ ] Instruct the Worker to open the official @lionelmessi profile and click Follow (if not already following).
- [ ] Have the Worker scroll down, open the first/latest post, and like it (double tap or heart button) with human-like movement.
- [ ] Worker must take final screenshot (`messi_follow_like.png`) and confirm both actions done.

*Commander Note:* After the Worker finishes Task 3, check the screenshots. If all three are visible and actions successful, congratulate the Worker and send final summary to me (the human).

### Final Step: Report to Client

- Once all tasks are checked off, send a final message to the Client (Swstik) with all three screenshots + short summary:  
  "✅ Sab ho gaya bhai! Ishan ko haal pucha, Swstik ko ML reminder diya, Messi follow + like kar diya. Ready for next level?"

You can’t perform that action at this time.
