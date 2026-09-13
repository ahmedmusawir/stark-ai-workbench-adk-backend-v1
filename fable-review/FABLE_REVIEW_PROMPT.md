# FABLE 5.1 — STARK AI WORKBENCH ADK BACKEND INDEPENDENT CODE REVIEW
# Review date: 2026-09-13

You are performing a deep independent senior/principal engineering review of this repository.

REPOSITORY:
stark-ai-workbench-adk-backend-v1

REVIEW BRANCH:
fable-code-review-13sep2026

PINNED SOURCE SNAPSHOT:
1eb7d88730447cc10d950817d24e8324429926cf

This SHA represents the clean main snapshot before review artifacts are added.

This branch exists only to preserve code-review evidence.

THIS BRANCH WILL NOT BE MERGED INTO MAIN.

Application source is READ ONLY.

Tony Stark retains all git authority.

============================================================
1. VERIFY THE REVIEW STATE FIRST
============================================================

Before reviewing:

1. Confirm repository name.
2. Confirm current branch is:

   fable-code-review-13sep2026

3. Confirm pinned source revision exists:

   1eb7d88730447cc10d950817d24e8324429926cf

4. Inspect git status read-only.

5. Record any unexpected or pre-existing changes.

Do NOT:

- switch branches
- reset
- stash
- stage
- commit
- push
- modify application code

If the source state materially differs from the pinned snapshot, STOP and report it.

============================================================
2. CREATE THE REVIEW WORKSPACE
============================================================

Create ONLY:

fable-review/
├── FABLE_REVIEW_PROMPT.md
├── FABLE_CODE_REVIEW.md
└── RUN_NOTES.md

FABLE_REVIEW_PROMPT.md
- Preserve this complete instruction set.

FABLE_CODE_REVIEW.md
- Final authoritative review artifact.

RUN_NOTES.md
Record:

- repository
- branch
- pinned source SHA
- review start time if available
- Python/runtime/dependency versions
- ADK/A2A versions discovered
- architecture summary
- commands executed
- test/lint/type/build/startup results
- unavailable external systems
- environment/configuration limitations
- important review interruptions
- confirmation application source remained untouched

Do not create files outside fable-review/ unless Tony explicitly authorizes them.

============================================================
3. CHANGE BOUNDARY — STRICT
============================================================

THIS IS REVIEW ONLY.

YOU MAY:

- read/search source
- inspect Python packages/modules
- inspect FastAPI/ADK routes
- inspect A2A integration
- inspect RemoteA2aAgent usage
- inspect agent manifests/configuration
- inspect session/context handling
- inspect tool registration
- inspect request/response models
- inspect tests
- inspect configuration
- inspect Docker/deployment artifacts
- inspect dependency metadata
- inspect documentation
- inspect git history read-only if useful
- run existing safe local verification
- run existing tests
- run lint/type checks if configured
- run safe startup/import checks
- perform controlled local requests against local-only services if non-destructive
- write ONLY under fable-review/

YOU MAY NOT:

- modify application source
- repair findings
- refactor
- reformat source
- alter tests
- alter dependencies
- alter configuration
- change environment files
- modify GCP resources
- modify Cloud Run
- modify GCS
- mutate Vertex AI resources
- mutate remote Hermes agents
- invoke dangerous external tools
- perform destructive agent actions
- stage
- commit
- push
- merge
- rebase
- reset
- stash
- create/delete/switch branches

If stronger verification would require mutation or live authority, document the evidence needed instead.

============================================================
4. FIRST DETERMINE WHAT THIS BACKEND ACTUALLY IS
============================================================

Do not begin with assumptions.

Establish from repository ground truth:

- framework/runtime
- ADK version
- A2A implementation
- exposed HTTP/API routes
- agent definitions
- RemoteA2aAgent usage
- downstream agent endpoints
- orchestration flow
- session model
- user/session identifiers
- context handling
- file/context upload handling
- tool authority
- persistence
- configuration sources
- secrets/environment handling
- CORS
- authentication
- authorization
- health/status endpoints
- logging
- error handling
- timeout/retry behavior
- Docker/deployment model
- intended Cloud Run/GCP boundaries if represented

Classify important integrations as:

LOCAL
REAL EXTERNAL SERVICE
CONFIGURED BUT UNVERIFIED
MOCK
UNKNOWN

