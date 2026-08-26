# 🌐 Overall Epic Refinement Debate Rules

## 1. 🎯 Purpose & Scope
Analyze the system specifications (`references/*.md`) and conduct overall multi-persona architecture debate to extract single-responsibility Epics.

## 2. ⚖️ Decision Resolution & Escalation Policy
- **Mandatory Reference to `references/decisions.md`**:
  - The LLM MUST strictly resolve architectural trade-offs, determinism, performance, and customization choices by following the pre-agreed decisions in `references/decisions.md`.
- **Autonomous Resolution**:
  - Do NOT output `STATUS: REQUIRES_SPEC_DECISION` for questions already resolved in `references/decisions.md`. Always resolve them autonomously according to `references/decisions.md` and conclude Ceremony 1 with **`STATUS: OVERALL_DEBATE_PASSED`**.
- **Escalation Exception**:
  - Only output `STATUS: REQUIRES_SPEC_DECISION` if there is a newly discovered, unresolvable physical spec contradiction not covered by `references/decisions.md`.
## 3. 🕵️ Specification Completeness Auditor Directive
- **Mandatory Participation**:
  - Section 2 MUST explicitly record participation of `[Specification Completeness Auditor]`.
- **Balanced Spec Audit**:
  - `[Specification Completeness Auditor]` MUST audit 100% of requirement sections in `references/*.md` to mandate that BOTH core application domains (logic, validation, API) AND infrastructure/deployment domains (`epic_docker_containerization`, `epic_cloud_run_deployment`) are classified as dedicated Epics under Section 3!

## 4. 📝 Mandatory Output Structure & Naming Pattern
The generated `# 🌐 Overall System Architecture Multi-Persona Debate Log` MUST contain the following exact sections:
- `## 1. System Goals & Specification Alignment`
- `## 2. Participating Personas` (MUST explicitly list `[Specification Completeness Auditor]`)
- `## 3. Classified Actionable Epics List` (MUST list all extracted Epics formatted as `- **epic_N_feature_name**: Scope description`)
- `## 4. Trade-off Resolutions`
- `## 5. Status` (MUST conclude with `STATUS: OVERALL_DEBATE_PASSED`)

