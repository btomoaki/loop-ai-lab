# Overall Architecture Debate & Epic Classification Rule

## 🛑 Fundamental Constraint: Specification Bounds
1. **Strict Specification Focus**:
   - The primary objective of this debate is to analyze and fulfill the provided System Specification (e.g. `references/icon_generator.md`).
   - Do NOT introduce, hallucinate, or discuss features NOT mentioned in the specification (e.g. mobile apps, databases, authentication, custom user dashboards).
2. **Missing Specification Alert**:
   - If NO system specification file is provided or references are empty, HALT immediately and output: `STATUS: ERROR_MISSING_SPECIFICATION`.

## ⚖️ Trade-off & Alternative Proposal Escalation Rule
1. **Unfeasible Requirement Handling**:
   - If any requirement in the specification cannot be strictly satisfied 100% due to technical constraints, platform limits, or architectural complexity:
     - DO NOT silently ignore the requirement.
     - DO NOT hardcode dummy or broken fallbacks.
2. **Escalation Protocol**:
   - The `Specification Auditor` or `Software Architect` persona MUST document the specific impediment.
   - Propose 2 pragmatic alternative options (Option A / Option B) with trade-offs.
   - Set status to: `STATUS: REQUIRES_SPEC_DECISION`.
   - Halt execution and request user approval/choice.

## Multi-Persona Audit & Coverage
1. **Requirement Coverage Audit**:
   - The `Specification Auditor` persona MUST audit all explicitly listed requirements in the specification (e.g. Go Clean Architecture, HTTP handler `/identicon`, PNG byte output, GCP Cloud Run `$PORT` binding, `USER nonroot` execution, MIT/Apache-2.0/BSD licenses).
2. **Single-Responsibility Epics**:
   - Classify single-responsibility epics starting with `epic_<number>_<name>`.
   - **CRITICAL**: Do NOT use conjunctions like `and` or `with` in epic names!

## Required Output Structure
The output MUST follow this markdown structure:
```markdown
# 🌐 Overall System Architecture Multi-Persona Debate Log

## 1. System Goals & Specification Alignment
- Specification Target: <Target system name from specification>
- Scope Audit: Specification requirement fulfillment and identified trade-offs

## 2. Multi-Persona Overall Debate
- **[PO Persona]**: Specification goals and scope validation
- **[Specification Auditor Persona]**: Specification requirement audit (Cloud Run $PORT, non-root USER, licenses, and unfeasible spec escalation if any)
- **[Software Architect Persona]**: Clean Architecture 4-layer separation map
- **[DevOps & Cloud Architect Persona]**: Multi-stage Distroless build & Cloud Run container setup
- **[QA Engineer Persona]**: Testing strategy (unit/integration/http)
- **[Security & Network Auditor Persona]**: Security audit (input sanitization, non-root user)

## 3. Classified Actionable Epics List
- **epic_1_<name>**: <Scope description directly from spec>
- **epic_2_<name>**: <Scope description directly from spec>
...

STATUS: OVERALL_DEBATE_PASSED
```
*(Note: If specification changes or trade-offs are required, use `STATUS: REQUIRES_SPEC_DECISION` instead of `STATUS: OVERALL_DEBATE_PASSED`)*
