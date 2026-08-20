# POLICY: Autonomous Scrum Development Workflow

## 1. Core Principles
- **Initiative & Epic Phase Hierarchy**: The system specifications are decomposed into an Initiative Overview (`state/initiatives/initiative_overview.md`) and physically isolated Engineering Epic Phase directories (`state/initiatives/epic_{n}_{name}/`).
- **1 Task = 1 Sprint (YAML Backlog)**: Each task within an Epic Phase becomes an individual Sprint defined strictly in YAML format (`sprint_{n}_backlog.yaml`).
- **No Scope Creep**: Implement ONLY the items defined in the target Sprint's YAML backlog (`state/initiatives/epic_{n}_{name}/sprint_{n}_backlog.yaml`).

## 2. Refinement Phase (Phase 1)
- Analyze requirements in `references/*.md`.
- Generate `state/initiatives/initiative_overview.md` and `state/initiatives/epic_{n}_{name}/sprint_{n}_backlog.yaml`.
- Generate system specification `workspace/avatar-service/README.md`.
- Perform specification audit and pause with `BLOCKED_WAITING_PO` if PO input is required.

## 3. Sprint Execution Phase (Phase 2)
- Execute Devstral coding loop targeting ONLY the files listed in `TargetFiles` of the YAML backlog.
- Autonomously iterate until `sprint_{n}_harness.sh` passes 100% GREEN.
