# Multi-Persona Debate Refinement Rule

## Rule Definition
1. **Multi-Persona Perspective**: Refinement MUST evaluate plans from PO, Architect, QA, and Devil's Advocate Auditor viewpoints.
2. **Hang Prevention**: Auditor persona MUST eliminate overly broad tasks that cause LLM code generation hangs.
3. **YAML Format**: Backlog definitions MUST be output in clean YAML format with explicit `spec_section` tags.
