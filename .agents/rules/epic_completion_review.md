# Epic Completion Gate & Definition of Done (DoD) Review Rule

## Rule Definition
1. **Lightweight Sprint Iteration**: Individual sprints (1 task) MUST only require `sprint_N_harness.sh` passing (Exit 0) for maximum execution speed.
2. **Epic Completion Gate**: When all sprints in an epic are finished, a 2-persona review ([PO] & [Auditor]) MUST evaluate the overall epic.
3. **Definition of Done (DoD) Checklist**:
   - **PO Check**: All sprint Acceptance Criteria in the epic are 100% satisfied.
   - **Auditor Check**: No Clean Architecture layer violations, no hardcoded secrets, and no unnecessary constructor exposures.
4. **Log & Status Output**:
   - Review log written to `state/.evaluator/epic_<topic>_review_log.md`.
   - MUST output explicit status tag: `STATUS: EPIC_APPROVED` or `STATUS: EPIC_REJECTED`.
5. **Rejection Feedback Loop**:
   - If `STATUS: EPIC_REJECTED`, fix requests MUST be appended into the target sprint backlog under `supplementary_instructions:` for targeted repair.
