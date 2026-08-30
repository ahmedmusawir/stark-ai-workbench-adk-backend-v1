# RECON REPORT — adk-2.x-and-harmes-v1 — P0 baseline

**Date:** 2026-08-29
**Engineer:** Claude Code (stark-recon v1.1)
**Repo:** `/home/moose/python/adk-2.x-and-harmes-v1` (branch `main`, 3 commits, HEAD `36edbd3 "multi profile done"`)
**Mission adaptation:** the RECON_MISSION questionnaire is Next.js-kit-oriented; this is a Python / Google ADK / Hermes-A2A repo. Web-kit sections (Tailwind tokens, Supabase migrations, nav/auth-state, tsconfig) are answered as N/A with the closest equivalent checked. Operator-added capture (A2A wiring, session state, artifact transport, exact versions, env names) is included as first-class sections.
**Read-only contract:** zero repo files modified outside `agent_docs/recon/`. No git mutations. Live probes (curl to localhost agent cards, `hermes profile list`, immutable-mode SQLite reads) were observation-only.

---

## Section 0 — Day-0 Ground-Truth Sweep (doc vs disk)

The three governing docs for this repo are:
- `docs/ADK 2.7.1 ↔ Hermes A2A — Proven Local POC Setup.md` (the POC doc)
- `docs/HERMES_MULTI_PROFILE_A2A_ADK_RUNBOOK_v1.0 (1).md` (the runbook)
- `docs/REPO_AUDIT_REPORT.md` (audit of the ANCESTOR repo, not this one — see drift D7)

| # | Doc claim | Disk reality | Verdict |
|---|---|---|---|
| D1 | POC doc §2: "google-adk==2.7.1 verified" | `requirements.txt:30` still pins `google-adk==1.13.0`; installed venv has **2.7.1** (`pip show google-adk`) | **DRIFT — requirements.txt is stale.** Disk (venv) wins: ADK 2.7.1 is what runs. EVIDENCE |
| D2 | Runbook §9: ADK shell for architect is `name="architect_agent"`, description "Software Architect connected through Hermes A2A." | `architect_agent/agent.py:7` → `name="hermes_agent"`; `designer_agent/agent.py:7` → `name="hermes_agent"`; only `devops_agent/agent.py:7` was renamed (`name="devops_agent"`). All three descriptions still read "Local Hermes Agent connected through A2A." | **DRIFT — copy-without-rename.** Two ADK shells self-identify as `hermes_agent`. EVIDENCE |
| D3 | Runbook §3: all profiles cloned from `default` (deepseek-v4-flash) | `hermes profile list` (live): architect=`deepseek-v4-pro:cloud`, designer=`minimax-m3:cloud`, devops=`glm-5.2:cloud` | **DRIFT (forward progress)** — model specialization landed after the runbook was written (matches commit "multi profile done"). Doc is behind reality. EVIDENCE |
| D4 | POC doc §13 / Known-Good Commands: default gateway on :9900 running | Live curl to `http://127.0.0.1:9900/.well-known/agent-card.json` → empty; `hermes profile list` shows default gateway **stopped**. :9901/:9902/:9903 all serve cards. | **DRIFT — `hermes_agent` ADK shell currently points at a dead endpoint.** EVIDENCE |
| D5 | `.env_example` names `GOOGLE_API_KEY`, `GHL_API_TOKEN`, `GHL_LOCATION_ID` | Actual `.env` contains none of those (names-only diff; values never read) | **DRIFT — example file does not describe the real env.** EVIDENCE |
| D6 | `start_server.sh:16` requires `SUPABASE_DB_URI` from `.env` | `SUPABASE_DB_URI` is absent from `.env` (name scan) | **GAP — `start_server.sh` cannot work as-is today.** EVIDENCE |
| D7 | `docs/REPO_AUDIT_REPORT.md` header: audits branch `kit-handbook-v1`, commit `9d119f1`, repo "ADK Harness Starter v1", claims a Dockerfile (python:3.11-slim) | This repo's `main` has 3 commits, no `kit-handbook-v1` branch content, and `find . -name Dockerfile` → **no Dockerfile anywhere** | **DRIFT — the audit describes the ancestor repo (`../adk-harness-starter-v1`), not this one.** Treat its every claim as CLAIM, not fact. EVIDENCE |
| D8 | `CHANGELOG.md` (2026-03-04): "Updated `ghl_mcp_agent/agent.py`" | No `ghl_mcp_agent/` directory exists; zero `ghl` refs in any `.py` | **DRIFT — changelog references a deleted/never-cloned agent.** EVIDENCE |
| D9 | `docs/architecture.md`, `docs/decisions.md`, `docs/patterns.md` present themselves as this repo's docs | All three are headed "**VidGen — Bibo YouTube Video Generator**, Extracted 2026-02-22" — a different project entirely | **DRIFT — cross-project doc residue** (the Q8.5 clone-debt class, in docs form). EVIDENCE |

