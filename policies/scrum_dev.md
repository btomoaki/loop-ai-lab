# Scrum Development & Refinement Policy

## Refinement Granularity & Quality Standards
1. Every Sprint Backlog YAML (`sprint_1_backlog.yaml`) generated during Refinement must provide detailed, concrete task descriptions (`description` field for every task).
2. Domain layer tasks (`epic_1_domain`) must strictly focus on pure struct definitions and zero-value invariants.
3. Construction, hashing, and factory functions must be isolated in Application/Service layers (`epic_2_usecase`).
