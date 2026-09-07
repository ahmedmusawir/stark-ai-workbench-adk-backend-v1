import os

import httpx

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent


root_agent = RemoteA2aAgent(
    name="architect_agent",
    description="Stark Architect worker connected through Hermes A2A.",
    agent_card="http://127.0.0.1:9901/.well-known/agent-card.json",
    httpx_client=httpx.AsyncClient(
        timeout=httpx.Timeout(120.0),
        headers={
            "Authorization": f"Bearer {os.environ['HERMES_A2A_TOKEN']}",
        }
    ),
)