# RUN_NOTES — Fable 5.1 independent review

## Identity

| Item | Value |
| --- | --- |
| Repository | `stark-ai-workbench-adk-backend-v1` (remote: `github.com/ahmedmusawir/stark-ai-workbench-adk-backend-v1`) |
| Review branch | `fable-code-review-13sep2026` (verified via `git rev-parse --abbrev-ref HEAD`) |
| Pinned source SHA | `1eb7d88730447cc10d950817d24e8324429926cf` — exists (`git cat-file -t` → commit) and **equals HEAD** |
| Working tree at start | clean (`git status --porcelain` empty; `git diff --stat <pinned> HEAD` empty) |
| Review start (local, UTC+06:00) | 2026-09-13 15:39 |
| Review end (local) | 2026-09-13 ~16:10 |
| Reviewer host | Windows 10 Pro 10.0.19045, Git 2.21.0.windows.1, Git Bash |
| Reviewer | Claude Fable 5.1 (Claude Code) |

Pre-existing / unexpected changes: none. `main`, `origin/main`, and the review branch all point at the pinned SHA.

## Runtime and dependency versions

| Component | Repo pin (`requirements.txt`) | Installed in review venv |
| --- | --- | --- |
| Python | `.python-version` = 3.12.11 | 3.12.1 (only interpreter on host; 3.12.11 not available) |
| google-adk | 2.7.1 | 2.7.1 |
| a2a-sdk | 1.1.2 | 1.1.2 (A2A v1.x protocol path, `IS_A2A_V1`) |
| google-genai | 2.20.0 | 2.20.0 |
| httpx | 0.28.1 | 0.28.1 |
| fastapi / starlette / uvicorn | 0.141.1 / 1.6.0 / 0.35.0 | same |
| pydantic | 2.13.5 | 2.13.5 |
| google-cloud-storage | 2.19.0 | 2.19.0 |
| pytest | 9.1.1 | 9.1.1 |

`pip check` → "No broken requirements found". `requirements.txt` is a full freeze (~140 packages) including many packages no repo module imports (litellm, yfinance, pandas, google-cloud-speech, etc.).

External (not in repo, from docs/recon only): Hermes Agent v0.20.5 per `agent_docs/recon/RECON_*_2026-08-29.md`; ADK ↔ Hermes over A2A JSON-RPC v1.0 with bearer auth; Hermes profiles on 127.0.0.1:9900–9903.

## Architecture summary (established from source)

- **No application server code exists in this repo.** The HTTP surface is Google ADK's stock `adk api_server` / `adk web` (FastAPI, `google/adk/cli/api_server.py`). There is no FastAPI wrapper, no route handler, no auth middleware, no CORS config, no Dockerfile, no deploy script in this repo (docs that claim otherwise describe an ancestor repo).
- **Six agent packages** at repo root, each `__init__.py` + `agent.py` + committed `.adk/session.db`:
  - `hermes_agent` — `RemoteA2aAgent` → `http://127.0.0.1:9900/.well-known/agent-card.json`, **hardcoded** `Authorization: Bearer stark-test-001`, httpx client with **default 5 s timeout**.
  - `architect_agent`, `designer_agent`, `devops_agent` — `RemoteA2aAgent` → 127.0.0.1:9901/9902/9903, bearer from `os.environ['HERMES_A2A_TOKEN']` (KeyError if absent), httpx timeout 120 s.
  - `jarvis_agent` — `LlmAgent`, model `gemini-3.7-flash`, tool `google_search`, instruction fetched from GCS on every LLM call, receipt callbacks.
  - `product_agent_rico_1` — `LlmAgent`, model `gemini-3.7-flash`, tool `fetch_context(file_name)` (GCS read), instruction from GCS (`fetch_instructions("product_agent")`), receipt callbacks.
- **Shared code:** `utils/gcs_utils.py`, `utils/context_utils.py` (hardcoded bucket `adk-agent-context-ninth-potion-455712-g9`), `utils/token_calculator.py`, `utils/run_receipt.py`, `callbacks/receipt_callback.py` (writes `logs/receipts/<agent>.jsonl`), `scripts/run_evals.py`, `scripts/usage_report.py`.
- **Session persistence:** ADK default local storage = per-agent SQLite `<agent_dir>/.adk/session.db` (ADK `cli/utils/local_storage.py`); alternative `start_server.sh` → `adk api_server . --host=0.0.0.0 --port=8000 --session_service_uri="$SUPABASE_DB_URI"`.
- **Consumer (outside repo, read-only look):** sibling `stark-ai-workbench-nextjs-frontend-v1` calls this api_server directly from Next.js route handlers (`src/app/api/agent/_lib/adk.ts`), forwarding the client-supplied `user_id` and `session-${Date.now()}` session ids.

