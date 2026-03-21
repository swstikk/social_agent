# Jules Commander Workflow Guide

This guide explains how you (the human user acting as a "Commander") can orchestrate and manage another AI ("The Worker") operating in a separate sandbox using the Jules REST API.

This setup allows you to remotely control a Jules session, monitor its progress, approve its plans, and provide it with new tasks or feedback entirely through a Command Line Interface (CLI).

## Prerequisites

Before you can command the Worker, you must set your Jules API key as an environment variable. The `jules_commander.py` tool will read this to authenticate your commands.

```bash
export JULES_API_KEY="your_api_key_here"
```

You will also need the **Session ID** of the Worker you want to control.

## The Commander Tool (`jules_commander.py`)

This Python script is your control panel. It interacts with the Jules API (`v1alpha` endpoints) to execute your commands.

### 1. Check Worker Status

**Command:** `python3 jules_commander.py status <SESSION_ID>`

**Purpose:** Use this command to see what the Worker is currently doing. It fetches the latest activities from the API.

**When to use it:**
- When you first connect to a new Worker session.
- Periodically, to check if the Worker has finished a task or is stuck.
- **Crucially:** To see if the Worker has generated a "Plan" that is "PENDING APPROVAL".

### 2. Approve Worker Plan

**Command:** `python3 jules_commander.py approve <SESSION_ID>`

**Purpose:** If a Worker session is configured to require explicit plan approval, it will pause execution after generating a plan. This command tells the API that you approve the plan, unblocking the Worker to start executing.

**When to use it:**
- Only after you have run the `status` command and confirmed there is a pending plan waiting for approval.

### 3. Send Command/Message to Worker

**Command:** `python3 jules_commander.py message <SESSION_ID> "Your instructions here"`

**Purpose:** This sends a new text prompt to the Worker, just like typing a message in a chat interface.

**When to use it:**
- To give the Worker its initial task.
- To provide feedback or corrections if the Worker makes a mistake.
- To answer questions the Worker might have asked (which you saw using the `status` command).
- To assign a new task after the previous one is completed.

## Orchestration Workflow Example

Here is a typical workflow for managing a Worker:

1. **Start:** You have a fresh Worker Session ID.
2. **Assign Task:** `python3 jules_commander.py message 123456789 "Create a simple README file."`
3. **Monitor:** Wait a few moments, then check what the Worker is doing: `python3 jules_commander.py status 123456789`
4. **Approve:** If the status shows a plan is pending approval, unblock it: `python3 jules_commander.py approve 123456789`
5. **Follow up:** After some time, check the status again. If the task is done, you can send another message: `python3 jules_commander.py message 123456789 "Great, now add a section about contributing."`

By looping through these steps, you can effectively act as the "Commander" for any Jules AI session.
