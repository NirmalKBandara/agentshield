#!/usr/bin/env bash
set -euo pipefail

# AgentShield GitHub Issue Generator
# Creates 28 GitHub issues (one per development day) in a single run.
#
# Usage:
#   chmod +x create_agentshield_issues.sh
#   gh auth login
#   ./create_agentshield_issues.sh OWNER/REPO
#
# Or, if you are already inside the target git repository:
#   ./create_agentshield_issues.sh
#
# Requirements:
#   - GitHub CLI: https://cli.github.com/
#   - Authenticated `gh` session

REPO="${1:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Install it first, then run: gh auth login"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: GitHub CLI is not authenticated."
  echo "Run: gh auth login"
  exit 1
fi

if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
fi

if [[ -z "$REPO" ]]; then
  echo "Error: Could not determine the repository."
  echo "Usage: $0 OWNER/REPO"
  exit 1
fi

echo "Target repository: $REPO"
echo

# ---------- Labels ----------
ensure_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  if gh label list --repo "$REPO" --limit 200 --json name -q '.[].name' | grep -Fxq "$name"; then
    return
  fi

  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --description "$description" >/dev/null
}

echo "Ensuring labels exist..."
ensure_label "week-1" "1D76DB" "Week 1 - Basic AI application"
ensure_label "week-2" "5319E7" "Week 2 - AgentShield security engine"
ensure_label "week-3" "A371F7" "Week 3 - Security dashboard and attack lab"
ensure_label "week-4" "0E8A16" "Week 4 - Testing, DevSecOps, and portfolio polish"
ensure_label "frontend" "FBCA04" "Frontend work"
ensure_label "backend" "0052CC" "Backend work"
ensure_label "database" "006B75" "Database work"
ensure_label "ai-agent" "D876E3" "AI agent implementation"
ensure_label "security" "D73A4A" "Security control or security engineering task"
ensure_label "testing" "BFD4F2" "Testing task"
ensure_label "devops" "0E8A16" "DevOps / CI/CD work"
ensure_label "documentation" "C5DEF5" "Documentation task"
ensure_label "red-team" "B60205" "Attack simulation / red-team work"
ensure_label "mvp" "F9D0C4" "AgentShield MVP"
echo "Labels ready."
echo

# ---------- Issue creation helper ----------
create_issue() {
  local title="$1"
  local labels="$2"
  local body="$3"

  echo "Creating: $title"

  # Skip if an issue with exactly the same title already exists.
  local existing
  existing="$(gh issue list --repo "$REPO" --state all --limit 500 \
    --json title -q ".[] | select(.title == \"$title\") | .title" 2>/dev/null || true)"

  if [[ "$existing" == "$title" ]]; then
    echo "  -> skipped (already exists)"
    return
  fi

  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --body "$body" \
    --label "$labels" >/dev/null

  echo "  -> created"
}

# ---------- Week 1 ----------
create_issue \
"Day 01 — Project Setup & Repository Structure" \
"week-1,mvp,backend,frontend,devops" \
"## Objective
Set up the AgentShield project so the frontend, backend, and development workflow are ready.

