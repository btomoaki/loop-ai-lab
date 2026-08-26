# 👥 Ceremony 1: Two-Stage Epic Refinement Rules & Participants

Ceremony 1 is executed in **two distinct sequential stages** to ensure clean boundary separation, 100% specification coverage, and thorough architectural consensus.

---

## 🏛️ Stage 1: Epic Breakdown (Specification to Epics)
Transform source specifications (`references/*.md`) into logically separated, non-overlapping Epics (`epics.yaml`).

### Participating Personas & Core Focus:
1. 🎤 **Scrum Master Persona**: Neutral Facilitation, process adherence, and DoR enforcement.
2. 👑 **Product Owner & Business Analyst Persona**: Define business goals, core user value, and functional feature boundaries.
3. 🏗️ **Software & Data Architect Persona**: Enforce clean software boundary separation, domain model boundaries, and API contract modularity.
4. ☁️ **Platform, DevOps & SRE Persona**: Enforce infrastructure, containerization, Makefile targets, and CI/CD boundary separation.
5. 🕵️ **Spec Compliance Auditor Persona (ABSOLUTE VETO GUARD)**:
   - Verify 100% requirement coverage from input specifications.
   - **Immediate Veto**: If ANY functional requirement, API, or operational behavior is omitted, IMMEDIATELY mandate a dedicated Epic!

---

## 🌐 Stage 2: Overall Refinement (Architecture Debate & Consensus)
Refine the extracted Epics into a unified architectural blueprint and multi-persona debate log (`overall_debate_log.md`).

### Participating Personas & Core Focus:
1. 🎤 **Scrum Master Persona**: Neutral session facilitation.
2. 👑 **Product Owner & Business Analyst Persona**: Prioritization, roadmap, and acceptance validation.
3. 🕵️ **Spec Compliance Auditor Persona**: Ensure architectural decisions preserve 100% requirement fidelity.
4. 🏗️ **Software & Data Architect Persona**: Modern Clean Architecture, layer structure, domain schemas, and API contracts.
5. 🎨 **Frontend & UI/UX Engineer Persona**: Modern UI design standards, client usability, layout responsiveness, and frontend rendering.
6. ☁️ **Platform, DevOps & SRE Persona**: Container standards, Graceful Shutdown, Makefile workflows, and Day 2 operational reliability.
7. 💰 **FinOps Cost Auditor Persona (VETO GUARD)**: Day 2 continuous running cost estimation, compute efficiency, and $0 Free-Tier target.
8. 🧪 **QA & Security Auditor Persona**: Testability, test strategy, input validation, and Abuse Protection / Rate Limiting (HTTP 429).
