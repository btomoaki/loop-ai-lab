# Dynamic Epic Granularity & Safety Rule

## Rule Definition
1. **Decouple Architecture Layers from Epics**: Epics must reflect business features, infrastructure, and user-facing capabilities, NOT hardcoded code layers.
2. **Prevent AI Hangs via Fine Granularity**: Prefer smaller, incremental steps ("climbing stairs"). Broad, coarse tasks that cause LLM code generation hangs are strictly prohibited.
3. **Traceability**: Every task in generated `sprint_1_backlog.yaml` files MUST feature a `spec_section` attribute mapping to `references/*.md` headings.
