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

## 1. System Architecture Debate (Facilitated by Scrum Master)
- **[Scrum Master Persona]**: Opens the refinement session as neutral agile facilitator. Establishes session objectives, ground rules, and timeboxing. Sets the multi-persona collaboration flow between PO, Architect, and FinOps/DevOps.
- **[PO Persona]**: Discusses product scope, user workflows, and core features from references/icon_generator.md.
- **[Architect Persona]**: Champions Clean Architecture 4-layer boundaries, domain logic purity, testability, and GCP Cloud Run stateless architecture as inviolable internal quality criteria (DoD). Mandates Double-Mockability for 100% Unit Testability with explicit layout:
  - `internal/domain/model/`: Pure structs (`AvatarSpec`, `Grid`, `ColorRGB`) with exported fields only (Zero logic, methods, or tests).
  - `internal/domain/service/`: Stateless pure algorithms (MD5 hash, 5x5 symmetric grid, RGB color extraction) + Unit Tests.
  - `internal/domain/rasterizer.go`: Output Port interface (`type Rasterizer interface`) owned by domain.
  - `internal/domain/usecase/avatar_usecase.go`: Input Port interface (`type AvatarUsecase interface`) owned by domain for 100% controller mockability.
  - `internal/application/usecase/avatar_usecase.go`: Concrete usecase orchestrator (`type avatarUsecase struct`) depending on `domain.Rasterizer` for 100% usecase mockability.
  - `internal/infrastructure/png/`: Concrete rasterizer implementing `domain.Rasterizer` using Go standard library (`image/png`).
  - `internal/delivery/http/`: HTTP handlers (`AvatarHandler`, `HealthHandler`, `StaticHandler`) depending exclusively on `domain.usecase.AvatarUsecase`. (Strictly prohibited to name package `interface` due to Go reserved keyword).
- **[FinOps & Cost Governance Persona]**: Mandates minimal operational overhead and strictly VETOES and ELIMINATES unauthorized features (e.g. unrequested Rate Limiting, unnecessary external DBs/auth, heavy libraries) from Epic titles and scopes. [GUARDRAIL]: Clean Architecture layer separation and testing are internal quality (DoD) and MUST NOT be stripped.
- **[Spec Compliance Persona]**: Audits and vetoes any dropped requirements from references/icon_generator.md, while validating that cloud/container Platform Contracts (dynamic $PORT, /healthz, SIGTERM 10s drain) are preserved.
- **[Capacity Guardian Persona]**: Analyzes the downstream Coder model profile and enforces modular Epic sizing that prevents context overflow.
- **[Platform & DevOps Persona]**: Discusses Docker containerization, Makefile targets, and GitHub Actions CI/CD.
- **[Ruler Persona (Discipline & Policy Controller)]**: Enforces .agents/rules/ and GEMINI.md with absolute rigor. Mandates Shift-Left Containerization (Epic 1 must prioritize compose.yaml), prohibits host toolchain pollution (all test/lint verify_commands must run inside Docker containers), enforces pure struct models with zero logic/methods/tests in internal/domain/model/, and mandates canonical go mod init. Strict prohibition on invented features like Rate Limiting. **Strict prohibition on premature source code implementation**: Do NOT output full code blocks (e.g. full Dockerfiles, full Go handlers/servers, full HTML/JS). Focus strictly on package structures, interface signatures, and acceptance boundaries. Full implementation belongs strictly to Ceremony 3.
- **[Scrum Master Persona]**: Summarizes final architectural consensus, validates that all personas are aligned with no unaddressed vetoes, and formally approves Ceremony 1 completion.

## 2. Epic Breakdown
(Decompose the application into modular, self-contained Epics: Epic 1, Epic 2, ... strictly adhering to the above Clean Architecture skeleton: Skeleton/Compose, Domain Core, Rasterizer Infra, Application Usecase, HTTP Delivery, Web SPA UI, and CI/CD/Docker delivery. **STRICT RULE**: Do NOT output full source code blocks, long scripts, or full Dockerfiles in the epics. Specify ONLY file paths, responsibilities, schema struct definitions, and interface signatures.)
- **Epic 1 <Title>**:
  - **Description**: <Technical explanation of what to build>
  - **Objective**: <Business/functional value of what we want to achieve>
  - **Background & Motivation**: <Why this epic is needed and its value>
  - **Scope**: <Functional and technical scope adhering strictly to the architectural directory layout>
  - **Dependencies**: <List of prerequisite Epics or 'None (Root Foundation)'>
  - **Acceptance Criteria (AC)**: <Testable requirements>
  - **Definition of Done (DoD)**: <Unit tests, code coverage, zero lint errors, buildable artifact>
  - **Target Personas for Detailed Design**: <List of relevant personas for this specific epic>
  - **Isolated Epic Specification**: <Interface signatures, data schemas, and file boundaries ONLY. Strictly FORBIDDEN to output full implementation source code, full Dockerfiles, HTML/JS code, or long code blocks at this stage. Full implementation belongs strictly to Ceremony 3 TDD.>
[/INST]
