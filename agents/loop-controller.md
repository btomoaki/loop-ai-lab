# Loop Controller Master Guidance (Language-Agnostic)

## Execution Loop Sequence
1. **Load Backlog Specification**: Read physical backlog file `sprint_N_backlog.yaml`.
2. **Generate Task Code**: Instruct Dev Agent to implement the single specified task.
3. **Execute Verification Harness**: Run assigned `./sprint_N_harness.sh`.
4. **Evaluate Harness Result**:
   - **PASS (Exit 0)**: Complete sprint iteration.
   - **FAIL (Non-zero)**: Append failure log into `sprint_N_backlog.yaml` under `harness_feedback:` and retry.

## File-Path Reference Standard
- Dev Agent MUST load task specifications directly from physical file `sprint_N_backlog.yaml` via file path reference.
- NEVER pass full text of backlog files in the prompt payload to prevent LLM context exhaustion.