## Commands executed (all read-only against the repo; writes only to `fable-review/` and a temp venv)

```
git rev-parse --show-toplevel / --abbrev-ref HEAD / HEAD
git cat-file -t 1eb7d88730447cc10d950817d24e8324429926cf
git status --porcelain=v1 --untracked-files=all ; git status --ignored --porcelain
git diff --stat 1eb7d88… HEAD ; git remote -v ; git log --oneline -5 --decorate ; git branch -a
git ls-files ; git ls-files -s | grep session.db
git log --stat --format=… ; git show 1eb7d88 -- <agent shells> ; git log --all -S"stark-test-001" ; git log --all -S"HERMES_A2A_TOKEN"
git log --all --name-only --pretty=format: | sort -u | grep -iE "\.env$|\.json$|credential|key"
cat / sed / grep over every tracked .py, .sh, .md, .txt, .json, .ini, .env_example, .gcloudignore
python (system 3.12.1) sqlite3 read-only (`file:…?mode=ro`) inspection of all six committed .adk/session.db
py -m venv C:\Users\user\AppData\Local\Temp\fv\venv ; pip install -r requirements.txt   (first attempt in scratchpad failed: WinError 206 path too long on pywin32; retried in short path)
python -m pytest -p no:cacheprovider --collect-only -q          → 41 tests collected
python -m pytest -p no:cacheprovider -m unit -q                 → 30 passed, 11 deselected (1.79 s)
python -m py_compile utils/*.py callbacks/*.py scripts/*.py */agent.py → OK
python -c "import <agent>" for all six agents, with and without HERMES_A2A_TOKEN
adk --version ; adk api_server --help ; adk web --help
adk api_server . --host 127.0.0.1 --port 18765 --session_service_uri sqlite:///<temp>/sess.db --artifact_service_uri memory:// --memory_service_uri memory:// --no-reload
   + scripted HTTP probes (see results) ; server terminated afterwards
python offline checks: httpx default timeout; GCS Blob.path encoding; estimate_cost("gemini-3.7-flash"); receipt callback with live model string (count_tokens mocked)
grep/sed over installed google-adk 2.7.1 and a2a-sdk 1.1.2 sources (api_server.py, remote_a2a_agent.py, _compat.py, to_adk_event.py, database_session_service.py, local_storage.py, runners.py, base_client.py)
read-only grep/cat of sibling frontend repo (src/app/api/agent/*, config/agents.manifest.json, .env.example, src/proxy.ts)
```

Not run: integration-marked tests (require Vertex AI credentials and cost tokens); `scripts/run_evals.py` (would call Gemini and write `logs/`, `evals/reports/`); `start_server.sh` (needs `.env` with `SUPABASE_DB_URI`); any lint/type tool (none configured in repo: no ruff/mypy/pyright/flake8 config).

## Results

### Tests
- Collection: 41 tests in 4 files (`test_eval_runner.py` 10, `test_receipt_callback.py` 6, `test_run_receipt.py` 13, `test_token_calculator.py` 10, marker `unit`/`integration`).
- `-m unit`: **30 passed, 0 failed**. 11 integration tests deselected (they call Vertex `count_tokens`).
- No test imports any agent package, any route, any session service, or any A2A code.

### Import / startup checks
- `hermes_agent`, `jarvis_agent`, `product_agent_rico_1` import cleanly (no network at import).
- `architect_agent`, `designer_agent`, `devops_agent` raise `KeyError: 'HERMES_A2A_TOKEN'` at import when the variable is unset; import fine with any dummy value (agent card is resolved lazily at first run, not at import).
- `adk api_server` started in ~1 s with a temp SQLite session DB; 16 route paths registered (`/openapi.json`).

### Local HTTP probes (E3, loopback only, temp session DB — no Gemini, GCS, or Hermes contacted)

| Probe | Result |
| --- | --- |
| `GET /list-apps` (no auth) | 200; returned every top-level directory name incl. `docs`, `tests`, `fable-review`, `logs` |
| `OPTIONS`/`GET /list-apps` with `Origin: https://evil.example` | **403** (ADK `_OriginCheckMiddleware`) |
| `POST /apps/hermes_agent/users/victim-user/sessions/fixed-session-1` | 200 — caller-chosen user id AND session id accepted |
| `GET /apps/hermes_agent/users/victim-user/sessions` (no auth) | 200 — lists that user's sessions |
| `GET …/users/victim-user/sessions/fixed-session-1` | 200 — full session returned |
| `GET …/users/attacker/sessions/fixed-session-1` | 404 — session key is (app, user_id, session_id); the user_id is caller-supplied so this is not an ownership check |
| `POST /run` hermes_agent (127.0.0.1:9900 not running here) | 200 with an `errorMessage` event: "Failed to resolve AgentCard … All connection attempts failed" |
| `POST /run` architect_agent with `HERMES_A2A_TOKEN` unset | **500** plain "Internal Server Error"; server log shows `KeyError: "Fail to load 'architect_agent' module. HERMES_A2A_TOKEN"` |
| `POST /run` unknown app | 404 with detail leaking absolute filesystem path of the agents dir |
| `DELETE …/users/victim-user/sessions/fixed-session-1` (no auth) | 200 |

