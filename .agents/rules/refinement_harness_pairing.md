# Harness Atomic Pairing Rule

## Rule Definition
1. **1-to-1 File Pairing**: Every `sprint_N_backlog.yaml` MUST be paired with a dedicated `sprint_N_harness.sh` script.
2. **Task Isolation**: `sprint_N_harness.sh` MUST only assert the criteria of sprint N's task to prevent test contamination.
