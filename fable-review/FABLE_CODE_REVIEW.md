# FABLE CODE REVIEW
## Stark AI Workbench ADK Backend

Reviewer: Claude Fable 5.1 · Date: 2026-09-13 · Branch: `fable-code-review-13sep2026` · Source SHA: `1eb7d88730447cc10d950817d24e8324429926cf`

---

### 1. Executive Assessment

**Review mode: source + controlled execution, partially integration-assisted (local HTTP boundary only).** The stock ADK `api_server` was started on loopback with a temporary SQLite session store and probed with real HTTP requests (E3 for the API boundary). No deployment-representative evidence exists in the repository, so nothing here is E4.

**Downstream systems:**

| System | Status during review |
| --- | --- |
| ADK 2.7.1 api_server (the only HTTP surface) | REAL, run locally |
| Hermes A2A gateways 127.0.0.1:9900–9903 | UNAVAILABLE (not on host); behaviour from source + committed session artifacts + prior recon doc |
| Vertex AI / Gemini | UNAVAILABLE (no credentials); not contacted |
| GCS bucket `adk-agent-context-ninth-potion-455712-g9` | UNAVAILABLE; offline client-encoding check only |
| Cloud Run / IAM / Secret Manager | UNKNOWN — no deploy artifacts in repo |
| Next.js frontend | read-only source look at sibling checkout (outside review scope; used only to answer "who enforces ownership") |

**What this backend actually is.** It is not a bespoke service. It is six ADK agent packages served by Google's stock `adk api_server`/`adk web`. Four packages are `RemoteA2aAgent` shells that forward the conversation to Hermes profiles over A2A with a shared bearer token; two are Gemini `LlmAgent`s whose system prompts are pulled from a GCS bucket on every model call. There is no authentication, no authorization, no request validation, no CORS policy, and no deployment configuration authored in this repo — every one of those properties is whatever ADK 2.7.1 ships, and ADK's own `--help` states the server "endpoints are unauthenticated. Run it on a trusted network only".

**Headline conclusions.**

1. **Identity is entirely caller-asserted.** `user_id` and `session_id` are URL/body parameters. Any network peer that can reach the port can create, read, list, run against, and delete any user's session (observed locally, F-01). The only known upstream (the Next.js proxy) forwards the browser-supplied `user_id` unchanged, so no layer in the observed system binds a session to an authenticated principal. Whether this is a P0 depends solely on network exposure, which the repo does not pin down: the default bind is 127.0.0.1, but `start_server.sh` binds `0.0.0.0`.
2. **The backend authenticates itself to Hermes, never the end user.** All users share one peer identity (`adk`). Hermes cannot distinguish tenants, and per the prior recon's live card the Hermes profiles advertise file, shell/code-execution, browser and computer-use toolsets. Any user of the ADK port therefore reaches those tools with the same authority (F-09, conditional on Hermes-side tool configuration).
3. **Real conversation transcripts are committed to git** in six `.adk/session.db` files, and the P1 hardening commit left the hermes shell's bearer token hardcoded (F-02, F-03).
4. **The A2A path has not demonstrably delivered a persisted reply.** Every remote turn recorded in the committed databases is a content-less `TASK_STATE_SUBMITTED` acknowledgement; no Hermes text exists in any ADK session (F-04). Combined with a 5 s default timeout on the hermes shell and history re-send on the next turn, timeouts can re-deliver prompts to a tool-capable agent (F-05).
5. **Cost telemetry is silently dead** for both live Gemini agents because `gemini-3.7-flash` is not in the pricing table (F-07).
6. The verification baseline is green (30/30 unit) but covers none of the boundaries above (F-11).

No finding requires exploiting anything; every claim below is either directly observed on loopback with throwaway data, read from source, or read from committed artifacts.

---

### 2. Snapshot and Review Boundary

- Repository `stark-ai-workbench-adk-backend-v1`, branch `fable-code-review-13sep2026`, HEAD = pinned `1eb7d88…`, clean tree at start; `main` and `origin/main` also at the pinned SHA.
- Reviewed: every tracked `.py`, `.sh`, `.ini`, `.json`, `.env_example`, `.gcloudignore`, `requirements*.txt`, the A2A/POC docs, changelog, recon report, ADK 2.7.1 and a2a-sdk 1.1.2 installed sources, six committed SQLite session DBs (read-only).
- Created: `fable-review/{FABLE_REVIEW_PROMPT.md, FABLE_CODE_REVIEW.md, RUN_NOTES.md}` only.
- Not modified: any source, test, dependency, config, env file, git ref, or external system. Byproducts of verification (`__pycache__/`, empty `logs/receipts/`) were removed; details in RUN_NOTES.
- Hermes, Vertex, GCS, Cloud Run were not contacted.

---

### 3. Architecture and Trust Map

**Request path**

```
caller (browser via Next.js route handler, curl, anything on the network)
  │  HTTP, no credential checked
  ▼
ADK api_server (google/adk/cli/api_server.py)            ← stock; Origin-check middleware only
  │  app_name = directory name under repo root (allow-list by filesystem)
  │  user_id, session_id = caller-supplied path/body strings
  ▼
Runner + session service
  │  default: <agent_dir>/.adk/session.db (SQLite)   |   start_server.sh: Supabase/Postgres URI
  ▼
root_agent
  ├── RemoteA2aAgent (hermes/architect/designer/devops)
  │     │  resolves agent card from hardcoded 127.0.0.1:990x URL (lazy, first run)
  │     │  Authorization: Bearer <shared token>  → peer identity "adk"
  │     │  forwards ALL user-authored parts since last remote reply (+ a2a:context_id)
  │     ▼
  │   Hermes gateway (external, not in repo) → Hermes profile → its own model + tools
  │
  └── LlmAgent (jarvis / rico)
        │  instruction = GCS object text fetched on every model call (sync)
        │  tools: google_search (jarvis) | fetch_context(file_name) → GCS read (rico)
        ▼
      Vertex AI Gemini (ADC / service account)
  │
  ▼
events → appended to session (non-partial only) → returned to caller as JSON list / SSE
```

**Authority path**

```
user            : asserted by caller string; never authenticated; never bound to a principal
session         : keyed (app_name, user_id, session_id); caller may choose the id (fixation possible)
agent           : caller picks any directory name; shells are static, endpoints hardcoded (good)
context         : session events (caller-writable via /run, session-create `events`, `state_delta`)
                  + GCS instruction object (writable by whoever has bucket write; frontend Mission Control does)
authority       : - Gemini agents: read-only GCS prefix + Google Search grounding
                  - Hermes agents: whatever the Hermes profile's toolset allows, exercised under ONE shared
                    peer identity regardless of which end user is talking
```

---

### 4. External Integration Map

