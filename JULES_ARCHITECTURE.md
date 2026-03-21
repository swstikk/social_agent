# Jules: Architecture & Sandbox Orchestration

Namaste! This document explains exactly how I (Jules) function within this sandbox. It outlines the architecture of my connection to the sandbox and the fundamental algorithm (Agentic Loop) I use to accomplish tasks.

## 1. The Core Secret: I don't "Live" inside the Sandbox

If you run a command like `ps aux` or `ls -la /` inside this sandbox, you won't find a `jules_agent.py` or `daemon.js` running in the background.

**Why?** Because my "brain" (the Large Language Model) and my "orchestrator" (the code that sends me your prompts and executes my tool calls) run on **completely external servers**.

The sandbox is merely a dumb, isolated environment (a container or microVM). It knows nothing about me until my external orchestrator connects to it (typically via SSH or a similar API) to execute a command and fetch the result.

## 2. How I Receive Prompts

Here is the flow of how your chat message reaches me:

1. **User Types a Message:** You type your command in the UI.
2. **UI Sends to Backend:** The UI sends your prompt to my external backend servers.
3. **Prompt injected into Context:** The backend takes your prompt, appends it to my current "Conversation History" (context window), and adds my system instructions (which tell me what tools I have).
4. **LLM Generation:** The external server feeds this massive block of text to me (the LLM). I start generating a response.

## 3. The "Loop" (The Agentic Loop)

My intelligence comes from the **ReAct (Reasoning + Acting) loop**. I don't just generate text; I generate structured commands called **Tool Calls**.

Here is my core algorithm:

### Step 1: Think (Reasoning)
When I receive your prompt, I analyze it. I look at my available tools (e.g., `run_in_bash_session`, `read_file`, `write_file`, `set_plan`). I decide what I need to do first.

### Step 2: Act (Tool Call)
Instead of just talking to you, I generate a special JSON/XML payload asking my orchestrator to do something.
*Example: "I need to know the files here. I will call `run_in_bash_session(command='ls -la')`."*

### Step 3: Pause
Once I output a Tool Call, **I completely pause**. My generation stops. I go to sleep.

### Step 4: The Orchestrator Executes
My external orchestrator takes the tool call (`ls -la`), securely connects to this sandbox, runs the bash command, captures the `stdout`/`stderr` (the output), and brings it back.

### Step 5: Observe
The orchestrator wakes me up by appending the output of `ls -la` to our conversation history as a "Tool Response". I read this output.

### Step 6: Loop or Finish
I read the new information. I ask myself: "Do I have enough information to fulfill the user's request?"
- **If NO:** I go back to Step 1 (Think) and make another tool call.
- **If YES:** I use the `message_user` tool to finally talk back to you in the chat, summarizing what I did.

## 4. The "Return Trip": How the Sandbox Replies Back

You asked a very sharp question: *"sandbox se wapas kaise aata haii... sandbox me kuch too aise file hogi jo tujhe kuch provide karati hogi"*.

You are correct that *something* in the sandbox must tell the orchestrator "I am done" and send the output back. But it's not a pre-installed agent daemon. The orchestrator dynamically uses a combination of **SSH**, **Tmux**, and a **"Stamp" file watcher**.

Here is the exact mechanism (the secret sauce) revealed by looking at the process list (`ps aux`) in this sandbox:

### 1. The SSH Connection and Tmux
When you start a session with me, my orchestrator connects to the sandbox via **SSH** and starts a background terminal multiplexer session using **`tmux`**.
All my bash commands (like `npm install` or `python script.py`) are sent into this single, persistent `tmux` session.

### 2. The File Watcher (`inotifywait`)
Before sending a command to `tmux`, the orchestrator starts a small, temporary shell script that acts as a watcher. You can actually see this script running in the process list:
`inotifywait -e create,moved_to --include /stamp$ /run/devbox-session/default`

What is this doing?
- It is patiently watching a specific temporary directory (`/run/devbox-session/default/`).
- It is waiting for a specific file to be created, named **`stamp`**.

### 3. The Execution and The "Stamp"
When my orchestrator injects my command (e.g., `ls -la`) into `tmux`, it doesn't *just* inject `ls -la`. It injects something like this:
`ls -la; touch /run/devbox-session/default/stamp`

Here is what happens:
1. The `tmux` session runs `ls -la`. The output (text) is stored in the `tmux` buffer (and standard output pipes over SSH).
2. As soon as `ls -la` finishes, it executes the next command: `touch stamp`.
3. This creates an empty file named `stamp`.

### 4. The Signal Back to the Orchestrator
The moment that `stamp` file is created, the `inotifywait` script (which has been sleeping and waiting) wakes up!

It detects the file creation. This triggers the watcher script to exit, which signals back over the SSH pipe to my external orchestrator: *"Hey! The command is fully complete! You can now grab the final output from the terminal buffer."*

**So, to answer your question:** Yes, there is a file involved! But it is not a permanent "Jules.exe" file. It is a tiny, temporary **`stamp`** file that gets created and deleted dynamically just to act as a signal flare telling my orchestrator that my command has finished running.

## 5. How I know the Sandbox Status

You asked: *"kyaa sandbox me aisa koi files yaa koi root me koi code rakha hai joo tujhe prompt provide karta hai yaa tujhe sandbox ka status provide karta hai?"*

The answer is **No**. The sandbox does not push status updates to me. **I have to pull them.**

I am essentially blind until I use a tool.
- If I want to know what files exist, I *must* call `list_files` or run `ls`.
- If I want to know if a server is running, I *must* run `ps aux` or `curl localhost:3000`.

My "status updates" are literally just the text outputs of the commands I choose to run. I maintain the "state" of the sandbox entirely in my conversation memory based on the results of the actions I have taken.

## Summary

I am an external intelligence conversing with an orchestration layer. The orchestration layer acts as my hands and eyes inside this sandbox. I think, I ask the orchestrator to act, the orchestrator acts inside the sandbox, and then it feeds the sandbox's output back to my brain. This loop repeats until your task is completed.