# Refinement Planner Master Guidance

## 1. Multi-Persona Debate
- Evaluate requirements using [PO], [Architect], [QA], and [Devil's Advocate Auditor] personas.
- Document debates in `state/.evaluator/refinement_debate_log.md`.

## 2. Dynamic Feature Epics
- Group initiatives dynamically by functional topic (`epic_<topic>`), not fixed layers.

## 3. 1-Sprint-1-Task Partitioning
- Output single-task `sprint_N_backlog.yaml` inheriting parent `epic_scope`.

## 4. Isolated Harness Pairing
- Pair every `sprint_N_backlog.yaml` with a dedicated `sprint_N_harness.sh`.

## 5. Domain-Specific Verification Harnesses
- **Docker**: `docker build` & `PORT` startup liveness in `refinement_harness_docker.md`.
- **HTTP API**: Dynamic URL mapping & `curl` status in `refinement_harness_http_api.md`.
- **Unit**: Language standard `go test` in `refinement_harness_unit.md`.

## 7. Epic Completion Gate & DoD Review
- Individual sprints are fast-tracked via `./sprint_N_harness.sh` (Exit 0).
- Epic completion triggers DoD review by [PO] and [Auditor], documented in `state/.evaluator/epic_<topic>_review_log.md`.


4. **Mandatory Definition of Done (DoD) Per Task**:
   - Every `sprint_N_backlog.yaml` MUST include an explicit `definition_of_done:` checklist (array of 2-3 unambiguous strings).
   - The DoD checklist MUST specify file placement paths, architectural constraints, and harness passing conditions.