Do not claim behavior from downstream Hermes/ADK/GCP systems that the repository does not prove.

============================================================
5. PURPOSE OF THIS REVIEW
============================================================

This backend sits in an agentic system.

That changes the review emphasis.

A normal API bug may expose data.

An agentic-backend bug may also:

- route work to the wrong agent
- execute a tool with the wrong authority
- mix user/session context
- leak prior conversation state
- duplicate side effects
- amplify retries
- forward untrusted instructions
- cross an authority boundary unintentionally

Review the system accordingly.

Do NOT invent AI-specific dangers merely because agents are involved.

Trace real code paths and real authority.

============================================================
6. PRIMARY REVIEW PRIORITIES
============================================================

A. API EXPOSURE / AUTHENTICATION / AUTHORIZATION

Map every externally reachable route.

For each route ask:

WHO CAN CALL THIS?

HOW IS CALLER IDENTITY ESTABLISHED?

WHERE IS AUTHENTICATION ENFORCED?

WHERE IS AUTHORIZATION ENFORCED?

WHAT CALLER-CONTROLLED IDENTIFIERS ARE ACCEPTED?

WHAT DOWNSTREAM AUTHORITY DOES THE SERVER EXERCISE?

CAN AN UNTRUSTED CALLER SELECT:

- another user
- another session
- another agent
- another tool
- another resource
- another backend target

Do not equate frontend protection with backend authorization.

Do not assume Cloud Run/IAM protects a route unless that architecture is demonstrated.

If the backend is intentionally unauthenticated, determine what downstream operations that actually permits.

------------------------------------------------------------

B. AGENT ROUTING

Trace:

incoming request
→ requested agent
→ validation
→ manifest/config lookup
→ orchestration layer
→ RemoteA2aAgent or equivalent
→ downstream endpoint
→ returned response

Look for:

- caller-selected arbitrary agent names
- arbitrary endpoint selection
- manifest bypass
- stale manifests
- duplicate agent definitions
- wrong port/URL mapping
- environment-dependent routing drift
- fallback to unintended agent
- route/manifest mismatch
- unsafe defaults
- agent identity confusion

Verify that agent selection is constrained by trusted configuration rather than caller-provided URLs.

------------------------------------------------------------

C. A2A TRUST BOUNDARY

Treat A2A as a real distributed-system boundary.

Inspect:

- request construction
- identity forwarding
- session/user propagation
- authentication headers
- authorization assumptions
- task/message IDs
- retries
- timeout handling
- response validation
- error propagation
- partial responses
- malformed downstream responses

Ask:

Does this service authenticate the END USER?

Does it merely authenticate itself to the downstream service?

Those are not the same thing.

Determine whether downstream services are expected to enforce ownership and whether that expectation is explicit and testable.

------------------------------------------------------------

D. SESSION / USER OWNERSHIP

Map exactly how:

- user_id
- session_id
- conversation/thread IDs
- request IDs
- agent IDs

are generated, accepted, stored, forwarded and validated.

Look for:

- caller-selected user IDs
- caller-selected session IDs
- session fixation
- cross-user session access
- stale session reuse
- session collision
- missing ownership binding
- inconsistent identifiers across layers
- globally shared state
- process-memory session state
- restart behavior

Do not call a missing local ownership check a full vulnerability if an upstream/downstream service genuinely enforces it.

But do not assume such enforcement without evidence.

------------------------------------------------------------

E. AGENT / TOOL AUTHORITY

Inventory tool-capable or side-effect-capable agent paths.

Determine:

- which agent can call which tools
- whether tool access differs by agent
- whether users can choose more powerful agents
- whether tool calls are validated
- whether arguments are caller/model-controlled
- whether destructive operations exist
- whether tool output is trusted
- whether downstream agents run with credentials

Look for confused-deputy patterns:

untrusted caller
→ backend
→ powerful agent
→ privileged tool

Do not assume a model deciding to call a tool constitutes authorization.

------------------------------------------------------------

F. PROMPT / INSTRUCTION / CONTEXT TRUST

Trace all context entering agents:

- user text
- system prompts
- uploaded context
- files
- manifests
- memory/session data
- retrieved content
- agent instructions
- environment configuration

Ask:

WHAT IS TRUSTED?

WHAT IS UNTRUSTED?

WHAT CAN CHANGE AGENT BEHAVIOR?

