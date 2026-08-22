# Multi-Persona Debate Refinement Rule

## Rule Definition
1. **Multi-Persona Perspective**: Refinement MUST evaluate plans from PO, Architect, QA, and Devil's Advocate Auditor viewpoints.
2. **Hang Prevention**: Auditor persona MUST eliminate overly broad tasks that cause LLM code generation hangs.
3. **YAML Format**: Backlog definitions MUST be output in clean YAML format with explicit `spec_section` tags.


4. **Mandatory Context & Rationale Explanation (背景と理由の解説義務)**:
   - When generating `state/.evaluator/refinement_debate_log.md`, the AI MUST NOT output bare bullet points alone.
   - It MUST include an explicit "Context & Rationale Explanation" section explaining:
     - **Why the critical challenge occurred** (e.g. which spec section was overlooked in early drafts).
     - **How the decision prevents AI code-generation hangs or production deployment failures**.