| Integration | Where | Classification | Notes |
| --- | --- | --- | --- |
| ADK api_server routes | ADK package | LOCAL / REAL | exercised on loopback |
| SQLite `.adk/session.db` | ADK default local storage | LOCAL (committed copies in repo) | writes into agent folders |
| Supabase/Postgres sessions | `start_server.sh` `SUPABASE_DB_URI` | CONFIGURED BUT UNVERIFIED (variable absent from `.env_example`; recon says absent from `.env`) | script cannot run as-is |
| Hermes A2A :9900 (default profile) | `hermes_agent/agent.py` | CONFIGURED BUT UNVERIFIED; recon (2026-08-29) observed it **stopped** | hardcoded token |
| Hermes A2A :9901–9903 | three shells | CONFIGURED BUT UNVERIFIED | token from env |
| Vertex AI Gemini `gemini-3.7-flash` | jarvis, rico | REAL EXTERNAL SERVICE, unverified here | ADC |
| Vertex `count_tokens` | `utils/token_calculator.py` | REAL EXTERNAL SERVICE, unverified here | 2 calls per turn |
| GCS bucket (hardcoded) | `utils/gcs_utils.py`, `utils/context_utils.py` | REAL EXTERNAL SERVICE, unverified here | read-only usage |
| Google Search grounding | jarvis | REAL EXTERNAL SERVICE | built-in tool |
| Cloud Run / Secret Manager / IAM | `grant_permissions.sh`, `store_secrets.sh`, docs | UNKNOWN — no Dockerfile/deploy.sh in repo | docs describe ancestor repo |
| Next.js frontend | sibling repo | outside scope; read-only look | forwards caller `user_id` |

---

### 5. Verification Baseline

| Gate | Result |
| --- | --- |
| Dependency install (`requirements.txt`, clean venv) | OK, `pip check` clean |
| `pytest -m unit` | 30 passed / 0 failed / 11 integration deselected |
| Integration tests | not run (Vertex credentials, cost) |
| Lint / type | none configured in repo |
| `py_compile` all modules | OK |
| Agent import | 3/6 import without env; 3/6 `KeyError: HERMES_A2A_TOKEN` when unset |
| `adk api_server` startup | OK, 16 routes |
| Startup config validation | none: misconfiguration surfaces per request as HTTP 500 |

A green unit suite here proves the receipt/eval helpers work in isolation. It proves nothing about routes, identity, sessions, A2A, or tools (section 16).

---

### 6. API / Identity / Authorization Assessment

**Routes (observed via `/openapi.json`):** `/health`, `/version`, `/list-apps`, `/apps/{app}/app-info`, `/apps/{app}/users/{user_id}/sessions[/{session_id}]` (GET/POST/DELETE/PATCH), `/apps/{app}/users/{user_id}/sessions/{session_id}/artifacts…`, `/apps/{app}/users/{user_id}/memory`, `/run`, `/run_sse`, `/run_live` (websocket), `/agent-identity/finalize`.

For every route:

- **Who can call it?** Anyone who can open a TCP connection to the bind address. Observed: all probes succeeded with no header of any kind.
- **How is caller identity established?** It is not. `user_id` is a path/body string.
- **Where is authentication enforced?** Nowhere in this repo; ADK ships none. The only gate is ADK's `_OriginCheckMiddleware`, which rejects requests carrying a non-allowed browser `Origin` header (observed 403) and guards DNS rebinding on loopback binds. Non-browser callers send no Origin and pass.
- **Where is authorization enforced?** Nowhere. The session key includes `user_id`, so a request must *name* the right user, but the caller names it.
- **Caller-controlled identifiers:** `app_name`, `user_id`, `session_id` (including choosing the id on create — fixation), `state`/`state_delta` (arbitrary session state), `events` on session create (arbitrary history injection), `new_message`.
- **Downstream authority exercised:** Gemini under the server's ADC/service account; GCS reads under the same; Hermes tools under the shared peer token.
- **Can a caller select another user/session?** Yes (observed). **Another agent?** Only among the six directories (unknown → 404). **Another tool?** No, tools are static per agent. **Another backend target?** No, agent-card URLs are hardcoded.

The frontend does not compensate: `src/app/api/agent/run/route.ts` forwards `body.user_id` from the browser; the Supabase middleware only refreshes the session and does not bind identity to the proxied request. This is outside the repo and outside the change boundary, but it means the ownership question ("which service enforces it?") currently has the answer **none**.

---

### 7. Agent Routing / A2A Assessment

**Routing (positive).** `app_name` must match a top-level directory that exports `root_agent`; unknown names 404. Endpoints are static in source. The card fetched from Hermes is validated by ADK: every RPC URL must be https or a loopback host and share the origin the card was fetched from (`remote_a2a_agent.py:506-550`). A compromised or misconfigured Hermes card cannot redirect ADK to another host.

**Identity across the boundary.** The A2A request carries the user's text parts (marked `is_user_input`), a fresh `message_id`, and the `context_id` from the last remote response. It carries **no** end-user identifier and no ADK `user_id`/`session_id`. Authentication is a static bearer token identical for all users → the backend authenticates *itself*. Hermes sees one peer, `adk`.

**History forwarding.** `_construct_message_parts_from_session` walks events backwards to the last event that carries `a2a:response` metadata and forwards every user-authored (and other-agent) part after it. Error events do **not** count as remote responses. Consequence: after any failed turn, the next turn re-sends the failed prompt together with the new one (F-05).

**Timeouts.** hermes shell: httpx default 5 s connect/read/write (verified); workforce shells: 120 s. ADK's own 600 s default applies only when ADK creates the client, which it does not here. With a2a-sdk 1.x the ADK compat layer does not force `streaming=False`, so the streaming path is used when the card advertises streaming (the recon card did). Read timeouts then apply per SSE chunk gap. On timeout or transport error, ADK yields an `error_message` event, logs it, and **does not cancel the remote task**.

**Response validation.** ADK converts tasks/messages with tolerant converters; unknown shapes yield "Unknown A2A response type" error events; `A2AClientError` becomes an error event. Malformed responses do not crash the server. However, the persisted evidence says the happy path never persisted a reply (F-04).

**Loop limits.** `RunConfig.max_llm_calls = 500` bounds Gemini agents per invocation. Remote shells make exactly one A2A send per turn; no delegation or recursion exists in this repo, so no loop surface today.

**Drift.** `hermes_agent` → :9900 which the recon found stopped; the `HERMES_A2A_TOKEN` hardening skipped this shell. `docs/…POC Setup.md` still shows `from . import agent` while code uses `from .agent import root_agent` (harmless).

---

### 8. Session / Context / Memory Assessment

