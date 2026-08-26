# 📝 Sprint Backlog Decomposition & DoR Rules

## 1. 🚥 DoR (Definition of Ready) Rules
- **Acceptance Criteria**: Each task in `epic_backlog.yaml` and `sprint_x_backlog.yaml` MUST have **at most 2 Acceptance Criteria**.
- **Story Points Required**: Each task MUST include a `story_points` field (integer 1-5 based on Ticket Matrix: Domain Core: 5, CI/CD: 4, DI: 3, Test: 2, Logic: 1-2, API: 1).
- **Task ID Format**: Task IDs MUST strictly use the pattern `- id: "TASK-1.1"` starting under `tasks:`.
- **No NFRs**: Non-functional requirements are EXCLUDED from DoR and validated during DoD.

## 2. 📝 Required YAML Task Schema Structure
Every generated task in `epic_backlog.yaml` MUST strictly follow this exact structure:
```yaml
epic: "Epic Title"
scope: "Epic scope"
target_workspace: "workspace/identicon-generator"
test_command: "go test ./..."
tasks:
  - id: "TASK-1.1"
    title: "Task title"
    story_points: 2
    acceptance_criteria:
      - "Criterion 1"
```


