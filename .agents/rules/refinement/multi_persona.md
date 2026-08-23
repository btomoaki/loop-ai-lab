# Overall System Debate & Multi-Persona Refinement Standard

## 1. Phase 1: Overall Debate Responsibilities (Epic Classification & Trimming)
Phase 1 Overall Architecture Debate (`state/.evaluator/overall_debate_log.md`) must execute before individual Epic debates to fulfill two critical objectives:
1. **Trim Non-Actionable Content**: Explicitly inspect `references/` spec documents and discard non-actionable elements such as external reference URLs, Cloud Run documentation links, or Go standard package links that require no coding or infra task creation.
2. **Classify Actionable Epics**: Dynamically determine the exact list of actionable Epics requiring code implementation, Clean Architecture layer design, and container deployment.

## 2. Phase 2: 4-Persona Representation & 4-Step Consensus Workflow
Scrum Refinement for EACH individual Epic must be conducted by **4 mandatory personas**:
1. **[PO Persona]**: Advocates for business value, scope completeness, and initial task breakdown proposals.
2. **[Technical Architect Persona]**: Enforces Go Clean Architecture 4-layer separation (`domain/model/`, `domain/repository/`, `application/usecase/`, `infrastructure/`, `interface/adapter/`), DI wiring, and package granularity.
3. **[QA Engineer Persona (OPPOSING VIEW)]**: Challenges implementation assumptions, edge cases, nil/empty string input vulnerabilities, and test coverage requirements.
4. **[Security Auditor Persona (CRITICAL AUDIT)]**: Audits threat boundaries, Distroless container safety (`gcr.io/distroless/static-debian12`), non-root execution (`USER nonroot:nonroot`), `PORT` environment variable binding, and enforces commercial license compliance (**MIT, Apache-2.0, or BSD**).

### 4-Step Consensus Workflow:
- **Step 1: Initial Task Proposals (PO & Dev)**: List initial feature tasks.
- **Step 2: Multi-Persona Debate & Challenge**: TA, QA, and Security Auditor challenge initial proposals regarding layer boundaries, edge tests, and security rules.
- **Step 3: Conflict Resolution & Task Merging**: Reconcile opposing views. Combine duplicate or overlapping tasks into single **Consolidated Tasks**. Resolve conflicts by prioritizing Technical Architect and Security Auditor constraints.
- **Step 4: Consensus-Approved Merged Task List**: Formally define the unified tasks with combined Descriptions and positive DoD (Definition of Done) criteria.

## 3. License & Dependency Compliance Policy (Positive Assertions)
- **Approved OSS Licenses**: Permitted 3rd-party packages must strictly use commercial-friendly open source licenses (**MIT, Apache-2.0, or BSD**).
- **Positive Phrasing Requirement**: Avoid double negatives or negative prompts. Use clear positive statements (e.g. *"Permitted 3rd-party packages must use commercial-friendly licenses (MIT, Apache-2.0, or BSD)"*).

## 4. Context Referencing Policy (No Text Injection)
- **Do NOT concatenate or inject raw text logs/spec strings directly into prompts.**
- Individual Epic debates must reference the overall debate decisions and specification context strictly via **physical file paths**:
  - Overall Architecture Context: `state/.evaluator/overall_debate_log.md`
  - Specification Context: `references/icon_generator.md §X.Y` or `references/go_clean_architecture.md §Z`

## 5. Mandatory Output Storage Paths
- **Overall Classification & Debate Log**: `state/.evaluator/overall_debate_log.md`
- **Per-Epic Debate Logs**: `state/initiatives/<epic_dir_name>/debate_log.md`
- **Consolidated Sprint Backlog**: `state/initiatives/<epic_dir_name>/sprint_1_backlog.yaml`
- **DoD Harness Verification Script**: `state/initiatives/<epic_dir_name>/sprint_1_harness.sh`
