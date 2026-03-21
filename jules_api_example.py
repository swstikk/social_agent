import requests
import json
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
    """Lists available sources connected to Jules."""
    url = f"{BASE_URL}/sources"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("--- Available Sources ---")
        sources = response.json()
        print(json.dumps(sources, indent=2))
        return sources
    except requests.exceptions.RequestException as e:
        print(f"Failed to list sources: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def create_session(source_name, prompt):
    """Creates a new Jules session."""
    url = f"{BASE_URL}/sessions"
    payload = {
        "prompt": prompt,
        "sourceContext": {
            "source": source_name,
            # Adjust githubRepoContext as needed for your specific repo/branch
            "githubRepoContext": {
                "startingBranch": "main"
            }
        },
        "title": "API Created Session"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"\n--- Created Session for prompt: '{prompt}' ---")
        session = response.json()
        print(json.dumps(session, indent=2))
        return session
    except requests.exceptions.RequestException as e:
        print(f"Failed to create session: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        return None

if __name__ == "__main__":
    # 1. List sources to find the name
    sources_data = list_sources()

    # 2. If a source exists, create a session using the first one
    if sources_data and 'sources' in sources_data and len(sources_data['sources']) > 0:
        first_source_name = sources_data['sources'][0]['name']

        # Example prompt
        prompt = "Explain how this repository is structured."
        create_session(first_source_name, prompt)
    else:
        print("\nNo sources found or failed to fetch sources. Make sure you have connected a source (like GitHub) to Jules in the web app.")