WHAT CAN CHANGE TOOL AUTHORITY?

Look for:

- user content accidentally treated as system authority
- instruction override seams
- cross-session context mixing
- unbounded context
- unsafe file contents
- context stored globally
- persistent malicious instructions
- context from one tenant/user reaching another

Do not treat ordinary prompt injection as automatically exploitable.

Tie impact to real tool/data authority.

------------------------------------------------------------

G. LIVE CONTEXT / FILE UPLOADS

If files or live context uploads exist or are scaffolded:

review:

- filename/path handling
- content size limits
- MIME/type assumptions
- temporary storage
- cleanup
- object naming
- user/session ownership
- duplicate uploads
- overwrite behavior
- malicious content handling
- retention
- concurrency
- downstream parsing

If functionality is not implemented, classify issues as FUTURE INTEGRATION RISK rather than current defect.

------------------------------------------------------------

H. CONTEXT CACHING / MEMORY

If caching, session memory, files, or persisted conversation context exist:

determine:

- ownership
- cache key structure
- TTL
- invalidation
- cross-user risk
- stale state
- process-local vs durable persistence
- concurrent updates
- restart behavior
- environment separation

Look for identifiers that are insufficiently namespaced.

Example concern:

session_id alone may be unsafe if ownership also depends on user/tenant identity.

Do not force this concern if the implementation already scopes correctly.

------------------------------------------------------------

I. ASYNC / CONCURRENCY / MULTI-AGENT EXECUTION

Inspect:

- async request handling
- background tasks
- concurrent agent calls
- shared mutable state
- retry loops
- cancellation
- timeouts
- locking/semaphores
- task IDs
- duplicate requests
- race conditions
- response ordering

Ask:

What happens if the user sends twice?

What happens if a downstream call times out after doing work?

What happens if the client retries?

Could a tool side effect execute twice?

Could results return out of order?

Can one request mutate state another request consumes?

------------------------------------------------------------

J. RETRY / TIMEOUT / FAILURE SEMANTICS

Trace failures through every major boundary.

Look for:

- infinite retry
- retrying non-idempotent work
- duplicate agent runs
- duplicate tool execution
- swallowed errors
- generic success after downstream failure
- stale task state
- timeout without cancellation
- local timeout while remote work continues
- failed partial orchestration
- malformed response handling

Distinguish:

REQUEST TIMED OUT

from:

REMOTE WORK WAS CANCELLED.

Those are not equivalent.

------------------------------------------------------------

K. A2A ANTI-LOOP / ORCHESTRATION LIMITS

If turn limits, recursion limits, loop prevention or delegation limits exist:

inspect:

- defaults
- configurability
- enforcement point
- reset behavior
- per-request vs global state
- failure messages
- whether nested/delegated agents can bypass limits

Look for:

- accidental infinite loops
- premature termination
- silently dropped work
- loop counters shared across sessions
- limits enforced only at UI level

------------------------------------------------------------

L. REQUEST VALIDATION

Inspect all request models and route handlers.

Look for:

- arbitrary strings where enums should exist
- unbounded text/context
- missing size limits
- invalid agent IDs
- malformed session IDs
- unexpected nulls
- model/tool names supplied by caller
- dangerous URLs
- numeric overflows/negative limits
- unsupported message structures
- missing schema validation

Do not classify every loose type as a security issue.

Tie it to reachable behavior.

------------------------------------------------------------

M. RESPONSE VALIDATION

Do not assume downstream agent responses are trustworthy.

Inspect:

- parsing
- schema validation
- missing fields
- malformed messages
- oversized responses
- tool-call payloads
- unexpected event types
- error structures
- streaming/chunk handling if present

Look for silent coercion or crashes caused by downstream drift.

------------------------------------------------------------

N. CONFIGURATION / SECRETS

Inspect:

- environment variables
- API keys
- service credentials
- agent endpoint URLs
- ports
- defaults
- dev/prod differences
- secrets printed in logs
- config committed to repository
- fallback credentials
- startup validation

Determine which variables are:

PUBLIC CONFIG

SERVER CONFIG

SECRET

Do not report a server-side environment variable as exposed merely because it exists.

Prove the exposure path.

------------------------------------------------------------

O. CORS / NETWORK EXPOSURE

Inspect:

