# Refinement & Single-Task Sprint Rule

## 1. Scoped Generation & Non-Omission Rule (省略絶対禁止原則)
- ALWAYS start backlog generation strictly from **Epic 1: Domain Core** (`internal/domain/model/`, `internal/domain/repository/`, `internal/domain/service/`).
- Never skip Epic 1 under any circumstances.
- Scope-limiting prevents LLM semantic compression breakdown, hangs, and summary fallbacks.

## 2. Granularity & DoD
- Each Sprint MUST contain exactly 1 focused task.
- EVERY task MUST reference a specific spec section (e.g., `spec_section: "4.2 Parameter Design Specs"`).
