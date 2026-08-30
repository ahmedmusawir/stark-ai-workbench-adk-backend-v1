import httpx

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent


root_agent = RemoteA2aAgent(
    name="devops_agent",
    description="Local Hermes Agent connected through A2A.",
    agent_card="http://127.0.0.1:9903/.well-known/agent-card.json",
    httpx_client=httpx.AsyncClient(
        headers={
            "Authorization": "Bearer stark-test-001",
        }
    ),
)