- CORS policy
- allowed origins
- credentials
- wildcard combinations
- public Cloud Run assumptions
- local development bypasses
- proxy assumptions
- forwarded headers
- direct-origin access

Do not treat CORS as authorization.

If an API is sensitive, server-side identity/authorization must still exist where appropriate.

------------------------------------------------------------

P. LOGGING / PRIVACY

Inspect logs for:

- prompts
- responses
- user IDs
- session IDs
- tokens
- credentials
- uploaded content
- model/tool arguments
- sensitive downstream responses

Ask whether logging can expose cross-user or secret material.

Also determine whether logs contain enough correlation information to debug distributed failures safely.

------------------------------------------------------------

Q. DEPENDENCY / VERSION / CONTRACT DRIFT

Compare:

- installed ADK version
- A2A SDK version
- code assumptions
- manifests
- docs
- tests
- Docker image/runtime
- deployment configs

Look for APIs that changed across versions.

Do not infer breakage solely because a dependency is old/new.

Trace actual usage.

------------------------------------------------------------

R. TEST QUALITY

Do not merely count passing tests.

Determine whether tests cover the dangerous boundaries.

Look for coverage of:

- route authentication
- authorization
- agent allow-listing
- user/session ownership
- malformed requests
- downstream failures
- timeouts
- retries
- concurrency
- duplicated execution
- A2A response drift
- invalid agent
- unavailable downstream agent
- tool authority
- context isolation
- CORS/config
- startup/config failure

Ask:

Are tests validating actual orchestration?

Or only mocked happy paths?

Can every test pass while cross-user session routing is broken?

Can every test pass while a timeout duplicates remote work?

A green suite is evidence, not proof.

------------------------------------------------------------

S. DEPLOYMENT / CLOUD RUN READINESS

Inspect repository evidence for:

- container startup
- port binding
- health endpoints
- graceful shutdown
- concurrency assumptions
- statelessness
- process-local memory
- restart behavior
- multiple instances
- shared persistence
- request timeout
- environment validation

Cloud Run may run multiple instances.

Any correctness model depending on one process's memory should be examined carefully.

Do NOT claim Cloud Run behavior unless the architecture/deployment config supports the claim.

------------------------------------------------------------

T. GCS / VERTEX / MANAGED SERVICES

If represented in this repository, inspect:

- credential authority
- object/resource naming
- user/session scoping
- caller-controlled resource names
- permissions assumptions
- retries
- partial failure
- cleanup
- retention
- cross-environment separation

If not implemented here, explicitly mark as outside current review.

============================================================
7. REVIEW SEQUENCE
============================================================

STEP 1 — MAP

Map:

HTTP/API
→ ADK
→ A2A
→ downstream agents
→ tools/services
→ response

Also map:

user
→ session
→ agent
→ context
→ tool authority

STEP 2 — BASELINE

Run existing safe verification:

- tests
- lint
- type/static checks
- import/startup validation
- other existing project gates

Do not repair broken tooling.

STEP 3 — TRACE PUBLIC ENTRY POINTS

Identify every route and its trust boundary.

STEP 4 — TRACE AGENT ROUTING

Follow agent selection and downstream endpoint resolution.

STEP 5 — TRACE IDENTITY / SESSION

Verify ownership assumptions end to end.

STEP 6 — TRACE TOOL AUTHORITY

Find every place where model/agent behavior can create external effects.

STEP 7 — FAILURE / RETRY / TIMEOUT

Trace distributed failure semantics carefully.

STEP 8 — CONCURRENCY

Examine multi-request and multi-instance behavior.

STEP 9 — CONTEXT / MEMORY / UPLOADS

Trace ownership and isolation.

STEP 10 — TEST FIDELITY

Determine what existing tests fail to prove.

STEP 11 — DEPLOYMENT PASS

Inspect Cloud Run/container/config assumptions.

STEP 12 — BREADTH PASS

Privacy, performance, observability, maintainability.

STEP 13 — CHALLENGE

Try to defeat your important findings.

STEP 14 — COMPRESS

Group common root causes.

STEP 15 — SELF-CRITIQUE

Attack the report before finalizing.

============================================================
8. EVIDENCE MODEL
============================================================

Use:

E0 — HYPOTHESIS

Plausible concern only.

E1 — SOURCE / ARTIFACT

Code/repository evidence establishes the local observation.

E2 — CONTROLLED EXECUTION