Forbidden-zone greps (adapted for Python): no `os.getenv`/`os.environ` outside `utils/token_calculator.py:45-46`, `utils/context_cache.py:18-19`, `scripts/run_evals.py:22` — but note there is **no `config_service.py` at all** in this repo, so the global "env via config_service" rule has nothing to route through (GAP, see Recommendation). No `dangerouslySetInnerHTML` / `: any` class of issue applies (no TS source).

---

## Section 1 — Stack Versions (exact, from disk)

**Python side (venv = truth; requirements.txt is stale where noted):**
- Python: **3.12.11** — EVIDENCE: `.python-version` + `.venv/bin/python --version` (both agree)
- google-adk: **2.7.1 installed** vs `1.13.0` pinned in `requirements.txt:30` — **stale pin**
- a2a-sdk: **1.1.2 installed**, **absent from requirements.txt** (installed via `google-adk[a2a]` per POC doc §3) — a fresh `pip install -r requirements.txt` would NOT reproduce the working env. EVIDENCE
- google-genai: **2.20.0 installed** vs `1.32.0` pinned — stale pin
- httpx: 0.28.1 (the A2A client transport dep used in every RemoteA2aAgent shell)
- Others (pinned + matching install assumed, not individually verified): fastapi 0.116.1, uvicorn 0.35.0, litellm 1.66.3, openai 1.98.0, mcp 1.12.2, google-cloud-storage 2.19.0, pydantic 2.11.7
- Test runner: **pytest** — EVIDENCE: `pytest.ini` with `unit` / `integration` markers. (Not run during recon — running it writes `.pytest_cache`, violating the zero-modification contract. CHANGELOG's "52/52 green" is a CLAIM as of kit lock.)

**Node/Next.js:** this repo contains **no `package.json`, no Node code, no Next.js** — GAP (expected nothing; confirmed nothing). Host has Node **v26.7.0** at `~/.local/bin/node`, relevant only as ambient tooling. EVIDENCE

**Hermes side (external to repo, live-verified):**
- Hermes Agent **v0.20.5 (2026.8.19)**, upstream `4c1f53be`, install method: git, at `~/.hermes/hermes-agent` — EVIDENCE: `hermes --version`
- Protocol: A2A v1.0, JSON-RPC binding, bearer security — EVIDENCE: live agent card

---

## Section 2 — Repo Structure vs Docs

**Actual shape (top 2 levels, non-generated):** six ADK agent packages (`jarvis_agent`, `hermes_agent`, `architect_agent`, `designer_agent`, `devops_agent`, `product_agent_rico_1` — each exactly `__init__.py` + `agent.py` + `.adk/session.db`), shared `utils/` (5 modules, 474 lines), `callbacks/` (receipt callback), `scripts/` (eval runner, usage report), `tests/` (5 files), `evals/`, `skills/` (one scaffold doc), `logs/receipts/`, `credentials/`, `docs/`, `agent_docs/`.

- Every `__init__.py` exports `root_agent` via `from .agent import root_agent` — EVIDENCE (all six read). Matches the ADK convention in project CLAUDE.md. (POC doc §9 shows `from . import agent` — minor doc drift; disk form also works. INFERENCE.)
- No `src/`, no services/types split, no middleware/proxy — N/A (Python repo).
- `agent_docs/` is **untracked in git** (git status) and contains `RECON/` (uppercase, empty), `RESPONSES/` (empty), `SKILLS/` (the stark-recon skill). This report creates the lowercase `recon/` sibling per operator instruction — the empty uppercase `RECON/` is now a duplicate-by-case. QUESTION: delete `RECON/` or consolidate? (Deletion not performed — read-only.)
- Protocol scaffolding named by project CLAUDE.md is **absent**: no `RECOVERY.md`, no `agent_docs/SESSIONS/`, no `agent_docs/KIP_REGISTRY.md` — GAP.

---

## Section 3 — A2A Wiring: Shells → Hermes Workers (operator capture #1)

**The full map, every cell disk- or live-verified:**

| ADK shell (dir) | Internal `name=` | Agent card URL | Hermes profile | Card `name` (live) | Profile model (live) | Gateway state (live 2026-08-29) |
|---|---|---|---|---|---|---|
| `hermes_agent/` | `hermes_agent` | `http://127.0.0.1:9900/...` | `default` | — (no response) | deepseek-v4-flash:0731-cloud | **STOPPED — dead endpoint** |
| `architect_agent/` | `hermes_agent` ⚠️ | `http://127.0.0.1:9901/...` | `architect_agent` | "Architect Agent" | deepseek-v4-pro:cloud | running |
| `designer_agent/` | `hermes_agent` ⚠️ | `http://127.0.0.1:9902/...` | `designer_agent` | "Designer Agent" | minimax-m3:cloud | running |
| `devops_agent/` | `devops_agent` | `http://127.0.0.1:9903/...` | `devops_agent` | "Devops Agent" | glm-5.2:cloud | running |

- EVIDENCE: `hermes_agent/agent.py:9`, `architect_agent/agent.py:9`, `designer_agent/agent.py:9`, `devops_agent/agent.py:9`; live curls; `hermes profile list`.
- All four shells hardcode the same bearer token in source (`Authorization: Bearer stark-…`, `*/agent.py:12`) — acknowledged POC-only in POC doc §9/§13, but it is now four copies instead of one. EVIDENCE.
- Auth scheme per live card: `{"bearer": {"type": "http", "scheme": "bearer"}}`. Streaming: true; pushNotifications: true.
- The two ⚠️ shells (`architect`, `designer`) self-identify as `hermes_agent` inside their own ADK app. Under `adk web` each folder is a separate app so they don't collide at runtime — INFERENCE — but transcripts/receipts/evals keyed by agent name would mislabel, and the runbook's own §9 spec says they should be renamed. Reconciliation candidate.
- **Local (non-A2A) agents:** `jarvis_agent` (tools: `google_search`) and `product_agent_rico_1` (tool: `fetch_context`), both `model="gemini-3.7-flash"` hardcoded twice each (Agent arg + receipt-callback arg — a skew risk if one is edited without the other), instructions fetched live from GCS on every run (`utils/gcs_utils.py:fetch_instructions`, bucket + folder hardcoded at `utils/gcs_utils.py:5-7`). EVIDENCE.
- ADK Dev UI at :8000 (`adk web` per POC doc; `start_server.sh` variant broken — see D6).

---

## Section 4 — Session State: Where It Lives, Does It Survive Restart (operator capture #2)

- **Where:** per-agent SQLite at `<agent_dir>/.adk/session.db` — created by the ADK 2.x dev runtime (`adk web`) — INFERENCE on creator; EVIDENCE on existence for all six agents.
- **Contents (read via SQLite immutable mode — zero write risk):** tables `app_states` / `user_states` / `sessions` / `events`. Row counts: jarvis 2 sessions/8 events; hermes 1/8; architect 3/16; designer 4/16; devops 9/28 (most recent activity, mtime Aug 29 08:52); rico 1/4. `app_states` and `user_states` are 0 everywhere — only conversational session/event state exists. EVIDENCE.
- **Survives restart:** **yes** — it is on-disk SQLite, not `InMemorySessionService`. EVIDENCE (files persist across the Aug 26 → Aug 29 gap with accumulating counts).
- **⚠️ Tracked in git:** all six `session.db` files are committed (`git ls-files`) and four show as modified in `git status`. Mutable runtime state is riding in history and will dirty the tree on every agent run. Reconciliation candidate: gitignore `**/.adk/session.db` and remove from tracking (operator's call, operator's commands).
- **Alternate path:** `start_server.sh` would instead use `adk api_server --session_service_uri=$SUPABASE_DB_URI` (Postgres/Supabase-backed sessions) — currently broken per D6. The two session backends are mutually exclusive per launch method; nothing migrates between them. INFERENCE.

---

## Section 5 — Artifact / File-Transport Code Paths (operator capture #3)

- **ADK side: none.** Grep across all repo `.py` for `artifact|save_artifact|load_artifact|FilePart|inline_data|Blob` → zero hits outside GCS text helpers. No `artifact_service` is configured anywhere. GAP (searched, absent).
- **A2A channel: text-only.** Live agent card `defaultInputModes: ['text/plain']`, `defaultOutputModes: ['text/plain']` — no file/binary modality is negotiated over A2A today. EVIDENCE.
- **Hermes side: file tools exist but are host-local.** The card advertises 33 skills including `toolset.file` (`read_file`, `search_files`, `write_file`) plus browser/code_execution/computer_use toolsets — meaning a Hermes worker can touch files **on the Hermes host's own filesystem**, but nothing round-trips file content through the A2A channel to ADK. EVIDENCE (card) + INFERENCE (locality).
- **Closest existing transport:** GCS text pulls — `utils/gcs_utils.py:28` and `utils/context_utils.py:32,76` (`download_as_text` only; no uploads, no binary). EVIDENCE.
- Net: **no artifact pipeline exists, even partial.** Anything Phase-1+ that needs file handoff between ADK and Hermes workers is greenfield.

---

## Section 6 — Environment Variables (names only) & Secrets Posture

**Referenced anywhere (union, names only — values never read or printed):**

| Name | Where referenced |
|---|---|
| `GOOGLE_GENAI_USE_VERTEXAI` | `.env`, `.env_example`, `scripts/run_evals.py:22` (setdefault before ADK imports ✓) |
| `GOOGLE_APPLICATION_CREDENTIALS` | `.env`, `.env_example` |
| `GOOGLE_CLOUD_PROJECT` | `.env`, `utils/token_calculator.py:45`, `utils/context_cache.py:18` |
| `GOOGLE_CLOUD_LOCATION` | `.env`, `utils/token_calculator.py:46`, `utils/context_cache.py:19` (default `us-central1`) |
| `GOOGLE_CLOUD_REGION` | `.env` only — **referenced by no code** (orphan name) |
| `GOOGLE_STT_BUCKET` | `.env` only — no code refs (speech-to-text residue; `google-cloud-speech` is pinned in requirements but imported nowhere) |
| `GOOGLE_API_KEY` | `.env_example` only (not in real `.env`; Vertex path doesn't need it) |
| `SUPABASE_DB_URI` | `start_server.sh:16`, `store_secrets.sh` — **not in `.env`** (GAP D6) |
| `GHL_API_TOKEN`, `GHL_LOCATION_ID` | `.env_example`, `store_secrets.sh` — zero code refs; GoHighLevel residue from ancestor kit (D8) |
| `A2A_AGENT_NAME`, `A2A_PEER_TOKENS`, `A2A_PORT` | Hermes-side `~/.hermes` profile `.env`s (per runbook §6; external to repo) |

**Secrets posture:** `.env` and `credentials/cyberize-vertex-api.json` are both properly git-ignored — EVIDENCE: `git check-ignore -v` hits `.gitignore:138` and `:211`. A service-account key file (dated Jun 2025) does sit on disk in `credentials/`. The A2A bearer token is hardcoded in four source files (tracked in git) — known POC debt. QUESTION for operator: `.env_example` contains partially-masked-but-real-looking GHL token fragments; scrub to pure placeholders?

---

## Section 7 — Config/Bucket Hardcoding (config-service rule check)

- `utils/gcs_utils.py:5-7` — bucket `adk-agent-context-…` + folder `ADK_Agent_Bundle_1` hardcoded.
- `utils/context_utils.py:7-8` — same bucket + `context_store` folder hardcoded (comment says "Configuration from your screenshot").
- `store_secrets.sh` / `grant_permissions.sh` — GCP project id + SA email hardcoded (acceptable for ops scripts; noted).
- There is **no `config_service.py`** in this repo — the global CLAUDE.md "all env via config_service" pattern is not instantiated here at all. Flagged as doctrine-vs-disk gap for the Architect to either scope in or explicitly waive for this POC repo. GAP.

---

## Section 8 — Demo/Tutorial Scaffolding & Cross-Project Residue

- **VidGen doc set:** `docs/architecture.md` (493 ln), `docs/decisions.md` (477 ln), `docs/patterns.md` (682 ln) — all from "Bibo YouTube Video Generator", a different project. Pure clone-debt; misleading to any future doc-reading agent. EVIDENCE (headers read).
- **Ancestor-kit residue:** `docs/REPO_AUDIT_REPORT.md` (audits `adk-harness-starter-v1` @ `kit-handbook-v1`), `docs/APP_BRIEFS/*` (MASTER_BRIEF v1.2 declares repo identity `adk-harness-starter-v1`), CHANGELOG's `ghl_mcp_agent` entries, GHL env names, `store_secrets.sh` GHL mappings. The sibling checkout `../adk-harness-starter-v1` exists on disk — this repo is its descendant. EVIDENCE + INFERENCE.
- **Dependency residue (INFERENCE from zero imports):** `yfinance`, `google-cloud-speech`, `beautifulsoup4`, `pandas`/`numpy`, `peewee`, `alembic`, `psycopg2-binary`, `litellm` (jarvis comment says "LiteLLM client" but code uses plain Gemini — comment drift at `jarvis_agent/agent.py:13`), `openai`, `tiktoken` — none imported by any repo `.py`. Bloat, not breakage.
- **DockBloxx residue:** `utils/context_utils.py` docstring instructs answering "questions about DockBloxx products" — product-specific text inside a shared util. EVIDENCE `utils/context_utils.py:15`.
- Recommended deletion bucket: one "clone-debt purge" reconciliation task (docs + env names + store_secrets map + dead deps) — single pass, operator-approved, NOT during recon.

---

## Section 9 — Packaging / Compile Scope

- N/A for tsconfig. Python equivalent: `pytest.ini` defines markers only, no testpaths — pytest would collect from repo root, but `agent_docs/` contains no `test_*.py`, so no scope pollution today. `.gcloudignore` excludes `.venv`, `.env`, `*.json` (note: `*.json` would also exclude `evals/*.json` from any Cloud Build upload — latent deploy trap, INFERENCE).
- `absolufy-imports` pinned — kit convention for absolute imports (`utils.…` imports confirm the pattern works from repo-root CWD; `adk web` must be launched from repo root — EVIDENCE: POC doc Known-Good Commands, and `sys.path` insert in `scripts/run_evals.py:26`).

---

## Section 10 — Surprises (the gold)

1. **The default Hermes gateway (:9900) is down**, so the flagship `hermes_agent` shell is currently a dead pointer while all three specialists are live. Anyone demoing "the original POC" today hits a connection error. (Also: default profile still on deepseek-v4-flash while specialists were upgraded to three *different* models — deliberate A/B, or drift? QUESTION.)
2. **Two of three specialist shells still self-identify as `hermes_agent`** (`architect_agent/agent.py:7`, `designer_agent/agent.py:7`) and all three kept the copy-pasted description. The runbook's own acceptance test ("who are you") passes only because identity comes from the Hermes-side SOUL.md, masking the ADK-side naming bug.
3. **Session DBs are committed to git** and perpetually dirty — four `session.db` files modified in the current tree. History will accrete binary churn every run until ignored.
4. **`requirements.txt` cannot rebuild the working environment** — it pins ADK 1.13.0 (actual 2.7.1) and omits `a2a-sdk` entirely. A clean-venv `pytest` per TDD doctrine would today install the *wrong ADK major version*.
5. **A third of `docs/` belongs to other projects** (VidGen trio; ancestor-kit briefs/audit). An agent doing doc-first discovery here would be badly misled — this recon nearly was.
6. **`start_server.sh` is broken on arrival** (missing `SUPABASE_DB_URI`) — the only scripted server entry point doesn't run; the actual proven path (`adk web`) lives only in the POC doc.
7. **Hermes workers advertise heavyweight toolsets** (file, code_execution, browser, computer_use, discord, homeassistant… 33 skills) on localhost bearer-token auth. Fine for local POC; the POC doc §13 already mandates limiting advertised toolsets before any exposure — reality confirms the concern is live, not theoretical.
8. `agent_docs/RECON/` (uppercase, empty) predates this report's `agent_docs/recon/` — case-twin directories now coexist.
9. No `cn()` helper / web checks — N/A across the board; noted per template completeness.

---

## Recommendation to Architect

**Facts safe to author against without re-verification:**
- Topology: 4 RemoteA2aAgent shells → Hermes profiles on :9900–:9903 (map in §3); 2 local Gemini agents (`gemini-3.7-flash`) with GCS-fetched instructions; ADK 2.7.1 + a2a-sdk 1.1.2 + Python 3.12.11; Hermes v0.20.5 git-install; A2A = JSON-RPC v1.0, bearer, text/plain both directions, streaming on.
- Session state: per-agent on-disk SQLite (`.adk/session.db`), survives restart, no app/user state in use.
- No artifact/file transport exists at any layer of the ADK↔Hermes path — greenfield.
- Test runner: pytest with unit/integration markers, 5 test files, shared-utils coverage only (no agent-shell or A2A tests exist).

**Doctrine/doc drift to surface (fix docs or schedule reconciliation — not both silently):**
- D1/D4 stale `requirements.txt` (ADK pin + missing a2a-sdk) — highest priority; breaks the clean-venv doctrine.
- D2 shell naming (`architect`/`designer` still named `hermes_agent`; descriptions all wrong).
- D6 `start_server.sh` vs missing env name; decide: fix script or bless `adk web` as the only entry point.
- Session DBs tracked in git — decide ignore-and-untrack (operator runs the git commands).
- Runbook/POC doc behind reality on models-per-profile and gateway states.

**Cleanup candidates (one operator-approved purge pass):** VidGen doc trio; ancestor-kit briefs/audit (or move to an `docs/_inherited/` attic); GHL env names + store_secrets mappings; orphan env names (`GOOGLE_CLOUD_REGION`, `GOOGLE_STT_BUCKET`, `GOOGLE_API_KEY` in example); unimported heavyweight deps; DockBloxx docstring; empty `agent_docs/RECON/`.

**Open questions for operator:**
1. Is :9900/default staying in the fleet (restart it, rename shell honestly) or retiring in favor of the three specialists?
2. Three different cloud models across specialists — deliberate evaluation matrix or interim state to converge?
3. `.env_example` GHL fragments — scrub to pure placeholders?
4. Should this repo adopt `config_service.py` per global doctrine, or is POC-grade hardcoding waived until the phase brief says otherwise?

**Protocol note:** per operator instruction this session wrote only inside `agent_docs/recon/`; the CLAUDE.md session-file/RESPONSES writes were intentionally skipped for this recon to honor the zero-modification contract. This report is the session's artifact of record.

---
*stark-recon v1.1 — one pass, one report. Disk wins.*
