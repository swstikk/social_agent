import requests
import json
import time
import os

# DO NOT HARDCODE YOUR API KEY
# Set the environment variable JULES_API_KEY before running this script
# Example: export JULES_API_KEY="your_api_key_here"
API_KEY = os.environ.get("JULES_API_KEY")

if not API_KEY:
    raise ValueError("JULES_API_KEY environment variable is not set. Please set it before running the script.")

BASE_URL = "https://jules.googleapis.com/v1alpha"

headers = {
    "X-Goog-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

def list_sources():
    """1. List sources: Gets available sources (like your connected GitHub repo) to work with."""
    url = f"{BASE_URL}/sources"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sources = response.json()
        print("\n[1] --- Available Sources ---")
        print(json.dumps(sources, indent=2))
        return sources
    except requests.exceptions.RequestException as e:
        print(f"Failed to list sources: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def create_session(source_name, prompt):
    """2. Create session: Starts a new work session with a prompt and a source."""
    url = f"{BASE_URL}/sessions"
    payload = {
        "prompt": prompt,
        "sourceContext": {
            "source": source_name,
            "githubRepoContext": {
                "startingBranch": "main"
            }
        },
        "title": "Pipeline Test Session",
        "requirePlanApproval": True # Setting this to true so we can test the approve plan feature
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        session = response.json()
        print(f"\n[2] --- Created Session ---")
        print(json.dumps(session, indent=2))
        return session
    except requests.exceptions.RequestException as e:
        print(f"Failed to create session: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def list_sessions():
    """3. List sessions: Gets a list of your recent sessions."""
    url = f"{BASE_URL}/sessions?pageSize=5"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sessions = response.json()
        print("\n[3] --- Recent Sessions ---")
        print(json.dumps(sessions, indent=2))
        return sessions
    except requests.exceptions.RequestException as e:
        print(f"Failed to list sessions: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def list_activities(session_name):
    """4. List activities: Checks the progress, plan, and messages within a session."""
    # Note: session_name includes 'sessions/' prefix, e.g., 'sessions/123'
    url = f"{BASE_URL}/{session_name}/activities?pageSize=10"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        activities = response.json()
        print(f"\n[4] --- Activities for {session_name} ---")
        print(json.dumps(activities, indent=2))
        return activities
    except requests.exceptions.RequestException as e:
        print(f"Failed to list activities: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def approve_plan(session_name):
    """5. Approve plan: Approves the agent's proposed plan if the session requires explicit approval."""
    url = f"{BASE_URL}/{session_name}:approvePlan"
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        print(f"\n[5] --- Plan Approved for {session_name} ---")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to approve plan: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def send_message(session_name, message):
    """6. Send message: Sends a prompt/message to the agent within an active session."""
    url = f"{BASE_URL}/{session_name}:sendMessage"
    payload = {
        "prompt": message
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"\n[6] --- Sent message to {session_name} ---")
        print(f"Message: '{message}'")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    print("Starting API Pipeline Test...")

    # 1. List Sources
    sources_data = list_sources()

    if sources_data and 'sources' in sources_data and len(sources_data['sources']) > 0:
        first_source_name = sources_data['sources'][0]['name']

        # 2. Create Session
        initial_prompt = "Can you create a simple README file for this repository?"
        session_data = create_session(first_source_name, initial_prompt)

        if session_data and 'name' in session_data:
            session_name = session_data['name']

            # 3. List Sessions (just to test the endpoint)
            list_sessions()

            # Wait a moment for the agent to generate a plan
            print("\nWaiting for 5 seconds to let the agent generate a plan...")
            time.sleep(5)

            # 4. List Activities (to see the generated plan)
            list_activities(session_name)

            # 5. Approve Plan
            # Note: This will only work if a plan was actually generated and requires approval.
            approve_plan(session_name)

            # Wait a moment for agent to start working
            print("\nWaiting for 5 seconds before sending a message...")
            time.sleep(5)

            # 6. Send Message
            send_message(session_name, "Actually, please make sure the README mentions it's a test.")

            # Final check of activities to see our message
            print("\nChecking final activities...")
            list_activities(session_name)

    else:
        print("\nPipeline stopped: No sources found to create a session.")
