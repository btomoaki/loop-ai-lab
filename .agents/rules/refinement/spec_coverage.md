# Specification Coverage & Traceability Audit Rule

## Rule Definition
1. **Traceability**: Every task in generated `sprint_1_backlog.yaml` files MUST feature a `spec_section` attribute mapping to `references/*.md` headings.
2. **Audit Mandatory**: The runner will automatically extract all `references/*.md` headings and perform a matrix coverage audit.
3. **No Omissions**: No major specification topic (Docker, GCP Cloud Run PORT, Frontend embed, Symmetry tests) may be left out of initiative backlogs.