Real application code demonstrates behavior under declared mocks,
fixtures, local stubs, injected failures, or controlled execution.

E3 — REAL BOUNDARY / INTEGRATION

A meaningful real boundary was exercised, such as:

- actual local HTTP dispatch
- real A2A server/client boundary
- real container startup
- real locally running downstream agent
- real persistence boundary in a safe environment

E4 — DEPLOYMENT-REPRESENTATIVE

Representative deployed configuration/services/identities were exercised.

Never turn an E1/E2 observation into an E4 claim.

For every consequential finding separate:

DIRECTLY OBSERVED

SOURCE INFERENCE

DOWNSTREAM-SERVICE ASSUMPTIONS

DEPLOYMENT ASSUMPTIONS

============================================================
9. FINDING CLASSIFICATION
============================================================

Classify before severity:

DEFECT

CURRENT SECURITY / RELIABILITY RISK

CONDITIONAL RISK / UNRESOLVED CONCERN

FUTURE INTEGRATION RISK

TRADEOFF

OPTIONAL IMPROVEMENT

VERIFICATION / TOOLING DEFECT

POSITIVE PROTECTION

Do not count optional improvements as defects.

============================================================
10. SEVERITY AND CONFIDENCE
============================================================

SEVERITY:

CRITICAL

Credible current path to broad unauthorized agent/tool authority,
cross-user data compromise, destructive external action, major credential
exposure, or catastrophic system integrity failure.

HIGH

Major security, identity, session-isolation, tool-authority,
data-integrity or availability failure.

MEDIUM

Material but bounded correctness/reliability/integration problem.

LOW

Narrow or readily recoverable defect.

FUTURE GATE

Important architecture issue that must be resolved before a planned
integration/deployment.

UNRATED

Insufficient context.

CONFIDENCE:

HIGH
MODERATE
LOW

Separate:

confidence in local code defect

from

confidence in distributed/deployed consequence

where necessary.

============================================================
11. REQUIRED FINDING FORMAT
============================================================

Every material finding must include:

ID

BOUNDED TITLE

CLASSIFICATION

SEVERITY / FUTURE-GATE LEVEL

CONFIDENCE

EVIDENCE LEVEL

EXACT LOCATION(S)

EXPECTED CONTRACT / INVARIANT

EXECUTION / TRUST / SESSION PATH

DIRECTLY OBSERVED

SOURCE INFERENCE

DOWNSTREAM-SERVICE ASSUMPTIONS

DEPLOYMENT ASSUMPTIONS

USER / SYSTEM IMPACT

TOOL / AUTHORITY IMPACT, IF RELEVANT

FALSIFIER / DOWNGRADE EVIDENCE

ROOT-CAUSE GROUP

For agentic findings explicitly answer where relevant:

- Can this cross users?
- Can this cross sessions?
- Can this select another agent?
- Can this change tool authority?
- Can retry duplicate side effects?
- Does the backend authenticate the user or merely itself?
- Which service is expected to enforce ownership?

============================================================
12. FALSIFIABILITY
============================================================

For every serious finding answer:

"What is the smallest realistic evidence another competent engineer
could provide that would make me withdraw, narrow, or downgrade this?"

Distinguish:

- disproving the local defect
- showing downstream enforcement
- blocking one exploitation path
- lowering practical severity
- proving deployed configuration differs

Do not require proof that the entire distributed system is safe.

============================================================
13. ROOT-CAUSE COMPRESSION
============================================================

Prefer common causes over inflated symptom counts.

Potential themes may include:

- missing API authorization
- caller-controlled identity
- weak session ownership
- agent-routing authority
- trust delegated without explicit contract
- retry/non-idempotency
- process-local state in distributed deployment
- config/manifest drift
- context ownership
- test-harness blind spots

Do not force these groups if unsupported.

============================================================
14. POSITIVE PROTECTIONS
============================================================

Record meaningful safeguards worth preserving.

Examples:

- manifest-constrained agents
- explicit allow-lists
- ownership checks
- bounded timeouts
- loop limits
- schema validation
- safe CORS configuration
- no secret logging
- scoped tools
- correlation IDs
- stateless request handling
- graceful failure
- strong negative tests

Scope positive claims carefully.

============================================================
15. UNDER-REVIEWED AREAS
============================================================

Explicitly identify important areas not adequately verified.