- **Generation/acceptance:** ids are caller-supplied or server-generated UUIDs; the frontend uses `session-<epoch ms>` (collision-prone only within one user, low risk). Caller-chosen ids are accepted verbatim → session fixation across users is trivial when the port is reachable.
- **Storage:** dev default is per-agent SQLite inside the source tree; six such DBs are committed with real transcripts (F-02). The DBs are cumulative copies of one another (architect/designer/devops contain hermes sessions), confirming copy-paste folder lineage.
- **Ownership binding:** composite key only; no principal.
- **Cross-session context mixing inside a session store:** none found. Each remote turn is scoped by its own `a2a:context_id`. Gemini agents get only their own session history from ADK.
- **Cross-user context via GCS instruction object:** the instruction text is global per agent and mutable at runtime by anyone with bucket write; a change affects every user immediately (F-08). This is by design ("hot reload"), but it is an unrecorded trust contract.
- **State pollution:** `get_start_time_callback` writes `_run_start_time` into session state on every model call; it is persisted as a state delta. Harmless but noisy; and callers may inject arbitrary `state_delta`, which nothing in this repo consumes.
- **Restart behaviour:** SQLite persists; `InMemorySessionService` is used only by `scripts/run_evals.py` (module-level per run — fine).
- **Multi-instance:** per-agent SQLite in the container filesystem cannot be shared across Cloud Run instances; ADK falls back to in-memory when the directory is unwritable. The Supabase path is the only multi-instance option and is currently unrunnable (F-10).

---

### 9. Tool Authority Assessment

| Agent | Tools | Argument control | Side effects | Authority source |
| --- | --- | --- | --- | --- |
| jarvis_agent | `google_search` | model | none (read) | Vertex grounding under server credentials |
| product_agent_rico_1 | `fetch_context(file_name)` | model (from user text) | none (GCS read) | server ADC; scope-bounded to `ADK_Agent_Bundle_1/context_store/` because the client URL-encodes `/` in object names (verified offline) |
| hermes/architect/designer/devops | none locally; **remote** Hermes toolsets | model on Hermes side, fed by our forwarded user text | per recon's live card: file read/write, code execution, browser, computer use, messaging integrations | Hermes host credentials; shared `adk` peer token |

Confused-deputy shape present: `untrusted caller → unauthenticated ADK port → RemoteA2aAgent (shared token) → Hermes profile with powerful tools`. The repo neither restricts which Hermes tools a profile exposes nor conveys who the end user is. Whether this is exploitable today depends entirely on Hermes-side configuration and on network reachability of the ADK port; the repo proves neither. Classified as CONDITIONAL / FUTURE GATE (F-09), not as a current CRITICAL.

Tool output trust: `fetch_context` returns GCS text or an error string straight into the model context. The context store is operator-controlled; fine for now, documented as a trust dependency.

---

### 10. Async / Retry / Timeout / Concurrency Assessment

- **Send twice / client retry:** two concurrent `/run`s on one session both append events; ADK holds a per-process per-session lock only around append, not around the whole invocation. Interleaved histories are possible; no idempotency key is honoured (`invocation_id` is accepted but not deduplicated).
- **Downstream timeout after work done:** ADK yields an error event; Hermes keeps running; no `cancel` RPC. Next user turn re-sends the earlier prompt (see §7) → possible duplicate side effects on Hermes tools (F-05).
- **Client disconnect:** `/run` monitors `http.disconnect` and cancels the local worker (499). The A2A request's httpx stream is closed by cancellation; remote work is not cancelled.
- **Blocking calls in the event loop:** `fetch_instructions` (GCS, sync) runs inside `canonical_instruction` on every model call; `count_tokens` (Vertex, sync, ×2) runs inside `after_model_callback`; `fetch_context` is a sync `FunctionTool` (ADK runs sync tools inline unless a tool thread pool is configured — none is). Under concurrency each request stalls the whole process for the duration of these network calls. Measurable performance defect, not a safety issue.
- **Retries:** none in ADK's A2A client for this version (no retry/backoff code found in a2a-sdk client), none in the repo. The frontend retries once on session-not-found only.
- **Ordering:** events are yielded in order; SSE partials precede the final. No reordering hazard found.

---

### 11. Findings Summary

| ID | Title | Classification | Severity / Risk | Confidence | Evidence | Root Cause | Current vs Conditional |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 | Unauthenticated API with caller-asserted `user_id`/`session_id`; any peer can read/write/delete/run any session | CURRENT SECURITY RISK | HIGH (CRITICAL if port reachable beyond loopback) | HIGH (local defect) / MODERATE (deployed consequence) | E3 | Missing API authorization; caller-controlled identity | Current |
| F-02 | Real conversation transcripts committed in six `.adk/session.db` files | DEFECT / CURRENT PRIVACY RISK | MEDIUM (HIGH if repo public) | HIGH | E1 | Runtime state inside source tree | Current |
| F-03 | Live Hermes bearer token hardcoded in `hermes_agent/agent.py` and POC doc; hardening commit missed it | CURRENT SECURITY RISK | MEDIUM | HIGH | E1 | Config/secret drift | Current |
| F-04 | No Hermes reply is ever persisted in ADK sessions (only `SUBMITTED` acks); history reload cannot show assistant turns | DEFECT | MEDIUM | HIGH (symptom) / LOW (mechanism) | E1 | A2A streaming/finality contract not verified | Current |
| F-05 | 5 s default timeout on hermes shell; timeouts don't cancel remote work; next turn re-sends failed prompt → duplicate delivery to tool-capable agent | CURRENT RELIABILITY RISK / CONDITIONAL | MEDIUM (HIGH if Hermes tools mutate state) | HIGH (local) / MODERATE (consequence) | E1+E2 | Retry/non-idempotency; trust delegated without contract | Current (dup) / Conditional (impact) |
| F-06 | Missing `HERMES_A2A_TOKEN` is a per-request HTTP 500, not a startup failure | DEFECT | LOW | HIGH | E3 | No startup config validation | Current |
| F-07 | Receipt/cost telemetry silently fails for `gemini-3.7-flash` (not in pricing table); no receipts written for either live agent | DEFECT | LOW–MEDIUM | HIGH | E2 | Config drift (model string duplicated, table stale) | Current |
| F-08 | System prompt is a mutable GCS object fetched sync each call; fetch failure substitutes an error string as the instruction and the agent keeps running with tools | CONDITIONAL RISK + DEFECT | MEDIUM | HIGH | E1 | Trust delegated without explicit contract; fail-open | Current |
| F-09 | Shared peer identity to Hermes profiles that advertise file/code/browser tools; backend authenticates itself, not the user | CONDITIONAL RISK / FUTURE GATE | FUTURE GATE (HIGH if exposed) | MODERATE | E1 (+recon card) | Agent/tool authority not scoped per user | Conditional |
| F-10 | Deployment model undefined: no Dockerfile/deploy, per-agent SQLite in source tree, Supabase path unrunnable, `0.0.0.0` bind script, `list-apps` enumerates non-agent dirs, 404 leaks filesystem path | FUTURE GATE + LOW defects | FUTURE GATE | HIGH | E1/E3 | Process-local state; config drift | Conditional |
| F-11 | Tests cover helpers only; zero coverage of routes, identity, sessions, A2A, tools, config failure | VERIFICATION / TOOLING DEFECT | MEDIUM | HIGH | E2 | Test-harness blind spots | Current |
| F-12 | Cross-project documentation residue and stale changelog/audit claims mislead discovery | OPTIONAL IMPROVEMENT | LOW | HIGH | E1 | Config/manifest drift | Current |

