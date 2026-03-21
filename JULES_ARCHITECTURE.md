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

## 4. How I know the Sandbox Status

You asked: *"kyaa sandbox me aisa koi files yaa koi root me koi code rakha hai joo tujhe prompt provide karta hai yaa tujhe sandbox ka status provide karta hai?"*

The answer is **No**. The sandbox does not push status updates to me. **I have to pull them.**

I am essentially blind until I use a tool.
- If I want to know what files exist, I *must* call `list_files` or run `ls`.
- If I want to know if a server is running, I *must* run `ps aux` or `curl localhost:3000`.

My "status updates" are literally just the text outputs of the commands I choose to run. I maintain the "state" of the sandbox entirely in my conversation memory based on the results of the actions I have taken.

## Summary

I am an external intelligence conversing with an orchestration layer. The orchestration layer acts as my hands and eyes inside this sandbox. I think, I ask the orchestrator to act, the orchestrator acts inside the sandbox, and then it feeds the sandbox's output back to my brain. This loop repeats until your task is completed.