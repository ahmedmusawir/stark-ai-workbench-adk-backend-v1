# ADK 2.7.1 ↔ Hermes A2A — Proven Local POC Setup

**Status:** WORKING POC  
**Environment:** Zorin OS  
**ADK:** 2.7.1  
**Hermes:** Stock Hermes Agent  
**Protocol:** A2A v1.0 / JSON-RPC  
**Hermes A2A Port:** 9900  
**Topology:** Localhost only

---

## 1. Final Working Architecture

```text
Browser
  │
  ▼
ADK Dev UI
http://127.0.0.1:8000
  │
  ▼
ADK RemoteA2aAgent
hermes_agent
  │
  │ A2A + Bearer Token
  ▼
Hermes Gateway
http://127.0.0.1:9900
  │
  ▼
Hermes Agent
default profile
  │
  ▼
Configured Model Provider
```

The interactive Hermes CLI does **not** need to remain running.

The Hermes Gateway is the process serving the inbound A2A endpoint.

---

# 2. Upgrade ADK

Original starter-kit version:

```text
google-adk==1.13.0
```

Upgrade:

```bash
pip install --upgrade google-adk
```

Verified version:

```text
google-adk==2.7.1
```

Existing starter-kit agents were tested after the upgrade and continued working.

---

# 3. Install ADK A2A Support

`RemoteA2aAgent` exists in ADK, but the A2A SDK is an optional dependency.

Install it while keeping ADK pinned:

```bash
pip install "google-adk[a2a]==2.7.1"
```

Verify:

```bash
python -c "from google.adk.agents.remote_a2a_agent import RemoteA2aAgent; print('A2A OK')"
```

Expected:

```text
A2A OK
```

---

# 4. Enter the Hermes Environment

Hermes was installed at:

```text
~/.hermes/hermes-agent
```

Open a normal terminal:

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
```

Verify:

```bash
which hermes
```

Expected:

```text
/home/moose/.hermes/hermes-agent/venv/bin/hermes
```

---

# 5. Configure Hermes A2A

Run:

```bash
hermes gateway setup
```

Select:

```text
A2A
```

Use:

```text
Inbound A2A port: 9900
Agent name: ADK Hermes
```

For the local POC, a peer credential was created:

```text
adk:stark-test-001
```

Meaning:

```text
Peer identity: adk
Bearer token:  stark-test-001
```

No shared bearer token was configured.

No remote bind host was configured.

The POC therefore remains local to the Zorin machine.

---

# 6. Hermes Setup Quirk Discovered

During setup, pressing Enter on:

```text
Inbound A2A port (default 9900):
```

caused Hermes to conceptually use its default port, but it did **not** persist:

```text
A2A_PORT=9900
```

The A2A setup menu therefore continued reporting:

```text
A2A (not configured)
```

Inspection of:

```text
plugins/platforms/a2a/__init__.py
```

showed that Hermes considers A2A connected when either its plugin config is explicitly enabled or the `A2A_PORT` environment variable exists.

The local POC was corrected with:

```bash
echo 'A2A_PORT=9900' >> ~/.hermes/.env
```

Final verified values:

```text
A2A_AGENT_NAME="ADK Hermes"
A2A_PEER_TOKENS=adk:stark-test-001
A2A_PORT=9900
```

For future installations, explicitly enter:

```text
9900
```

rather than leaving the port prompt blank.

---

# 7. Start the Hermes A2A Service

From the activated Hermes environment:

```bash
hermes gateway run
```

Leave this process running.

The interactive Hermes CLI does **not** need to be running.

---

# 8. Verify the Hermes Agent Card

From another terminal:

```bash
curl http://127.0.0.1:9900/.well-known/agent-card.json
```

The successful POC returned an Agent Card containing, among other fields:

```text
name: ADK Hermes
url: http://127.0.0.1:9900/
protocolBinding: JSONRPC
protocolVersion: 1.0
streaming: true
```

The card also advertised Hermes toolsets/capabilities.

At this point:

```text
Hermes A2A Server = VERIFIED
```

---

# 9. Create the ADK Remote Hermes Agent

Add:

```text
hermes_agent/
├── __init__.py
└── agent.py
```

## `hermes_agent/__init__.py`

```python
from . import agent
```

## `hermes_agent/agent.py`

```python
import httpx

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent


root_agent = RemoteA2aAgent(
    name="hermes_agent",
    description="Local Hermes Agent connected through A2A.",
    agent_card="http://127.0.0.1:9900/.well-known/agent-card.json",
    httpx_client=httpx.AsyncClient(
        headers={
            "Authorization": "Bearer stark-test-001",
        }
    ),
)
```

**POC note:** The bearer token is hardcoded only for this local experiment.

Do **not** keep credentials in source code for deployment.

---

# 10. Start ADK

From the ADK project virtual environment:

```bash
adk web
```

Open the ADK Dev UI and select:

```text
hermes_agent
```

---

# 11. Proof Test

Send:

```text
hello?
```

Then:

```text
what is your name?
```

Observed response:

```text
I'm Hermes Agent, an AI assistant built by Nous Research.
I'm running under the default profile on this machine.
```

This proved the complete request path:

```text
ADK Dev UI
   ↓
RemoteA2aAgent
   ↓
A2A
   ↓
Hermes Gateway
   ↓
Hermes Agent
   ↓
response
   ↓
ADK Dev UI
```

---

# 12. POC Verdict

## PASS

The experiment proved:

- ADK 2.7.1 can consume a Hermes Agent through A2A.
- Hermes exposes a valid A2A Agent Card.
- Bearer-authenticated ADK requests reach Hermes.
- Hermes responds through its normal agent runtime.
- The response successfully returns into ADK Dev UI.
- The interactive Hermes CLI is not required during A2A operation.
- The Hermes Gateway is the service boundary ADK depends on.

---

# 13. Production Changes Required

The local POC configuration is **not** a production configuration.

Before deployment:

- Remove the bearer token from Python source.
- Generate a strong random peer credential.
- Store the credential in a secret manager.
- Terminate traffic with HTTPS/TLS.
- Do not expose raw port 9900 directly to the public Internet.
- Restrict authenticated peer identities.
- Apply network/firewall restrictions.
- Limit advertised Hermes toolsets.
- Preserve Hermes state on persistent storage.
- Add gateway health monitoring.
- Add A2A audit-log collection.
- Add rate limits and resource limits.
- Run regression tests against ADK after every deployment change.

---

# Known-Good Local Commands

## Hermes

```bash
cd ~/.hermes/hermes-agent
source venv/bin/activate
hermes gateway run
```

## Verify Hermes

```bash
curl http://127.0.0.1:9900/.well-known/agent-card.json
```

## ADK

```bash
cd ~/python/adk-2.x-and-harmes-v1
source .venv/bin/activate
adk web
```

---

**Baseline rule:** preserve this working configuration before experimenting with ADK graphs, multiple Hermes agents/profiles, cloud deployment, or expanded A2A orchestration.