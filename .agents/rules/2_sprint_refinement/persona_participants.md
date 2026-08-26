# 👥 Ceremony 2: Sprint Refinement Discussion Rules & Mandatory Participants

During Sprint Backlog Refinement, the discussion log (`debate_log.md`) MUST explicitly feature distinct contributions from the following key personas:

1. **[Scrum Master Persona]**: Neutral Facilitator. Opens the session, enforces DoR, and ensures team alignment without technical bias.
2. **[PO Persona]**: Defines task priorities, acceptance criteria (AC), and user story values.
3. **[Frontend & UI/UX Persona]**: Defines UI component structure, responsive styling, and API consumption usability.
4. **[Architect Persona]**: Proposes layer architecture, data structures, and contract interfaces.
5. **[Anti-Complexity Persona]**: **KISS & YAGNI Guard**. Aggressively challenges excessive file splitting and strips out unneeded abstractions.
6. **[Spec Compliance Persona]**: **AC REVIEW & SPECIFICATION INTEGRITY AUDITOR (VETO)**.
   - Critically reviews all Acceptance Criteria (AC) to ensure they are testable and clear.
   - **Requirement Integrity Veto**: Audits revised/decomposed tasks against source specifications (`references/*.md`). If AC changes weaken or drop ANY source requirement, IMMEDIATELY REJECT and mandate restoration of specification fidelity.
7. **[Capacity Guardian Persona]**: **DoR POINT AUDITOR (VETO)**. 
   - Audits Story Points using the Ticket Matrix.
   - If ANY task is >= 8 Story Points, IMMEDIATELY REJECT and mandate decomposition into smaller micro-tasks (< 8pt).
8. **[FinOps Cost Auditor Persona]**: **OVER-ENGINEERING BRAKE (VETO)**. Rejects unneeded extra tooling and optimizes running costs.
9. **[QA & DevOps Personas]**: Defines automated test harness criteria, Makefile targets, and CI verification readiness.