## Tasks
- [ ] Create the GitHub repository
- [ ] Create \`frontend/\`, \`backend/\`, \`docs/\`, and \`tests/\`
- [ ] Initialize Next.js + TypeScript frontend
- [ ] Initialize FastAPI backend
- [ ] Add environment-variable templates
- [ ] Add \`.gitignore\`
- [ ] Add starter \`README.md\`
- [ ] Confirm frontend can call a backend health endpoint
- [ ] Commit and push the initial project structure

## Definition of Done
- [ ] Frontend runs locally
- [ ] Backend runs locally
- [ ] \`GET /health\` returns success
- [ ] Frontend successfully reaches backend
- [ ] Clean initial commit exists on GitHub"

create_issue \
"Day 02 — PostgreSQL Database & Core Models" \
"week-1,mvp,backend,database" \
"## Objective
Add persistent storage for AgentShield.

## Tasks
- [ ] Configure PostgreSQL
- [ ] Add database connection from FastAPI
- [ ] Create initial models/tables for users
- [ ] Create agents table
- [ ] Create tools table
- [ ] Create agent_permissions table
- [ ] Create tool_calls table
- [ ] Create security_events table
- [ ] Create policies table
- [ ] Add migration support
- [ ] Test basic create/read operations

## Definition of Done
- [ ] Backend connects to PostgreSQL
- [ ] Initial schema is reproducible
- [ ] A test record can be inserted and queried
- [ ] Database configuration is documented"

create_issue \
"Day 03 — Build the Demo AI Agent" \
"week-1,mvp,backend,ai-agent" \
"## Objective
Create a simple tool-using AI agent that can interpret user requests and decide when a tool should be called.

## Tasks
- [ ] Choose local model/provider for MVP
- [ ] Create agent service/module
- [ ] Add basic system instructions
- [ ] Define a structured tool-call format
- [ ] Parse model tool-call output safely
- [ ] Add error handling for invalid model output
- [ ] Test with simple requests such as 'Show customer 1002'

## Definition of Done
- [ ] Agent accepts a natural-language prompt
- [ ] Agent can select a tool
- [ ] Agent can produce structured tool arguments
- [ ] Invalid model output fails safely"

create_issue \
"Day 04 — Implement Demo Tools" \
"week-1,mvp,backend,ai-agent" \
"## Objective
Create controlled demo tools that later become security targets for AgentShield.

## Tasks
- [ ] Implement \`get_customer(customer_id)\`
- [ ] Implement \`send_email(to, message)\`
- [ ] Implement \`issue_refund(order_id, amount)\`
- [ ] Implement \`fetch_url(url)\`
- [ ] Use fake/demo data only
- [ ] Add clear tool schemas
- [ ] Add input validation at the tool layer
- [ ] Write simple unit tests for each tool

## Definition of Done
- [ ] All four tools work
- [ ] Each tool has a defined schema
- [ ] No real customer/payment data is used
- [ ] Tests cover normal tool execution"

create_issue \
"Day 05 — Connect AI Agent to Tool Calling" \
"week-1,mvp,backend,ai-agent" \
"## Objective
Complete the initial insecure agent flow before adding AgentShield.

## Tasks
- [ ] Connect agent decisions to the tool registry
- [ ] Execute selected tool with structured arguments
- [ ] Return tool result to the agent/user
- [ ] Capture tool name and arguments
- [ ] Add graceful handling for unknown tools
- [ ] Test several normal requests end-to-end

## Expected Flow
\`User -> AI Agent -> Tool -> Result\`

## Definition of Done
- [ ] Natural-language request can trigger a tool
- [ ] Tool executes and returns a result
- [ ] Unknown tools cannot execute
- [ ] End-to-end demo works"

create_issue \
"Day 06 — Build the Agent Playground UI" \
"week-1,mvp,frontend,ai-agent" \
"## Objective
Create the main UI used to interact with and demonstrate the AI agent.

## Tasks
- [ ] Create Agent Playground page
- [ ] Add prompt input
- [ ] Add submit/run action
- [ ] Show AI response
- [ ] Show requested tool
- [ ] Show tool arguments
- [ ] Show tool response
- [ ] Add loading/error states
- [ ] Make layout clean enough for demo use

## Definition of Done
- [ ] User can interact with the agent from the browser
- [ ] Tool-call details are visible
- [ ] Backend errors are displayed cleanly"

create_issue \
"Day 07 — Week 1 Integration Review" \
"week-1,mvp,testing" \
"## Objective
Stabilize the complete basic AI application before building security controls.

## Tasks
- [ ] Test frontend-to-backend communication
- [ ] Test backend-to-database communication
- [ ] Test AI-agent requests
- [ ] Test all demo tools
- [ ] Test tool calling end-to-end
- [ ] Fix blocking bugs
- [ ] Clean configuration and environment files
- [ ] Update README setup instructions
- [ ] Tag or note Week 1 milestone

## Definition of Done
- [ ] Full insecure flow works reliably
- [ ] Setup works from clean instructions
- [ ] No known blocker remains for Week 2"

# ---------- Week 2 ----------
create_issue \
"Day 08 — Create the AgentShield Security Gateway" \
"week-2,mvp,backend,security" \
"## Objective
Insert AgentShield between the AI agent and every tool execution.

## Tasks
- [ ] Create gateway module
- [ ] Define security request/context object
- [ ] Define security decision response
- [ ] Support ALLOW/BLOCK decisions
- [ ] Include reason and risk information
- [ ] Ensure tools cannot be called without passing through gateway
- [ ] Add unit tests for gateway flow

## Expected Flow
\`AI Agent -> AgentShield -> ALLOW/BLOCK -> Tool\`

## Definition of Done
- [ ] Every tool call passes through AgentShield
- [ ] Gateway can block execution
- [ ] Gateway returns a machine-readable decision"

create_issue \
"Day 09 — Tool Permission Validation" \
"week-2,mvp,backend,security" \
"## Objective
Prevent agents from using tools they are not authorized to execute.

## Tasks
- [ ] Define agent-to-tool permission model
- [ ] Load permissions from database/config
- [ ] Check requested tool before execution
- [ ] Block unauthorized tools
- [ ] Return clear denial reason
- [ ] Record permission denials
- [ ] Test support-agent cannot call \`issue_refund\`

## Definition of Done
- [ ] Authorized tool call is allowed
- [ ] Unauthorized tool call is blocked
- [ ] Decision is logged
- [ ] Tests cover allow and deny cases"

create_issue \
"Day 10 — Tool Parameter Validation" \
"week-2,mvp,backend,security" \
"## Objective
Stop dangerous tool calls even when the tool itself is permitted.

## Tasks
- [ ] Define per-tool parameter schemas
- [ ] Validate types and required fields
- [ ] Add business/security constraints
- [ ] Add refund amount threshold
- [ ] Reject unexpected parameters
- [ ] Return useful security reason
- [ ] Test oversized refund attempt

## Definition of Done
- [ ] Invalid arguments are blocked
- [ ] Dangerous but valid-looking arguments can be blocked by policy
- [ ] Tests cover edge cases"

create_issue \
"Day 11 — SSRF & URL Validation Protection" \
"week-2,mvp,backend,security" \
"## Objective
Protect URL-fetching tools against SSRF and unsafe URL schemes.

## Tasks
- [ ] Validate URL scheme
- [ ] Allow only HTTP/HTTPS
- [ ] Block localhost
- [ ] Block loopback ranges
- [ ] Block RFC1918 private ranges
- [ ] Block link-local addresses
- [ ] Block cloud metadata address \`169.254.169.254\`
- [ ] Handle hostname resolution safely
- [ ] Add tests for bypass attempts

## Definition of Done
- [ ] Public safe URL can pass
- [ ] Internal/private target is blocked
- [ ] Metadata endpoint is blocked
- [ ] SSRF security events are logged"

create_issue \
"Day 12 — PII Detection & Masking" \
"week-2,mvp,backend,security" \
"## Objective
Detect sensitive data before it is exposed through AI/tool actions.

## Tasks
- [ ] Define initial PII categories
- [ ] Detect email addresses
- [ ] Detect phone numbers
- [ ] Detect credit-card-like values
- [ ] Detect API keys/secrets using conservative patterns
- [ ] Add masking/redaction function
- [ ] Add configurable block vs mask action
- [ ] Test attempted external data exfiltration

## Definition of Done
- [ ] PII can be detected
- [ ] Sensitive values can be masked
- [ ] High-risk exfiltration can be blocked
- [ ] Detection reason is logged"

create_issue \
"Day 13 — Prompt Injection Detection" \
"week-2,mvp,backend,security" \
"## Objective
Implement practical prompt-injection detection without building a custom ML model.

## Tasks
- [ ] Define suspicious instruction patterns
- [ ] Detect instruction-override attempts
- [ ] Detect system-prompt extraction attempts
- [ ] Detect obvious data-exfiltration requests
- [ ] Combine signals into a risk score
- [ ] Return detected indicators
- [ ] Add false-positive tests
- [ ] Test malicious prompt examples

## Definition of Done
- [ ] Known attack prompts are detected
- [ ] Normal prompts are not routinely blocked
- [ ] Detection contributes to risk score
- [ ] Findings are visible in security decision"

create_issue \
"Day 14 — Rate Limiting & Audit Logging" \
"week-2,mvp,backend,security,database" \
"## Objective
Limit abusive agent activity and create a complete security audit trail.

## Tasks
- [ ] Add per-user/agent request limits
- [ ] Add tool-call rate limits
- [ ] Return clean 429/blocked response
- [ ] Store security-event timestamp
- [ ] Store user/agent identity
- [ ] Store requested tool and sanitized arguments
- [ ] Store decision
- [ ] Store risk score
- [ ] Store reason/policy
- [ ] Avoid logging secrets in plaintext

## Definition of Done
- [ ] Excessive requests are blocked
- [ ] Security decisions persist in PostgreSQL
- [ ] Sensitive values are sanitized before logging"

# ---------- Week 3 ----------
create_issue \
"Day 15 — Security Dashboard" \
"week-3,mvp,frontend,database" \
"## Objective
Create the main security overview page.

## Tasks
- [ ] Add total requests metric
- [ ] Add allowed requests metric
- [ ] Add blocked requests metric
- [ ] Add high-risk events metric
- [ ] Show most attacked tool
- [ ] Show most common attack category
- [ ] Add recent security-events table
- [ ] Connect metrics to backend/database

## Definition of Done
- [ ] Dashboard uses real application data
- [ ] Security status is understandable at a glance
- [ ] Page is suitable for an interview demo"

create_issue \
"Day 16 — Security Events Page" \
"week-3,mvp,frontend,security" \
"## Objective
Provide detailed inspection of detected/blocked security events.

## Tasks
- [ ] Create \`/security-events\`
- [ ] Show event ID
- [ ] Show timestamp
- [ ] Show threat category
- [ ] Show risk level/score
- [ ] Show tool
- [ ] Show ALLOW/BLOCK decision
- [ ] Show reason
- [ ] Add event detail view
- [ ] Add basic filtering

## Definition of Done
- [ ] Events are retrieved from the backend
- [ ] User can inspect why an action was blocked"

create_issue \
"Day 17 — Tool Calls Page" \
"week-3,mvp,frontend,database" \
"## Objective
Make agent tool usage transparent and auditable.

## Tasks
- [ ] Create \`/tool-calls\`
- [ ] Show agent identity
- [ ] Show tool name
- [ ] Show sanitized arguments
- [ ] Show decision
- [ ] Show risk score
- [ ] Show timestamp
- [ ] Add filter by tool/decision
- [ ] Link blocked calls to security events

## Definition of Done
- [ ] Every relevant tool call is visible
- [ ] Sensitive values remain masked
- [ ] Blocked calls can be investigated"

create_issue \
"Day 18 — Agent Security Policies Page" \
"week-3,mvp,frontend,backend,security" \
"## Objective
Allow security policies to be viewed and edited through the web interface.

## Tasks
- [ ] Create \`/policies\`
- [ ] List agents
- [ ] List tools per agent
- [ ] Show allowed/denied state
- [ ] Add simple permission editing
- [ ] Persist policy changes
- [ ] Validate policy updates in backend
- [ ] Show clear success/error state

## Definition of Done
- [ ] Tool permissions can be changed from UI
- [ ] Changes immediately affect AgentShield decisions"

create_issue \
"Day 19 — Red Team Attack Simulation Lab" \
"week-3,mvp,frontend,red-team,security" \
"## Objective
Create a repeatable attack lab for demonstrating AgentShield defenses.

## Tasks
- [ ] Create \`/red-team\`
- [ ] Add prompt-injection scenario
- [ ] Add unauthorized-tool scenario
- [ ] Add PII-exfiltration scenario
- [ ] Add SSRF scenario
- [ ] Add rate-limit abuse scenario
- [ ] Add dangerous-parameter scenario
- [ ] Add Run Attack action
- [ ] Show ALLOWED/BLOCKED result
- [ ] Show reasons and risk score

## Definition of Done
- [ ] Six attack scenarios can be executed
- [ ] Results are recorded as security events
- [ ] Page can be used directly during interviews"

create_issue \
"Day 20 — Risk Scoring Engine" \
"week-3,mvp,backend,security" \
"## Objective
Combine security signals into a simple explainable risk score.

## Tasks
- [ ] Define scoring weights
- [ ] Add prompt-injection contribution
- [ ] Add unauthorized-tool contribution
- [ ] Add PII-exposure contribution
- [ ] Add SSRF contribution
- [ ] Add rate-abuse contribution
- [ ] Cap score to 0-100
- [ ] Map score to LOW/MEDIUM/HIGH/CRITICAL
- [ ] Return contributing reasons
- [ ] Add unit tests

## Definition of Done
- [ ] Risk score is deterministic
- [ ] Risk level is explainable
- [ ] Dashboard/events display the score"

create_issue \
"Day 21 — UI/UX Cleanup & Week 3 Review" \
"week-3,mvp,frontend,testing" \
"## Objective
Make all MVP screens consistent, readable, and demo-ready.

## Tasks
- [ ] Finalize navigation
- [ ] Clean dashboard spacing and states
- [ ] Clean Agent Playground
- [ ] Clean Security Events
- [ ] Clean Tool Calls
- [ ] Clean Policies
- [ ] Clean Red Team Lab
- [ ] Add Audit Logs navigation/page if not already present
- [ ] Fix obvious responsive issues
- [ ] Run complete Week 3 regression test

## Definition of Done
- [ ] All core pages are usable
- [ ] No broken navigation
- [ ] Main attack/demo scenarios work from UI"

# ---------- Week 4 ----------
create_issue \
"Day 22 — STRIDE Threat Model & Architecture Review" \
"week-4,mvp,security,documentation" \
"## Objective
Document how AgentShield is threatened and how the architecture responds.

## Tasks
- [ ] Draw system/data-flow architecture
- [ ] Identify trust boundaries
- [ ] Analyze Spoofing threats
- [ ] Analyze Tampering threats
- [ ] Analyze Repudiation threats
- [ ] Analyze Information Disclosure threats
- [ ] Analyze Denial of Service threats
- [ ] Analyze Elevation of Privilege threats
- [ ] Map threats to implemented controls
- [ ] Add remaining risks/limitations

## Definition of Done
- [ ] \`docs/threat-model.md\` exists
- [ ] STRIDE covers the actual application
- [ ] Architecture diagram matches implementation"

create_issue \
"Day 23 — Unit Test Security Controls" \
"week-4,mvp,testing,security" \
"## Objective
Build automated tests for the core security engine.

## Tasks
- [ ] Test prompt-injection detection
- [ ] Test PII detection/masking
- [ ] Test tool permissions
- [ ] Test parameter validation
- [ ] Test SSRF protection
- [ ] Test rate limiting
- [ ] Test risk scoring
- [ ] Add negative/false-positive cases
- [ ] Make test output easy to run locally

## Definition of Done
- [ ] Core security controls have automated tests
- [ ] Test suite passes consistently"

create_issue \
"Day 24 — End-to-End Security Integration Tests" \
"week-4,mvp,testing,security,red-team" \
"## Objective
Verify attacks are stopped through the complete system, not only individual functions.

## Tasks
- [ ] Test normal allowed tool flow
- [ ] Test unauthorized tool end-to-end
- [ ] Test prompt injection end-to-end
- [ ] Test PII exfiltration end-to-end
- [ ] Test SSRF end-to-end
- [ ] Test dangerous parameter end-to-end
- [ ] Test rate limiting end-to-end
- [ ] Confirm security event is stored for blocked actions

## Definition of Done
- [ ] Critical flows pass integration tests
- [ ] Every blocked attack produces an auditable event"

create_issue \
"Day 25 — Dockerize AgentShield" \
"week-4,mvp,devops" \
"## Objective
Make the MVP easy to start consistently.

## Tasks
- [ ] Add frontend Dockerfile
- [ ] Add backend Dockerfile
- [ ] Add PostgreSQL service
- [ ] Create/update \`docker-compose.yml\`
- [ ] Add environment handling
- [ ] Add health checks where useful
- [ ] Test clean startup
- [ ] Document Docker setup

## Definition of Done
- [ ] \`docker compose up\` starts the required stack
- [ ] App works after a clean build"

create_issue \
"Day 26 — GitHub Actions DevSecOps Pipeline" \
"week-4,mvp,devops,security,testing" \
"## Objective
Add a small but meaningful security-focused CI pipeline.

## Tasks
- [ ] Run backend tests on push/PR
- [ ] Run frontend checks/build
- [ ] Add dependency audit
- [ ] Add Semgrep or equivalent SAST
- [ ] Add Gitleaks secret scanning
- [ ] Add Trivy where appropriate
- [ ] Fail pipeline for meaningful security/test failures
- [ ] Keep workflow understandable and maintainable

## Definition of Done
- [ ] GitHub Actions runs automatically
- [ ] Tests and selected security scans execute
- [ ] Pipeline status is visible in repository"

create_issue \
"Day 27 — Final Documentation & README" \
"week-4,mvp,documentation" \
"## Objective
Make the project understandable to recruiters, interviewers, and developers.

## Tasks
- [ ] Write project overview
- [ ] Explain AI-agent security problem
- [ ] Add architecture diagram
- [ ] Document seven core security controls
- [ ] Document installation
- [ ] Document demo workflow
- [ ] Document attack scenarios
- [ ] Document API where useful
- [ ] Add screenshots
- [ ] Add known limitations
- [ ] Add \`docs/architecture.md\`
- [ ] Add \`docs/security-controls.md\`
- [ ] Add \`docs/attack-scenarios.md\`

## Definition of Done
- [ ] Someone can understand and run the project from README
- [ ] Security design is clearly documented"

create_issue \
"Day 28 — Final Demo, Cleanup & MVP Release" \
"week-4,mvp,testing,documentation" \
"## Objective
Finish the one-month MVP and prepare it for portfolio/interview use.

## Tasks
- [ ] Run normal customer lookup demo
- [ ] Run unauthorized refund demo
- [ ] Run prompt-injection + exfiltration demo
- [ ] Run SSRF metadata-target demo
- [ ] Show resulting dashboard/security events
- [ ] Fix final demo-breaking bugs
- [ ] Remove unused/debug code
- [ ] Verify no secrets are committed
- [ ] Verify clean installation
- [ ] Capture final screenshots
- [ ] Prepare 5-10 minute interview demonstration
- [ ] Create MVP release/tag

## Definition of Done
- [ ] Working web application
- [ ] Working AI agent
- [ ] AgentShield security gateway
- [ ] Seven core security controls
- [ ] Security dashboard
- [ ] Red-team attack simulator
- [ ] PostgreSQL audit trail
- [ ] Dockerized stack
- [ ] CI/CD security pipeline
- [ ] Automated tests
- [ ] STRIDE threat model
- [ ] Professional README
- [ ] Interview-ready demo"

echo
echo "Done. AgentShield 28-day issue plan created in: $REPO"
echo "View issues with:"
echo "  gh issue list --repo \"$REPO\" --limit 100"
