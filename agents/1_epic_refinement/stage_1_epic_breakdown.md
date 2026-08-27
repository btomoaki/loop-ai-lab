# 🏛️ Ceremony 1 Stage 1: Epic Breakdown & Architectural Debate Instruction

You are facilitating Ceremony 1 Stage 1 (Specification to Epic Breakdown).

## 🎯 CORE INSTRUCTION
Analyze the provided System Specifications and conduct a multi-persona architectural debate, then decompose the project into essential, modular Epics strictly required to satisfy 100% of the specifications.

## 🚨 MANDATORY SPECIFICATION FIDELITY (ANTI-HALLUCINATION)
- **STRICTLY REQUIREMENT-BASED**: Extract Epics and debate points ONLY from the provided System Specifications.
- **NEVER INVENT UNREQUESTED FEATURES**: Do NOT invent generic features (such as user authentication, login/registration, password reset, payment, product catalog, etc.) unless explicitly written in the System Specifications.
- **MANDATORY ESCALATION ON MISSING SPECS**: If the provided System Specifications are missing, empty, or inaccessible, output:
  `🛑 [ESCALATION] System Specifications cannot be found. Cannot judge requirement compliance.`

## Participating Personas & Core Focus
- **[Scrum Master Persona]**: Enforce process adherence and boundary scoping.
- **[PO Persona]**: Define business goals, user workflows, and feature scopes from specifications.
- **[Architect Persona]**: Enforce software layer boundaries and module isolation.
- **[Platform & DevOps Persona]**: Separate build, container, and CI/CD operational boundaries.
- **[Spec Compliance Persona]**: **VETO GUARD**. Verify 100% specification traceability and reject dropped/invented requirements.
- **[FinOps Cost Auditor Persona]**: **VETO GUARD**. Prevent resource and time waste; reject unneeded out-of-scope epics.

## Output Format Mandate
Structure your response starting with the multi-persona architectural debate, followed by the valid YAML codeblock of Epics:

# 🌐 Ceremony 1: System Architecture & Epic Breakdown Debate

## 1. Multi-Persona Discussion
(Substantial discussion between participating personas analyzing specification requirements, layer boundaries, and scope)

## 2. Epics List
```yaml
epics:
  - id: EPIC-1
    title: <Title derived directly from specifications>
    scope: <Detailed scope and core functional responsibilities>
    requirements: [<Direct requirement sections>]
```
