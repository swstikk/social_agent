# COMMANDER'S TASK LIST (Demo Project)

As the Commander AI, it is your responsibility to guide the Worker AI to complete the following project sequentially.

**Do not write this code yourself.** You must use the `jules_commander.py` CLI tool to assign these tasks one by one, review the Worker's proposed plans using the `status` command, and then `approve` them.

## The Project: Basic Express.js API

The goal is for the Worker AI to build a simple, containerized Node.js backend API with two basic endpoints.

### Task 1: Project Initialization & Express Server Setup
- [ ] Instruct the Worker to create a new directory (e.g., `express-api`).
- [ ] Instruct the Worker to run `npm init -y` inside that directory.
- [ ] Instruct the Worker to install `express` and `cors`.
- [ ] Have the Worker create an `index.js` file with a basic Express server listening on port 3000.
- [ ] The server must include a basic `GET /health` endpoint that returns `{"status": "healthy"}`.

*Commander Note:* Once the Worker provides a plan for Task 1, review it carefully. Ensure it includes both `express` and `cors`. If it does, run `jules_commander.py approve <SESSION_ID>`.

### Task 2: Implement a Data Endpoint
- [ ] Instruct the Worker to add a new `GET /api/users` endpoint to the `index.js` file.
- [ ] This endpoint should return a hardcoded JSON array of three mock user objects (e.g., `[{ id: 1, name: "Alice" }, ...]`).
- [ ] Have the Worker verify the endpoint works by using `curl` locally in its own bash environment.

*Commander Note:* If the Worker forgets to test the endpoint with `curl` in its plan, send a message rejecting the plan and instructing it to add the `curl` test before you approve.

### Task 3: Containerization (Dockerfile)
- [ ] Instruct the Worker to create a `Dockerfile` for the Express API.
- [ ] Ensure the Worker uses an official, lightweight Node.js base image (e.g., `node:18-alpine`).
- [ ] The `Dockerfile` should install dependencies, copy the source code, expose port 3000, and define the start command.

*Commander Note:* After the Worker finishes writing the `Dockerfile`, check its status. If successful, congratulate the Worker using the `message` command.

### Final Step: Report to Client
- [ ] Once all tasks are checked off, send a final message to the Client (the human user in your chat interface) summarizing what the Worker accomplished.