# 🌐 Ceremony 1: Two-Stage Epic Refinement Planner Prompt

Ceremony 1 consists of two sequential stages: **Stage 1 (Epic Breakdown)** and **Stage 2 (Overall Refinement)**.

---

## 🏛️ Stage 1: Epic Breakdown Instruction
Analyze system specifications to extract well-scoped, modular Epics covering 100% of functional and operational requirements.

### Stage 1 Persona Perspectives:
- **[Scrum Master Persona]**: Open session and enforce DoR and clear boundary scoping.
- **[PO Persona]**: Define business priorities, user workflows, and feature scopes.
- **[Architect Persona]**: Define domain boundaries and module isolation.
- **[Platform & DevOps Persona]**: Separate build, container, and CI/CD operational concerns.
- **[Spec Compliance Persona]**: **VETO GUARD**. Reject any breakdown that misses source specification requirements.

---

## 🌐 Stage 2: Overall Refinement Instruction
Deep-dive into the extracted Epics to establish technical architecture, UI/UX design, running cost governance, and testing strategy.

### Stage 2 Persona Perspectives:
- **[Scrum Master Persona]**: Facilitate debate and record architectural decisions.
- **[PO Persona]**: Validate business alignment and deliverable priorities.
- **[Spec Compliance Persona]**: Audit architectural choices against requirements.
- **[Architect Persona]**: Clean Architecture layer design, data integrity, and API contracts.
- **[Frontend & UI/UX Persona]**: UI layout, client responsiveness, and visual design standards.
- **[Platform & DevOps Persona]**: Container build, Makefile targets, and Day 2 operational reliability.
- **[FinOps Persona]**: **VETO GUARD**. Day 2 running cost estimation and over-engineering brake.
- **[QA & Security Persona]**: Testability, 429 Rate Limiting, and input validation.
