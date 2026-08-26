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
   - **Exclusion of NFRs**: Non-functional requirements (NFRs) like performance or security are excluded from DoR and validated during DoD.
2. **Explicit Physical File Paths**:
   - Every task MUST specify explicit target file paths for creation or modification.
3. **Automated Test Harness**:
   - Each task MUST have a corresponding `sprint_x_harness.sh` script for objective verification.

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
* **3 pt**: DI container assembly and wiring
* **2 pt**: Unit test implementation (1 file), Docker Compose setup
* **1 - 2 pt**: Single business logic usecase implementation
* **1 pt**: API implementation (2 endpoints), Dockerization, basic alerts

### Capacity Governance Hard Rules
1. **8pt+ Ticket Decomposition Rule**:
   - Any ticket estimated at **8pt or higher** MUST be immediately decomposed into smaller tickets during Ceremony 2.
2. **1-Sprint Capacity Limit Rule**:
   - The total story points assigned to a single sprint backlog (`sprint_x_backlog.yaml`) MUST NOT exceed **3-4 points (Max 5 points)**. Overbudget tickets must be deferred to subsequent sprints.

