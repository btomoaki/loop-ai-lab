# Scrum-Based Autonomous Development Policy

## 🏛️ Framework Overview
Development is divided into iterative Sprint cycles:
1. **Refinement Phase**: Analyze requirements, detect specification gaps, split full project into a multi-sprint roadmap (`sprints/product_backlog.md`), define Sprint 1 scope (`sprints/sprint_1_backlog.md`), and generate custom harness (`sprints/sprint_1_harness.sh`).
2. **Sprint Execution Phase**: Autonomously implement ONLY the items in `sprint_N_backlog.md` until `sprint_N_harness.sh` passes 100% GREEN.
3. **Retrospective & Feedback**: If Sprint does not complete within 5 loops, write lessons learned to `sprints/retrospective.md` and feed it back into next Refinement/Sprint retry.

## 📏 Target Sprint Velocity & Granularity
- **Target Loops per Sprint**: 3 to 5 loop steps max.
- **Scope Limit**: Focus on at most 1-2 architectural layers (~5 files modified) per Sprint.
- **No Scope Creep**: Do NOT add features outside `sprint_N_backlog.md`.

## 🤖 Target Executor Environment Spec (Local LLM - Devstral 24B / Qwen 27B)
- **Context Window (num_ctx)**: 16,384 tokens (~12,000 words max prompt input)
- **Max Generation Limit (max_tokens)**: 4,096 tokens per single output
- **Capacity Characteristics**:
  - High capacity for one-shot initial skeleton generation (structs, handlers, tests in 1-2 passes).
  - Weak at resolving complex multi-package refactoring with cyclic dependencies once type errors occur.
  - High risk of code truncation if a single generated file exceeds ~4,000 tokens.
- **Design Rule**: Keep prompts and file outputs comfortably within 16k context and 4k generation bounds.