### Committed session databases (read-only)
- All six `.adk/session.db` are tracked. Tables `app_states`, `user_states`, `sessions`, `events`. They contain **real conversation content**: user prompts (e.g., "hey jarvis ... compare deepseek v4 pro with claude opus models"), a full Jarvis answer, a Rico product-price table (85 KB of event data), and a frontend-originated user id `ca62b315-1db0-4921-b47d-a7a31eacfc15` with `session-<epoch-ms>` ids.
- The `architect_agent`, `designer_agent`, `devops_agent` DBs are cumulative copies that also contain `hermes_agent` sessions (copied-folder lineage).
- For **every** remote (A2A) agent turn across all four shells (18 turns), the persisted agent event has **no `content`** and `a2a:response.status.state == TASK_STATE_SUBMITTED`. No Hermes reply text is persisted anywhere. Two `devops_agent` events are `error_message` events ("All connection attempts failed" to :9903).
- No bearer token, API key, or credential material found in the event JSON (substring scan; the only "sk-" hits were `task-…` ids).

### Offline checks
- `httpx.AsyncClient(headers=…)` (hermes_agent shell) → `Timeout(timeout=5.0)`; workforce shells `Timeout(timeout=120.0)`.
- `estimate_cost(…, model="gemini-3.7-flash")` → `ValueError: Unknown model`. Driving `get_receipt_callback("jarvis_agent","gemini-3.7-flash")` with `count_tokens` mocked prints `[receipt_callback] Warning: failed to save receipt: Unknown model 'gemini-3.7-flash' …` and writes **no receipt file**; the same with `gemini-2.5-flash` writes one.
- GCS `Blob.path` URL-encodes `/` in object names: `fetch_context("../jarvis_agent/…")` addresses the literal object `…context_store%2F..%2Fjarvis_agent…`, so the tool cannot escape the `ADK_Agent_Bundle_1/context_store/` prefix.

## Unavailable / not exercised
- Live Hermes gateways (127.0.0.1:9900–9903) — not present on the review host; all A2A behaviour beyond the failure path is source inference plus committed-DB artifacts.
- Vertex AI / Gemini, GCS bucket, GCP IAM, Secret Manager — no credentials on host; not contacted.
- Cloud Run — no Dockerfile/deploy config in this repo to review; only playbook docs.
- Supabase-backed session service (`start_server.sh`) — no `.env`.
- `gh` CLI not installed → repository visibility (public/private) **unknown**.

## Environment / configuration limitations
- Python 3.12.1 instead of pinned 3.12.11 (patch-level difference; no impact observed).
- Windows host; the proven Hermes/ADK setup is Linux (Zorin). `adk api_server` itself ran fine.
- Long-path failure forced the venv to `C:\Users\user\AppData\Local\Temp\fv\venv` instead of the session scratchpad.

## Interruptions / incidents
- Review byproducts were created inside the repo by the verification runs and then removed: nine gitignored `__pycache__/` directories (bytecode from imports/pytest/server load) and an empty gitignored `logs/receipts/` tree created at server start. All were created after 15:39 today, contained only `.pyc` files or nothing, and were removed. `git status --ignored` afterwards shows only `?? fable-review/`.
- Two Bash heredoc attempts failed (harness command-length / long-path); files were written with the editor tool instead.
- Project `CLAUDE.md` mandates session-log / RECOVERY.md / `agent_docs/RESPONSES` writes; these were **not** performed because the review instructions restrict writes to `fable-review/`. Noted for the Operator.

## Change-boundary confirmation
- Files created: `fable-review/FABLE_REVIEW_PROMPT.md`, `fable-review/FABLE_CODE_REVIEW.md`, `fable-review/RUN_NOTES.md`.
- `git status --porcelain` at end: `?? fable-review/` only. `git diff --stat HEAD`: empty.
- No application source, tests, dependencies, configuration, `.env`, GCP/GCS/Vertex/Cloud Run resources, Hermes agents, or git refs were modified. No git mutating command was run.
