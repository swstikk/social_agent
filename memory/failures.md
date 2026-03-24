## 2024-03-24: Inefficient Bulk Message Deletion (Instagram)
- Error: The AI worker took 1 hour to delete just 2 messages because of a "hit-and-trial" approach (repeatedly writing, modifying, and testing one-off python deletion scripts and re-fetching the inbox).
- Fix: For bulk or repetitive tasks (like deleting all messages sent by "You"), **ALWAYS** follow the optimal 3-step strategy:
    1. Navigate to the chat and take a full HTML/DOM snapshot to see the message alignment.
    2. Write a quick parsing block to identify only the user's specific text strings (e.g., right-aligned messages) and form a predefined list (array) of target strings.
    3. Run a **single** Playwright loop script that just executes `unsend_message` on every text string in that predefined array.
- Lesson: Do not guess DOM structure or run blind loops trying to check if an element is clickable. Extract the exact text targets *first*, then act.
