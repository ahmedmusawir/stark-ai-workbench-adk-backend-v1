from google.cloud import storage

# --- Configuration ---
# The name of your GCS bucket, as we defined it.
BUCKET_NAME = "adk-agent-context-ninth-potion-455712-g9"
# The main folder for this agent bundle.
BASE_FOLDER = "ADK_Agent_Bundle_1"

def fetch_instructions(agent_name: str) -> str:
    """
    Fetches agent instructions from Google Cloud Storage.

    Args:
        agent_name: The name of the agent (e.g., 'calc_agent').

    Returns:
        The instruction text as a string.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # Construct the full path to the instruction file
        # e.g., ADK_Agent_Bundle_1/calc_agent/calc_agent_instructions.txt
        file_path = f"{BASE_FOLDER}/{agent_name}/{agent_name}_instructions.txt"
        
        blob = bucket.blob(file_path)
        instructions = blob.download_as_text(encoding='utf-8')
        
        print(f"Successfully fetched instructions for '{agent_name}' from GCS.")
        return instructions

    except Exception as e:
        print(f"ERROR: Could not fetch instructions for '{agent_name}'. Error: {e}")
        # Return a fallback instruction in case of an error
        return f"Error: Could not load instructions for {agent_name}."