---

### 12. Detailed Findings

#### F-01 — Unauthenticated ADK API with caller-asserted user and session identity

- **Classification:** CURRENT SECURITY / RELIABILITY RISK
- **Severity:** HIGH; CRITICAL if the port is reachable by anyone other than the trusted frontend host.
- **Confidence:** HIGH that the local behaviour is as described; MODERATE about deployed impact (exposure unknown).
- **Evidence level:** E3 (real local HTTP dispatch against the real server with a throwaway SQLite store).
- **Locations:** ADK `google/adk/cli/api_server.py` routes `create_session_with_id` (l.1457–1472), `create_session` (l.1474–1500), `list_sessions`/`get_session`/`delete_session` (l.1423–1509), `run_agent` (l.1798); repo `start_server.sh:13-16` (`--host=0.0.0.0`); absence of any wrapper/auth code in the repo.
- **Expected contract / invariant:** a session may be read, mutated, run, or deleted only by the principal that owns it, and `user_id` must derive from an authenticated identity, not from the request.
- **Execution / trust / session path:** `caller → POST /apps/{app}/users/{ANY}/sessions/{ANY} → SQLite row keyed (app, user, session)`; `GET` returns full event history including user prompts and model replies; `POST /run` executes the agent under the server's Google credentials in that session; `DELETE` removes it.
- **Directly observed:** creating `victim-user/fixed-session-1`, listing `victim-user`'s sessions, reading the session, running an agent in it, and deleting it — all HTTP 200 with no credentials. Reading it under a different `user_id` → 404 (the key includes the string, but the string is chosen by the caller).
- **Source inference:** no code in this repository adds middleware, dependencies, or API-key checks; ADK's help text explicitly warns the server is unauthenticated.
- **Downstream-service assumptions:** the sibling frontend's route handler forwards the browser-supplied `user_id` and does not bind it to the Supabase user (outside-repo read). If the frontend is the only path to the port, an *authenticated* frontend user can still address other users' sessions by editing the request body.
- **Deployment assumptions:** default bind 127.0.0.1 is safe-by-default; `start_server.sh` and any Cloud Run deployment change that. Cloud Run ingress/IAM are not represented in the repo.
- **User / system impact:** cross-user transcript disclosure, session tampering (inject `events`/`state` into another user's session before their next turn), deletion, and use of the server's Gemini/GCS/Hermes authority by anyone reaching the port.
- **Tool / authority impact:** see F-09 — the run endpoint is the door to Hermes tools.
- **Agentic answers:** crosses users: **yes**; crosses sessions: **yes**; selects another agent: only among the six; changes tool authority: indirectly (any caller reaches any agent); retry duplicates side effects: see F-05; authenticates user or itself: **itself only**; who enforces ownership: **no service does today**.
- **Falsifier / downgrade evidence:** (a) proof that every deployment binds loopback and only a same-host proxy that rewrites `user_id` from a verified session can reach it → downgrade to FUTURE GATE; (b) a Cloud Run config with ingress=internal + `run.invoker` restricted to the frontend's service account **and** frontend binding of `user_id` → downgrade to MEDIUM (defence-in-depth gap). Neither exists in the repo.
- **Root-cause group:** RC-1 Missing API authorization / caller-controlled identity.

#### F-02 — Real transcripts committed in `.adk/session.db`

- **Classification:** DEFECT / CURRENT PRIVACY RISK · **Severity:** MEDIUM (HIGH if the GitHub repo is public — visibility could not be checked, `gh` absent) · **Confidence:** HIGH · **Evidence:** E1 (artifact inspected read-only).
- **Locations:** `architect_agent/.adk/session.db`, `designer_agent/.adk/session.db`, `devops_agent/.adk/session.db`, `hermes_agent/.adk/session.db`, `jarvis_agent/.adk/session.db`, `product_agent_rico_1/.adk/session.db` (all in `git ls-files`, added in `4964d49`); `.gitignore` ignores `adk_sessions.db` but not `**/.adk/`.
- **Invariant:** runtime conversation state never enters version control.
- **Observed:** 22 sessions / 86 events across the six files; user prompts and full model answers for jarvis and rico; a frontend user UUID (`ca62b315-…`) and `session-<epoch>` ids; cumulative copies (the three workforce DBs contain hermes sessions). No credentials found in event JSON.
- **Inference:** ADK's default local storage (`local_storage.py:46-66`) writes here whenever `adk web`/`api_server` runs without `--session_service_uri`; the files will keep changing and dirtying the tree (the recon already saw four modified).
- **Impact:** disclosure of whoever's conversations are captured; noisy binary churn in history; accidental persistence of future sensitive prompts.
- **Falsifier:** repo private and all participants are the operator → practical severity LOW, still a hygiene defect. (Remediation is the Operator's: untrack + ignore `**/.adk/`; history rewrite is a separate decision.)
- **Root-cause group:** RC-4 Runtime/process-local state inside the source tree.

#### F-03 — Hardcoded Hermes bearer token in `hermes_agent/agent.py`

- **Classification:** CURRENT SECURITY RISK · **Severity:** MEDIUM · **Confidence:** HIGH · **Evidence:** E1.
- **Locations:** `hermes_agent/agent.py:12` (`"Authorization": "Bearer stark-test-001"`), `docs/ADK 2.7.1 ↔ Hermes A2A — Proven Local POC Setup.md:146-153,202,288` (documents the same token as the configured peer credential `adk:stark-test-001`); present in both commits `4964d49` and `1eb7d88`.
- **Invariant:** no live credential in source; the P1 commit's own intent ("harden workforce shells") was to move tokens to `HERMES_A2A_TOKEN`.
- **Observed:** three shells were converted; this one was not. The runbook says all profiles keep the same peer token, so this string may be the *same* credential the other shells now read from the environment — in which case the env-var migration is cosmetic until the token is rotated.
- **Deployment assumptions:** the gateway is loopback-only per docs, so the token's blast radius is local today.
- **Falsifier:** the `default` profile's `A2A_PEER_TOKENS` has been rotated/removed and differs from the workforce token → downgrade to LOW (dead credential in history).
- **Root-cause group:** RC-5 Config / secret drift.

#### F-04 — Hermes replies are not persisted in ADK sessions

- **Classification:** DEFECT (reliability / integration) · **Severity:** MEDIUM · **Confidence:** HIGH that the artifacts show it; LOW–MODERATE on mechanism · **Evidence:** E1 (committed DBs) + source reading.
- **Locations:** all four remote shells; ADK `remote_a2a_agent.py:751-880` (`_handle_a2a_response`), `runners.py:1523-1541` (`_should_append_event` — partial events are not appended), `a2a/_compat.py:769-792` (for a2a-sdk 1.x ADK does not set `streaming=False`, so the SDK default `streaming=True` applies when the card advertises streaming).
- **Invariant:** after a successful remote turn, the session contains an agent event with the reply text so that history reload and downstream consumers see it.
- **Observed:** 18 remote-agent events across four shells; 18/18 have no `content` and `a2a:response.status.state == TASK_STATE_SUBMITTED`; 0 contain text. Two additional events are connection errors. By contrast jarvis/rico sessions persist full replies.
- **Inference:** the only persisted item per turn is the initial task acknowledgement; whatever carried the answer (streamed artifact chunks with `last_chunk` false → `partial=True`, or status updates without message) was never a non-partial event. The frontend's `/run` path may still display text because `/run` returns partial events too, but `getHistory` (reads persisted session) will show no assistant turns for these agents. The POC doc's "observed response" was via the Dev UI's live stream, which is consistent with this.
- **Downstream-service assumptions:** Hermes's A2A finality semantics (does it emit a COMPLETED status with message, or artifacts with `last_chunk`?) — not verifiable here.
- **Impact:** lost conversation history for the entire Hermes workforce path; misleading "success" persisted as an empty acknowledgement; receipts/evals impossible for these agents.
- **Falsifier:** one live capture of a remote turn whose persisted session event carries text and a COMPLETED state → withdraw. If the Dev UI shows answers but history never does → confirm.
- **Root-cause group:** RC-3 Trust/contract delegated to A2A peer without explicit, tested contract.

#### F-05 — Timeout without cancellation plus history re-send can duplicate prompts to a tool-capable agent

- **Classification:** CURRENT RELIABILITY RISK; consequence CONDITIONAL · **Severity:** MEDIUM (HIGH if Hermes profiles have mutating tools enabled — the recon card lists `write_file`, code execution, browser) · **Confidence:** HIGH for local mechanics (E2 verified timeout; E1 code path), MODERATE for consequence.
- **Locations:** `hermes_agent/agent.py:10-14` (no `timeout=` → httpx default 5 s, verified), `architect|designer|devops_agent/agent.py:13` (120 s); ADK `remote_a2a_agent.py:678-749` (`_construct_message_parts_from_session` stops only at events carrying `a2a:response`; error events carry `a2a:error` and are skipped), `:1076-1105` (error → event, no cancel), `api_server.py:1830-1860` (client disconnect cancels the local task only).
- **Invariant:** a prompt is delivered to the remote agent at most once; a local timeout either cancels or is reconciled with the remote task.
- **Path:** user turn 1 → A2A send → Hermes starts (possibly runs tools) → ADK read timeout at 5 s/120 s → error event persisted → user turn 2 → ADK rebuilds the message from history: turn-1 text **and** turn-2 text, new `message_id`, same `context_id` → Hermes receives turn 1 again.
- **Observed:** timeouts verified offline; error-event persistence observed in committed DB (connection errors) and locally (dead endpoint). Duplicate delivery itself is source inference (no live Hermes).
- **Downstream assumptions:** Hermes does not deduplicate on content; A2A `message_id` differs per attempt, so protocol-level dedup will not help.
- **Impact:** duplicated side effects on the Hermes host (file writes, commands, messages), duplicated cost; for the hermes shell a 5 s budget makes timeouts the *normal* case for any non-trivial answer.
- **Falsifier:** Hermes gateway shown to reject/ignore a message whose text it already processed in the same context, or evidence that the profiles expose read-only toolsets → downgrade to LOW (wasted tokens only).
- **Root-cause group:** RC-2 Retry / non-idempotency across the A2A boundary.

#### F-06 — Missing `HERMES_A2A_TOKEN` fails per request as HTTP 500

- **Classification:** DEFECT · **Severity:** LOW · **Confidence:** HIGH · **Evidence:** E3.
- **Locations:** `architect_agent/agent.py:15`, `designer_agent/agent.py:15`, `devops_agent/agent.py:15`; ADK loads agents lazily on first request.
- **Observed:** server starts fine; `/list-apps` lists the agents; first `/run` → 500 "Internal Server Error", stack trace only in server log.
- **Impact:** availability/diagnosability: a misconfigured deployment looks healthy (`/health`, `/list-apps` OK) until a user hits a workforce agent. Failing closed is correct; failing *late* is the defect.
- **Positive note:** no fallback token, no `os.getenv(..., "placeholder")` pattern (the scaffold doc's Pattern B recommends exactly that anti-pattern — see F-12).
- **Root-cause group:** RC-5 Config drift / no startup validation.

#### F-07 — Cost telemetry silently disabled for the live model

- **Classification:** DEFECT · **Severity:** LOW–MEDIUM (the receipt/usage system is the kit's stated instrumentation) · **Confidence:** HIGH · **Evidence:** E2.
- **Locations:** `jarvis_agent/agent.py:16,24`, `product_agent_rico_1/agent.py:17,25` (`gemini-3.7-flash`), `utils/token_calculator.py:6-22` (`_PRICING` has only 2.5-flash, 2.5-pro, 2.0-flash), `callbacks/receipt_callback.py:54-67` (broad `except` → print warning).
- **Observed:** `estimate_cost(model="gemini-3.7-flash")` raises `ValueError`; the callback prints `[receipt_callback] Warning: failed to save receipt: Unknown model …` and writes nothing; with `gemini-2.5-flash` it writes a receipt.
- **Also:** `count_tokens` makes two synchronous Vertex calls per model response before the failure point (cost and latency paid, result discarded); the model string is duplicated in each agent file (Agent arg vs callback arg) — a skew risk the recon already flagged.
- **Impact:** `scripts/usage_report.py` reports nothing; evals' cost tracking claims in `docs/EVAL_TESTING_MANUAL.txt` are false for current agents; the warning is a stdout print, easy to miss.
- **Root-cause group:** RC-5 Config drift.

#### F-08 — Mutable remote system prompt with fail-open fallback

- **Classification:** CONDITIONAL RISK + DEFECT · **Severity:** MEDIUM · **Confidence:** HIGH · **Evidence:** E1.
- **Locations:** `utils/gcs_utils.py:9-36` (`fetch_instructions` → on any exception returns `"Error: Could not load instructions for {agent}."`), `jarvis_agent/agent.py:8-10,19`, `product_agent_rico_1/agent.py:11-12,20` (instruction provider called on every model call); ADK `llm_agent.py:699-722` (provider result used verbatim, state injection bypassed — good).
- **Invariant:** the system prompt is trusted configuration; if it cannot be loaded the agent should refuse to run, not run instruction-less with tools attached.
- **Observed/inferred:** on GCS failure the literal error string becomes the system instruction and the run proceeds with `google_search` / `fetch_context` available. Separately, whoever can write `ADK_Agent_Bundle_1/<agent>/<agent>_instructions.txt` controls the behaviour of every user's session instantly; the frontend's Mission Control feature is designed to write it. The sync GCS call also blocks the event loop per model call.
- **Trust answer:** trusted = GCS object (implicitly = anyone with bucket write, incl. the frontend's server credentials); untrusted = user text and Hermes replies. Nothing in this repo records or tests that contract. Rico's key is `"product_agent"` while its folder is `product_agent_rico_1` (documented inconsistency, works only because the object exists under the old name).
- **Falsifier:** bucket IAM shows write limited to the operator and Mission Control is admin-only → keep as documented TRADEOFF; the fail-open fallback remains a defect regardless.
- **Root-cause group:** RC-3 Trust delegated without explicit contract.

#### F-09 — Shared peer identity to tool-capable Hermes profiles

- **Classification:** CONDITIONAL RISK / FUTURE GATE · **Severity:** FUTURE GATE (becomes HIGH/CRITICAL the moment the ADK port is reachable by untrusted users while Hermes tools remain enabled) · **Confidence:** MODERATE (tool inventory comes from the 2026-08-29 recon's live card, not re-observed) · **Evidence:** E1 (repo) + E1 (recon artifact).
- **Locations:** all four `RemoteA2aAgent` shells; `agent_docs/recon/RECON_…2026-08-29.md` §5 and §10.7 (card advertises 33 skills incl. `toolset.file` read/write, code execution, browser, computer use); `docs/…POC Setup.md` §13 ("Limit advertised Hermes toolsets" listed as a required production change, not done in repo).
- **Invariant:** tool authority must be scoped to the principal on whose behalf the request runs, or the caller population must be trusted.
- **Path:** any caller → `/run` → forwarded text (`is_user_input`) → Hermes profile under peer `adk` → Hermes model decides tool calls on its host with its credentials. ADK sends no user identity; Hermes cannot apply per-user policy even if it wanted to.
- **Agentic answers:** crosses users: yes (all users are one peer); changes tool authority: any user reaches the most capable profile; backend authenticates: itself.
- **Falsifier:** Hermes profiles configured read-only / sandboxed, or ADK port only reachable from the trusted frontend host → remains FUTURE GATE with LOW current risk.
- **Root-cause group:** RC-3 Trust delegated without explicit contract; RC-1 caller-controlled identity.

#### F-10 — Deployment readiness gaps and minor exposure defects

- **Classification:** FUTURE GATE + LOW defects · **Confidence:** HIGH · **Evidence:** E1 / E3.
- Items:
  1. No Dockerfile, `deploy.sh`, or Cloud Run config exists despite `docs/REPO_AUDIT_REPORT.md`, `STARTER_KIT_SPEC.md`, `CHANGELOG.md` describing them (they belong to the ancestor repo). Nothing in this repo can be deployed as documented.
  2. `start_server.sh` binds `0.0.0.0:8000` and requires `SUPABASE_DB_URI`, which `.env_example` does not list; `store_secrets.sh` uses substring `grep` for variable names.
  3. Default per-agent SQLite lives in the source tree; on Cloud Run's read-only FS ADK silently falls back to in-memory → sessions vanish per instance/restart (ADK help text). Multi-instance correctness requires the unrunnable Supabase path.
  4. `GET /list-apps` enumerates every top-level directory (`docs`, `tests`, `fable-review`, …) — information disclosure and misleading agent list (observed).
  5. 404 for unknown app leaks the absolute filesystem path (observed).
  6. `.gcloudignore` excludes `*.json`, which would drop `evals/*.json` from a source-based Cloud Build upload (recon noted).
  7. `.env_example` contains partially masked but real-looking GHL token fragments (`pit-1ac05ee8-******-fea882c11721`) — scrub to placeholders.
- **Root-cause group:** RC-4 process-local state; RC-5 config/doc drift.

#### F-11 — Test suite does not touch any dangerous boundary

- **Classification:** VERIFICATION / TOOLING DEFECT · **Severity:** MEDIUM · **Confidence:** HIGH · **Evidence:** E2 (ran suite, read tests).
- **Observed:** 41 tests: token math, receipt dict shape, JSONL append, eval-runner report formatting, callback with `SimpleNamespace` mocks. No test imports an agent, constructs a `RemoteA2aAgent`, starts the api_server, creates a session, exercises `fetch_instructions` failure, or asserts receipt writing for the configured model (F-07 would have been caught by one line: `get_model_pricing("gemini-3.7-flash")`).
- **Can every test pass while…** cross-user session access is possible: **yes**. A timeout duplicates remote work: **yes**. Hermes replies are never persisted: **yes**. Receipts are silently dead: **yes** (tests use `gemini-2.5-flash`).
- 11 integration tests require live Vertex and are not runnable in a clean venv without ADC — the `CLAUDE.md` "pytest must pass in a clean venv" gate can only be met by deselecting them.
- **Root-cause group:** RC-6 Test-harness blind spots.

#### F-12 — Documentation and configuration residue misleads discovery

- **Classification:** OPTIONAL IMPROVEMENT · **Severity:** LOW · **Evidence:** E1.
- `docs/architecture.md`, `decisions.md`, `patterns.md` are for "VidGen — Bibo YouTube Video Generator"; `REPO_AUDIT_REPORT.md` audits another repo/branch; `CHANGELOG.md` references `ghl_mcp_agent`, `Dockerfile`, `utils/context_cache.py` that do not exist at this SHA; `skills/SCAFFOLD_NEW_AGENT.md` recommends `os.getenv("MY_API_KEY", "placeholder")` (a fallback-credential anti-pattern) and lists `ghl_mcp_agent` as a reference; `requirements.txt` freezes ~140 packages, most unused; protocol files mandated by `CLAUDE.md` (`RECOVERY.md`, `agent_docs/SESSIONS/`, `agent_docs/KIP_REGISTRY.md`, `config_service.py`) are absent; `jarvis_agent/agent.py:13` comment says LiteLLM, code uses Gemini directly.
- **Root-cause group:** RC-5 drift.

---

### 13. Root-Cause Themes

| RC | Theme | Findings |
| --- | --- | --- |
| RC-1 | **Missing API authorization / caller-controlled identity** — the repo adds nothing on top of an intentionally unauthenticated dev server, and the only upstream forwards caller identity verbatim | F-01, F-09 |
| RC-2 | **Retry / non-idempotency across A2A** — local timeout ≠ remote cancel; history re-send by design | F-05 |
| RC-3 | **Trust delegated without an explicit, tested contract** — Hermes finality semantics, Hermes tool scope, GCS prompt authority are all assumed | F-04, F-08, F-09 |
| RC-4 | **Process-local runtime state inside the source tree / single instance** | F-02, F-10 |
| RC-5 | **Config / secret / doc drift** — copy-paste shells, stale pricing table, half-finished token migration, ancestor docs | F-03, F-06, F-07, F-10, F-12 |
| RC-6 | **Test-harness blind spots** | F-11 |

Most of the severity in this repo comes from RC-1 and RC-3 together: a door with no lock leading to agents whose authority the repo neither scopes nor conveys per user.

---

### 14. Deployment / Cloud Run Assessment

Repository evidence for deployment is **absent**: no Dockerfile, no `deploy.sh`, no Cloud Run YAML, no CI. Only playbooks (`docs/PYTHON_ADK_PLAYBOOKS/cloud-run-deployment.md`) and IAM/secret helper scripts exist. Therefore:

- Container startup / port binding / health: ADK provides `/health` and honours `--port`; the shell-form `CMD` pattern is documented but not present.
- Statelessness: default local SQLite per agent is process-local; Cloud Run's read-only filesystem triggers ADK's in-memory fallback (per `--use_local_storage` help) → sessions lost across instances/restarts unless `--session_service_uri` points at shared Postgres. That path is unrunnable today (F-10).
- Multiple instances: no shared lock; concurrent runs on one session interleave (§10).
- Request timeout: A2A shells wait up to 120 s (hermes 5 s); frontend budget 90 s total — a Hermes answer longer than ~75 s will be cut by the frontend while ADK and Hermes continue.
- Environment validation: none at startup (F-06).
- Ingress/IAM: `grant_permissions.sh` grants Vertex user, storage **objectViewer** (read-only — good), secret accessor. Nothing constrains who may invoke the service; the playbook itself shows `--allow-unauthenticated`. **Do not deploy this repo publicly without an authorization layer** (F-01).
- Hermes on Cloud Run: shells target `127.0.0.1:990x`; in any non-colocated deployment they are dead pointers by construction.

Verdict: **not deployment-ready; FUTURE GATE items F-01 (auth layer), F-09 (tool/identity scoping), F-10 (state + endpoints + config) must be resolved first.**

---

### 15. Positive Protections to Preserve

Scoped to what was observed or read in source:

- **Agent selection is filesystem-allow-listed** (unknown app → 404, observed); endpoints are hardcoded, never caller-supplied.
- **ADK Origin-check middleware** rejects cross-origin browser requests (403 observed) and includes a DNS-rebinding guard for loopback binds; **default bind is 127.0.0.1**.
- **Agent-card RPC target validation** in `RemoteA2aAgent` (https or loopback; same origin as the card source) prevents a card from redirecting traffic.
- **Credential sanitisation** when forwarding function responses to A2A peers (`_sanitize_user_function_response_event`).
- **No auto-created sessions on `/run`** (`--auto_create_session` off; unknown session → 404).
- **Client disconnect cancels the local worker** (499 path).
- **`max_llm_calls = 500`** bounds Gemini loops per invocation.
- **Fail-closed on missing `HERMES_A2A_TOKEN`** (no fallback credential) — keep, but move the failure to startup (F-06).
- **`fetch_context` cannot escape its GCS prefix** because object names are URL-encoded (verified).
- **`.env` and the service-account JSON are gitignored**; history contains no `.env` or key files (checked with `git log --all --name-only`).
- **Read-only storage IAM** (`roles/storage.objectViewer`) for the service account.
- **500 responses do not leak stack traces** to the client (trace only in server log).
- **Instruction providers bypass ADK state templating**, so caller-controlled session state cannot be injected into the system prompt via `{placeholders}`.
- **Prior recon discipline**: `agent_docs/recon/…` is an honest, evidence-labelled baseline; several of its drifts were fixed in `1eb7d88`.

---

### 16. Test and Verification Quality

- Suite: 41 tests, 30 unit green, 11 integration (live Vertex) not runnable offline.
- Coverage of the boundaries this review cares about:

| Boundary | Covered? |
| --- | --- |
| Route authentication / authorization | No (none exists to test) |
| Agent allow-listing | No |
| User/session ownership | No |
| Malformed requests | No |
| Downstream A2A failure / timeout / retry | No |
| Duplicate execution | No |
| A2A response drift / finality | No |
| Invalid or unavailable agent | No |
| Tool authority / `fetch_context` scope | No |
| Instruction fetch failure behaviour | No |
| Receipt for the *configured* model | No (tests hardcode 2.5-flash) |
| Startup / config failure | No |

- The eval runner (`scripts/run_evals.py`) is a substring grader against live Gemini; useful smoke test, not a boundary test. Its `--agent` flag imports an arbitrary module by name — acceptable for a local CLI.
- Recommendation for the Operator's backlog (not implemented here): a `TestClient` suite against `get_fast_api_app` with a temp SQLite URI would cover routes, session semantics, unknown app, missing token, and could stub `RemoteA2aAgent` to assert history re-send and error-event behaviour; a `respx`-mocked A2A card/task sequence would pin the finality contract (F-04).

---

### 17. Concerns / Tradeoffs / Optional Improvements

- **Tradeoff:** GCS hot-reloaded prompts give instant control at the cost of an implicit authority boundary and a blocking call per turn (F-08). Acceptable for a single-operator POC if documented.
- **Tradeoff:** shared bearer peer identity is the simplest thing that works locally; it is the wrong shape for multi-user (F-09).
- **Optional:** run sync GCS/Vertex calls off the event loop (ADK `ToolThreadPoolConfig`, or async GCS client); cache instructions with a short TTL.
- **Optional:** single source of truth for model name per agent; extend `_PRICING` or make receipts model-agnostic on unknown models (log tokens, cost `None`).
- **Optional:** `list-apps` will keep listing `fable-review/` and `docs/` — consider an `agents/` directory or ADK's single-agent mode when restructuring.
- **Optional:** prune `requirements.txt` to imported packages; retire ancestor/VidGen docs to an `_inherited/` attic.
- **Question (architecture):** is Hermes meant to be co-located with ADK forever (127.0.0.1)? If not, the shells need configurable, https endpoints and per-environment cards.

---

### 18. Under-Reviewed Areas and Limitations

| Area | Depth achieved | Missing evidence | Why missing | Effect on conclusions |
| --- | --- | --- | --- | --- |
| Live Hermes agents / A2A endpoints | Source + committed artifacts + prior recon card | Live task stream, finality events, tool inventory today, dedup behaviour | Not on review host | F-04 mechanism and F-05 impact stay inferential; F-09 tool list is dated 2026-08-29 |
| GCP IAM / Cloud Run ingress | Scripts and playbooks only | Actual service config, ingress, invoker bindings, bind host | No deploy artifacts in repo | F-01 exposure severity unresolved between HIGH and CRITICAL |
| GCS bucket | Offline client-encoding check | Bucket IAM (who can write instructions), object contents | No credentials | F-08 authority scope unverified |
| Vertex AI | Not exercised | Behaviour of `gemini-3.7-flash`, count_tokens latency | No credentials | F-07 is pure logic and unaffected |
| Real tool effects on Hermes host | None | Which toolsets are enabled per profile | External system | F-09 conditional |
| Multi-instance execution | Source only | Supabase-backed run, concurrency test | `.env`/DB absent | §10 concurrency claims are E1 |
| Production authentication | None exists | — | — | F-01 stands as stated |
| Frontend identity binding | Read-only look at sibling repo | Full auth flow, deployment | Out of scope | Used only to answer "who enforces ownership"; not a finding against this repo |
| Repo visibility | Unknown | GitHub visibility | `gh` absent | F-02 severity MEDIUM vs HIGH |

Absent external evidence was treated as neither safe nor vulnerable.

---

### 19. Reviewer Self-Critique

1. **Strongest consequential findings:** F-01 (observed on the real server), F-02 (artifact in hand), F-04 (18/18 artifacts agree). Each rests on direct observation, not inference.
2. **Why they survive challenge:** F-01 — the code adding authorization simply does not exist in this repo, and the vendor documents the server as unauthenticated; the only counter is deployment topology, which the repo does not provide. F-02 — files are in `git ls-files` and contain readable prompts. F-04 — every remote turn persisted is content-less; a single counter-example would be visible in the same DBs and none exists.
3. **Weakest consequential findings:** F-05's *impact* (needs Hermes to actually act on duplicates and to have mutating tools enabled), F-09 (tool inventory is second-hand from the recon), F-08's authority claim (depends on bucket IAM I could not see).
4. **Assumptions making them vulnerable:** Hermes profiles still expose the toolsets seen on 2026-08-29; Hermes does not deduplicate; Mission Control can write the instruction objects in production.
5. **Possibly overstated:** F-01 as HIGH if every real deployment is loopback-only behind a same-host frontend that (in future) binds `user_id`; F-02 if the repo is private and all captured users are the operator.
6. **Possibly understated:** F-09 — if the ADK port is already exposed on a LAN/VPS with `start_server.sh`, the combination F-01 + F-09 is a current CRITICAL (unauthenticated path to code-execution tools). F-04 — if the frontend's `/run` also fails to surface partial events, the workforce path may be non-functional end to end.
7. **Shared root causes:** RC-1 and RC-3 dominate; RC-5 explains most of the smaller defects.
8. **Important under-reviewed areas:** live A2A finality (F-04), Hermes toolsets (F-09), deployment topology (F-01 severity).
9. **Wording that may outrun evidence:** "Hermes cannot distinguish tenants" is inference from the request shape, not from Hermes source; "duplicate delivery" is a code-path reading, not a live capture. Both are labelled as such in the findings.
10. **What another senior reviewer should challenge first:** whether F-04 is an artifact of *how the sessions were captured* (Dev UI + early ADK 2.x) rather than current behaviour — the cheapest test is one live turn and a `GET` of the session. Second, whether the ADK port has ever been bound to anything but loopback.

No finding was withdrawn by the critique; F-05 and F-09 were kept at conditional severities rather than promoted.

---

### 20. Prioritized Handoff (no remediation performed)

**P0 — immediate current risk**
- None *proven* current at CRITICAL: exposure is unknown. If `start_server.sh` (or any non-loopback bind) is in use anywhere reachable by non-operator hosts, **treat F-01 + F-09 as P0 now** and confirm containment (bind host, firewall) before anything else.

**P1 — significant defect/risk**
- F-01 Add an authorization layer in front of / inside the ADK server and derive `user_id` from a verified identity (frontend must stop forwarding caller-supplied ids).
- F-02 Untrack and ignore `**/.adk/`; decide on history handling; move dev sessions out of the source tree.
- F-03 Remove the hardcoded token from `hermes_agent/agent.py`, rotate the `default` profile peer token, scrub the POC doc.
- F-04 Capture one live Hermes turn and confirm/fix reply persistence (finality contract).
- F-05 Give the hermes shell an explicit timeout consistent with the others; define timeout → cancel/reconcile semantics before Hermes tools can mutate anything.
- F-07 Fix the pricing table / model duplication so receipts work for `gemini-3.7-flash`.
- F-08 Fail closed when instructions cannot be loaded; document who may write instruction objects.

**P2 — normal backlog**
- F-06 Validate required env at startup.
- F-10 items 4–7 (list-apps noise, path leak, `.gcloudignore *.json`, `.env_example` fragments, `store_secrets.sh` grep).
- F-11 Boundary tests (routes, sessions, A2A stub, config failure, receipts for configured model).
- F-12 Documentation purge / attic; prune requirements; add the `CLAUDE.md` protocol files or waive them explicitly.
- Move sync GCS/Vertex calls off the event loop.

**FUTURE GATE — before planned deployment/integration**
- F-09 Per-user identity propagation to Hermes (or a trusted-caller-only topology) and restriction of Hermes toolsets per profile.
- F-10 items 1–3: real Dockerfile/deploy config, shared session store, configurable https Hermes endpoints, ingress/IAM design.

**QUESTION — requires architecture/environment clarification**
1. Where has the ADK server ever been bound to a non-loopback interface, and who can reach it?
2. Is the GitHub repository private?
3. Which Hermes toolsets are enabled on each profile today, and is the `default` (:9900) profile retired?
4. Does Hermes emit a terminal (COMPLETED) A2A event with the reply, or only streamed chunks? (decides F-04's fix)
5. Who is allowed to write `ADK_Agent_Bundle_1/*/*_instructions.txt` in the bucket?
6. Is the frontend expected to bind `user_id` to the Supabase session, or is the backend expected to authenticate users directly?

---

### 21. Change Boundary Confirmation

Files created (all under `fable-review/`):
- `fable-review/FABLE_REVIEW_PROMPT.md`
- `fable-review/FABLE_CODE_REVIEW.md`
- `fable-review/RUN_NOTES.md`

Confirmed unchanged: all application source, tests, `requirements*.txt`, `pytest.ini`, `.env_example`, `.gcloudignore`, shell scripts, docs, committed `.adk/session.db` files (opened read-only via `mode=ro`), git refs and index (`git status --porcelain` → only `?? fable-review/`; `git diff --stat HEAD` empty). No GCP, Cloud Run, GCS, Vertex AI, Supabase, or Hermes resource was contacted or modified. No git mutating command was executed. Verification byproducts created inside the repo (`__pycache__/`, empty `logs/receipts/`) were removed and are recorded in RUN_NOTES.
