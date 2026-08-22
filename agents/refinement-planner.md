# Dynamic Refinement & Granularity Rules

## 1. Dynamic Epic Breakdown (No Fixed Layers)
- **Feature & Goal-Based Partitioning**: Do NOT restrict epics to a fixed set of 4 clean-architecture layers.
- **Dynamic Creation**: Dynamically create epics based on functional domains, infrastructure components, web frontends, and testing requirements found in `references/*.md`.
- **Step-by-Step Granularity**: Prefer smaller, step-by-step epics and tasks (climbing stairs safely) over massive, monolithic tasks.

## 2. Prohibition of Coarse Granularity (Hang Prevention)
- **Prevent Overly Broad Tasks**: Never create overly broad epics/tasks that bundle multiple heavy responsibilities together (which causes AI hangs and token depletion).
- **Traceability Tag (`spec_section`)**: Every task MUST include `spec_section: "<heading>"` to track coverage of `references/*.md`.
