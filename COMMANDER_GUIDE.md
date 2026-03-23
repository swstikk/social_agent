# The Jules Commander Protocol: A Guide for Human Orchestrators

Welcome, Commander.

This guide outlines the **Master-Worker (Commander-Worker) Architecture**. In this setup, you are the Orchestrator (The Commander). Your job is to manage, direct, and supervise a separate, isolated AI session ("The Worker") operating in its own sandbox environment via the Jules REST API.

You will not interact with the Worker through a standard chat interface. Instead, you will use a powerful Command Line Interface (CLI) tool—`jules_commander.py`—to issue direct commands, check statuses, and approve execution plans.

---

## The Architecture & Your Role

1. **The Commander (You):** You hold the vision. You decide what needs to be built, break it down into high-level tasks, review the AI's plans, and course-correct when necessary.
2. **The Worker (The Jules AI Session):** A fresh instance of an AI agent connected to a source repository. It has no context other than what you provide. It is the execution engine.
3. **The Bridge (The CLI Tool):** `jules_commander.py` uses the Jules REST API to translate your terminal commands into direct API requests to the Worker's session.

### Prerequisites & Authentication
The CLI tool requires authentication to communicate with the API. You **must** set your API key as an environment variable before issuing commands.

```bash
export JULES_API_KEY="your_api_key_here"
```

You must also know the **Session ID** of the Worker you are commanding (e.g., `10290120723086341887`).

---

## The Orchestration Workflow (The Loop)

Managing a Worker is a continuous loop of checking status, analyzing the situation, and taking action.

### Step 1: Check Status (Function 4)
Always start by checking what the Worker is currently doing or if it is waiting for your input.

**Command:**
```bash
python3 jules_commander.py status <SESSION_ID>
```
**What to look for:**
*   Is the Worker idle?
*   Did it encounter an error?
*   Has it generated a "Plan" that is currently "PENDING APPROVAL"?

### Step 2: Analyze & Decide
Based on the status report, decide your next move:
*   **Scenario A:** The Worker just generated a plan and is paused, waiting for your permission to execute. -> **Go to Step 3a (Approve).**
*   **Scenario B:** The Worker is idle, has finished its previous task, or is asking you a clarifying question. -> **Go to Step 3b (Message).**

### Step 3a: Approve Plan (Function 5)
If the status report shows a pending plan, and you agree with the steps the Worker proposed, unblock it so it can begin coding.

**Command:**
```bash
python3 jules_commander.py approve <SESSION_ID>
```

### Step 3b: Send Message / Command (Function 6)
If you need to assign a new task, provide feedback on completed work, or answer a question from the Worker, send a direct message.

**Command:**
```bash
python3 jules_commander.py message <SESSION_ID> "Your instructions here"
```

---

## Commander Prompting Guide & Examples

As a Commander communicating via an API, your prompts should be direct, structured, and focused on outcomes. You are not "chatting"; you are issuing specifications.

Here are practical examples of how to phrase your prompts for maximum effectiveness.

### Example 1: Initializing a New Task
When starting a fresh session, provide clear context and the ultimate goal.

> **Command:**
> `python3 jules_commander.py message <SESSION_ID> "Task: Set up a basic Express.js server. Requirements: It should run on port 3000, include a single GET endpoint at '/' that returns { 'status': 'ok' }, and include a start script in package.json. Please generate a plan for this."`

### Example 2: Providing Feedback on a Plan
If you read the Worker's plan via the `status` command and realize it missed something, DO NOT approve it. Instead, send a message to correct the plan.

> **Command:**
> `python3 jules_commander.py message <SESSION_ID> "Reviewing your plan. You missed the requirement to add CORS middleware. Please update your plan to include installing the 'cors' package and applying it to the Express app before I approve."`

### Example 3: Course Correction During Execution
If you check the `status` and see the Worker is stuck on a bug or heading in the wrong direction, intervene immediately.

> **Command:**
> `python3 jules_commander.py message <SESSION_ID> "Stop current execution. The error log shows a missing database connection string. You need to use process.env.DATABASE_URL instead of hardcoding the localhost URL. Fix this and proceed."`

### Example 4: Task Completion & Handoff
When the `status` indicates the Worker has finished its current task, assign the next logical step in your architecture.

> **Command:**
> `python3 jules_commander.py message <SESSION_ID> "Excellent work on the server setup. Next Phase: Create a Dockerfile to containerize this Node.js application. Ensure you use a lightweight alpine image. Generate a plan for this phase."`