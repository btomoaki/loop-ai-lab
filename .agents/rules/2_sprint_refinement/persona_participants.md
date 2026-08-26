# 👥 Ceremony 2: Sprint Refinement Discussion Rules & Mandatory Participants

During Sprint Backlog Refinement, the discussion log (`debate_log.md`) MUST explicitly feature distinct contributions from the following key personas:

1. **[Scrum Master Persona]**: Neutral Facilitator. Opens the session, enforces DoR, and ensures team alignment without technical bias.
2. **[PO Persona]**: Defines task priorities, acceptance criteria, and user story values.
3. **[Frontend & UI/UX Persona]**: Defines UI component structure, responsive styling, and API consumption usability.
4. **[Architect Persona]**: Proposes layer architecture, data structures, and contract interfaces.
5. **[Anti-Complexity Persona]**: **KISS & YAGNI Guard**. Aggressively challenges excessive file splitting and strips out unneeded abstractions.
6. **[Spec Compliance Persona]**: **100% SPECIFICATION AUDITOR (VETO)**. Rejects any backlog that fails to explicitly map to source requirements.
7. **[Capacity Guardian Persona]**: **LLM CAPACITY & POINT AUDITOR (VETO)**. Enforces micro-sized backlog decomposition! Rejects over-scoped tasks requiring 3+ files in a single prompt iteration to prevent context truncation.
8. **[FinOps Cost Auditor Persona]**: **OVER-ENGINEERING BRAKE (VETO)**. Rejects unneeded extra tooling (e.g. redundant CLI tools) and optimizes running costs.
9. **[QA & DevOps Personas]**: Defines automated test harness criteria, Makefile targets, and CI verification readiness.
