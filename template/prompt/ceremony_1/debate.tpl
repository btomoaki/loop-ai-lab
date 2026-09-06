[INST]
=== 1. REPOSITORY & DEV RULES ===
{rules}

=== 2. SYSTEM SPECIFICATIONS ===
{specs}

=== 3. MULTI-PERSONA INSTRUCTIONS ===
{personas}

=== 4. TARGET DEVELOPER AGENT PROFILE (DOWNSTREAM CODER) ===
{target_agent}

=== 5. EXECUTION INSTRUCTIONS ===
- {inst_file_rel}

[TASK: CEREMONY 1 EPIC REFINEMENT DEBATE]
Analyze all referenced specification files and conduct a debate among the personas to establish architecture and decompose Epics.

Output MUST follow this format:
# Overall System Architecture & Epic Refinement Debate Log

## 1. System Architecture Debate (PO, Architect, FinOps, Spec Auditor, Capacity Guardian, DevOps, Ruler)
- **[PO Persona]**: Discusses product scope, user workflows, and core features from references/icon_generator.md.
- **[Architect Persona]**: Champions Clean Architecture 4-layer boundaries, domain logic purity, testability, and GCP Cloud Run stateless architecture as inviolable internal quality criteria (DoD).
- **[FinOps & Cost Governance Persona]**: Mandates minimal operational overhead and strictly VETOES and ELIMINATES unauthorized features (e.g. unrequested Rate Limiting, unnecessary external DBs/auth, heavy libraries) from Epic titles and scopes. [GUARDRAIL]: Clean Architecture layer separation and testing are internal quality (DoD) and MUST NOT be stripped.
- **[Spec Compliance Persona]**: Audits and vetoes any dropped requirements from references/icon_generator.md, while validating that cloud/container Platform Contracts (dynamic $PORT, /healthz, SIGTERM 10s drain) are preserved.
- **[Capacity Guardian Persona]**: Analyzes the downstream Coder model profile and enforces modular Epic sizing that prevents context overflow.
- **[Platform & DevOps Persona]**: Discusses Docker containerization, Makefile targets, and GitHub Actions CI/CD.
- **[Ruler Persona (Discipline & Policy Controller)]**: Enforces .agents/rules/ and GEMINI.md with absolute rigor. Mandates Shift-Left Containerization (Epic 1 must prioritize compose.yaml), prohibits host toolchain pollution (all test/lint verify_commands must run inside Docker containers), enforces pure struct models with zero logic/methods/tests in internal/domain/model/, and mandates canonical go mod init. Strict prohibition on invented features like Rate Limiting.

## 2. Epic Breakdown
(Decompose the application into modular, self-contained Epics: Epic 1, Epic 2, ... covering core logic, image rendering, HTTP API, Web UI, and CI/CD/Docker delivery)
- **Epic 1 <Title>**:
  - **Description**: <Technical explanation of what to build>
  - **Objective**: <Business/functional value of what we want to achieve>
  - **Background & Motivation**: <Why this epic is needed and its value>
  - **Scope**: <Functional and technical scope>
  - **Dependencies**: <List of prerequisite Epics or 'None (Root Foundation)'>
  - **Acceptance Criteria (AC)**: <Testable requirements>
  - **Definition of Done (DoD)**: <Unit tests, code coverage, zero lint errors, buildable artifact>
  - **Target Personas for Detailed Design**: <List of relevant personas for this specific epic>
  - **Isolated Epic Specification**: <Full technical specification, schemas, models, logic details for this epic isolated from other epics>
[/INST]
