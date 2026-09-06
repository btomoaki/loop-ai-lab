# ⚙️ Scrum Ceremonies & Governance Rules

## 1. 🎯 Autonomous Scrum Ceremony Lifecycle
The pipeline consists of the following 3 autonomous ceremonies:

1. **Epic Refinement (Ceremony 1)**:
   - Analyzes system specification documents (`references/*.md`) and conducts overall multi-persona architecture debate to extract single-responsibility Epics (`epic_1` to `epic_N`).
2. **Sprint Backlog Refinement (Ceremony 2)**:
   - Conducts multi-persona refinement for each Epic to generate single-responsibility task definitions (`sprint_x_backlog.yaml`) and automated test harnesses (`sprint_x_harness.sh`).
3. **Sprint Execution & Review Gate (Ceremony 3)**:
   - Executes autonomous TDD implementation loops (Red ➔ Green) and validates DoD compliance using automated test harnesses.

## 2. 🚥 DoR (Definition of Ready Rules)
Prerequisites for initiating TDD implementation in Sprint Execution:

1. **Strict Acceptance Criteria Limit (Acceptance Criteria <= 2)**:
   - Each task MUST have **at most 2 Acceptance Criteria** ensuring single responsibility. (Tasks with 3+ criteria MUST be split during refinement).
   - **Exclusion of NFRs**: Non-functional requirements (NFRs) like performance or security are validated during DoD rather than cluttering AC.
2. **Capacity & Story Point Limits (Capacity Guardian)**:
   - Any task estimated at **>=8 Story Points** MUST be immediately decomposed into smaller micro-tasks (1-5 SP).
3. **Explicit Physical File Paths**:
   - Every task MUST specify explicit target file paths for creation or modification.
4. **Explicit Dependencies (`depends_on`)**:
   - Every task MUST explicitly declare its dependency array (`depends_on: ["TASK-X.Y"]` or `depends_on: []`).
5. **Read-Only System Specifications (`references/*`)**:
   - `references/*` files are strictly **READ-ONLY Single Source of Truth**. AI agents MUST NEVER create tasks to edit, delete, or rewrite files in `references/`.
6. **Mandatory Documentation Task**:
   - The final task of an initiative's backlog MUST be a dedicated documentation task (e.g. API contract specifications like `docs/openapi.yaml` or feature documentation).
   - [REPOSITORY README ALLOCATION]: Comprehensive repository documentation (`README.md`) meeting all criteria in `developer_standards.md` is architecturally allocated to the final operational documentation epic (Epic 7). In intermediate epics, documentation tasks are scoped strictly to the architectural artifacts introduced in that epic, preventing premature scope creep.
7. **Automated Test Harness**:
   - Each sprint backlog MUST have a corresponding `sprint_x_harness.sh` script for objective verification.
8. **Strict YAML Quoting Governance (Mandatory String Quoting)**:
   - All string values within `epic_backlog.yaml`—especially `verify_command`, `title`, and items in `acceptance_criteria`—MUST be explicitly enclosed in double quotes (`"..."`).
   - Unquoted strings containing colons followed by spaces (e.g. `: `, CSS properties like `width: 250px`, or regex patterns) cause fatal YAML parser collisions and are strictly prohibited.

## 3. 🚫 No Ad-Hoc Design Modifications Rule (CRITICAL)
- **System Architecture Consistency Guarantee**:
  - Ad-hoc design changes or specification additions during Sprint Execution are strictly forbidden.
  - The Sprint Review Gate evaluates only Pass/Fail against DoD criteria (100% harness pass, Clean Architecture 4-layer structure, security standards).
- **Refinement Rollback Directive**:
  - If critical spec contradictions are discovered during development, rollback to Ceremony 1 or Ceremony 2 refinement to maintain systemic architecture consistency.

## 4. 📂 Ceremony Artifact Map
Official artifact paths generated and maintained across ceremonies:

- **Ceremony 1 (Epic Refinement)**:
  - `state/.evaluator/overall_debate_log.md` (Overall Architecture Debate & Epics List)
- **Ceremony 2 (Sprint Backlog Refinement)**:
  - `state/initiatives/epic_X/debate_log.md` (Epic Multi-Persona Debate)
  - `state/initiatives/epic_X/epic_backlog.yaml` (Epic Backlog)
  - `state/initiatives/epic_X/sprint_N_backlog.yaml` (Sprint Task Definitions)
  - `state/initiatives/epic_X/sprint_N_harness.sh` (Automated Verification Test Harness)
- **Ceremony 3 (Sprint Execution & Review Gate)**:
  - `workspace/<project_name>/...` (Source Code & Unit Tests)
  - `state/initiatives/epic_X/sprint_N_review_gate.md` (DoD Review Gate Log)

## 5. 📊 Ticket Story Point Matrix & Capacity Governance

### Ticket Story Point Matrix
Story points are estimated exclusively at the individual **Ticket/Task** level.

* **5 pt**: Domain core design and critical interface modeling
* **4 pt**: CI/CD pipeline setup, public cloud release design, initial alert setup
* **3 pt**: Dependency Wiring (DI Wiring) assembly
* **2 pt**: Unit test implementation (1 file), Docker Compose setup
* **1 - 2 pt**: Single business logic usecase implementation
* **1 pt**: API implementation (2 endpoints), Dockerization, basic alerts

### Capacity Governance Hard Rules
1. **8pt+ Ticket Decomposition Rule**:
   - Any ticket estimated at **8pt or higher** MUST be immediately decomposed into smaller tickets during Ceremony 2.
2. **Task-Level Single-Responsibility Principle**:
   - Decompositions must be driven by cohesive domain boundaries, single-responsibility principle (SRP), and downstream Coder context capacity (each task ≤ 5 SP, ≤ 2 ACs), strictly prohibiting artificial hardcoded limits on the total number or total points across a sprint.


---

## 🚨 6. Escalation Protocol for Missing Specifications & Rule Corruption
- **No Guessing or Fabricating Features**: If specification documents (`references/*`) are missing, empty, or completely ambiguous, the team and all AI agents MUST NOT invent speculative generic features (such as generic login, payment, or unrelated templates).
- **Rule Corruption & Fatal Policy Conflict**: If the Ruler Persona detects fatal contradictions across `.agents/rules/` or unexecutable mandates, the team MUST NOT perform silent workarounds or mock fallbacks.
- **Mandatory Escalation Halt**: The Scrum Master, Spec Compliance Auditor, or Ruler Persona MUST immediately halt refinement/execution and issue an explicit escalation to the human stakeholder requesting resolution.