Especially:

- live Hermes agents
- live A2A endpoints
- GCP IAM
- Cloud Run ingress
- GCS
- Vertex AI
- real tool effects
- real multi-instance execution
- production authentication
- live session ownership
- deployed observability

For each state:

AREA
DEPTH ACHIEVED
MISSING EVIDENCE
WHY MISSING
EFFECT ON CONCLUSIONS

Do not treat absent external evidence as either safe or vulnerable.

============================================================
16. MANDATORY SELF-CRITIQUE
============================================================

Before finalizing identify:

1. Three strongest consequential findings.
2. Why they survive skeptical challenge.
3. Three weakest consequential findings.
4. Assumptions making them vulnerable.
5. Severities possibly overstated.
6. Severities possibly understated.
7. Shared root causes.
8. Important under-reviewed areas.
9. Wording that may outrun evidence.
10. What another senior reviewer should challenge first.

If your critique defeats a finding:

withdraw it.

If evidence supports less:

narrow it.

If severity is too high:

downgrade it.

============================================================
17. IMMEDIATE RISK RULE
============================================================

If you discover a plausible CURRENT P0 involving:

- unauthenticated access to powerful agents/tools
- cross-user session/transcript access
- arbitrary downstream endpoint selection
- exposed live credentials
- unrestricted destructive tool invocation
- broad remote code/command execution
- serious cross-tenant/context leakage

DO NOT exploit it.

DO NOT remediate it.

Immediately notify Tony:

POTENTIAL CURRENT P0

Finding:
Evidence:
What is proven:
What is assumed:
Safe containment question:

Continue only if doing so remains safe.

============================================================
18. FINAL REPORT
============================================================

Write:

fable-review/FABLE_CODE_REVIEW.md

Use:

# FABLE CODE REVIEW
## Stark AI Workbench ADK Backend

### 1. Executive Assessment

State whether review was:

- source-only
- source + controlled execution
- integration-assisted
- deployment-assisted

Also state which downstream systems were real, mocked, unavailable or unknown.

### 2. Snapshot and Review Boundary

### 3. Architecture and Trust Map

Show:

caller
→ API
→ ADK
→ A2A
→ downstream agent
→ tools/services

and:

user
→ session
→ agent
→ context
→ authority

### 4. External Integration Map

Classify:

LOCAL
REAL
CONFIGURED BUT UNVERIFIED
MOCK
UNKNOWN

### 5. Verification Baseline

### 6. API / Identity / Authorization Assessment

### 7. Agent Routing / A2A Assessment

### 8. Session / Context / Memory Assessment

### 9. Tool Authority Assessment

### 10. Async / Retry / Timeout / Concurrency Assessment

### 11. Findings Summary

Table:

ID
Title
Classification
Severity/Risk
Confidence
Evidence
Root Cause
Current vs Conditional

### 12. Detailed Findings

### 13. Root-Cause Themes

### 14. Deployment / Cloud Run Assessment

### 15. Positive Protections to Preserve

### 16. Test and Verification Quality

### 17. Concerns / Tradeoffs / Optional Improvements

### 18. Under-Reviewed Areas and Limitations

### 19. Reviewer Self-Critique

### 20. Prioritized Handoff

P0 — immediate current risk
P1 — significant defect/risk
P2 — normal backlog
FUTURE GATE — must be resolved before planned deployment/integration
QUESTION — requires architecture/environment clarification

Do NOT implement remediation.

### 21. Change Boundary Confirmation

List every created file.

Confirm no application source, tests, dependencies, configuration,
external systems or git state were modified.

============================================================
19. FINAL STANDARD
============================================================

The mission is to determine:

- who can call this backend
- how identity is established
- how sessions are owned
- how agents are selected
- what authority agents possess
- where trust crosses service boundaries
- whether retries can duplicate work
- whether state survives safely across requests/instances
- whether context can cross users/sessions
- whether tests protect these boundaries
- what is proven locally
- what depends on downstream enforcement
- what must be fixed before production use

Evidence beats assertion.

Root causes beat symptom counts.

Reproducibility beats confidence.

A distributed trust boundary must be demonstrated, not assumed.

BEGIN.

Verify branch and snapshot.
Create the authorized review workspace.
Map the complete API → ADK → A2A → agent path.
Then review identity, session ownership, agent routing and tool authority before expanding outward.
