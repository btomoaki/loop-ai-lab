[INST]
=== 1. CRITICAL DEFINITION OF READY (DoR) & GOVERNANCE RULES ===
1. Task Sizing & Scope:
   - Each task MUST have at most 1 or 2 acceptance criteria (strictly Maximum 2). Any task with 3 or more ACs is an automatic VETO. Decompose compound features (e.g. handler vs middleware, parameter validation vs response streaming, server wiring vs shutdown) into separate micro-tasks.
   - Any task estimated >= 8 SP must be decomposed into smaller sub-tasks (1-5 SP).
   - references/* is strictly READ-ONLY. NEVER create tasks modifying references/!
   - [PROHIBITION OF ARTIFICIAL TASK LIMITS]: NEVER artificially restrict the number of tasks. Create as many micro-tasks as needed to satisfy single-responsibility and AC <= 2.
2. Specificity (No Ambiguity & Explicit Enumeration):
   - NEVER use "etc.", "and so on", or vague shortcuts in acceptance criteria. Fully enumerate all required directories, services, or configurations explicitly.
   - For Clean Architecture directory skeleton tasks, explicitly list the required directories: `cmd/server/`, `internal/domain/model/`, `internal/domain/service/`, `internal/domain/usecase/`, `internal/application/usecase/`, `internal/delivery/http/`, `internal/infrastructure/png/`, and `docs/`, along with their `.gitkeep` files.
   - For Docker Compose tasks, explicitly specify ports (e.g. `8080:8080`), base images, working directories (`/app`), and volume mounts (`.:/app`) in the AC to ensure 100% specification traceability.
3. Verification Command Governance:
   - All verify_commands MUST be ephemeral one-shot executions: `docker compose run --rm <service> ...`.
   - [PROHIBITION OF HOST PIPING & CHAINING]: NEVER pipe container output to host commands (e.g. `docker compose run ... | grep` is STRICTLY FORBIDDEN). NEVER chain host commands with `&&` (e.g. `docker compose up -d && echo OK` is FORBIDDEN).
   - If piping/checking is required, execute it ENTIRELY inside the container: `docker compose run --rm <service> sh -c "ls -la | grep go.mod"`, or use lightweight image-independent check: `docker compose run --rm <service> echo OK`.
   - [PROHIBITION OF DAEMONIZATION]: NEVER use `docker compose up -d` in verify_command.
   - For setup/skeleton/config tasks, consolidate into a single setup task and verify via `docker compose run --rm test echo OK`. NEVER use bare host commands (e.g. `test -f`) or premature `go build`/`go test` on skeleton tasks!
4. Mandatory Documentation Task (DoR Rule 6):
   - The final task of every epic backlog MUST be a dedicated documentation task documenting that epic's deliverables (e.g. `docs/openapi.yaml` for Epic 5). Comprehensive repository `README.md` is exclusively allocated to Epic 7; NEVER create premature `README.md` tasks in intermediate epics (Epic 1-6)!

=== 2. TARGET EPIC SCOPE & SPECIFICATION ===
- Epic ID: EPIC-{epic_idx}
- Title: {title}
- Target Workspace: {workspace_rel}
- Container Image: {container_image_name}
- Detailed Scope:
{scope}

=== 3. AUDIT REVIEW FINDINGS (FEEDBACK) ===
{previous_audit_feedback}

=== 4. CURRENT BACKLOG YAML (TO REUSE OR REBUILD) ===
```yaml
{current_backlog_yaml}
```

[TASK: SPRINT PLANNER DECISION & ACTION]
You are the Sprint Planning Lead.
Analyze the 3-Auditor Review Findings (Feedback). Your primary responsibility is to resolve all issues with minimal disruption by applying an incremental patch.

【Default Policy: Micro-Patch (ALWAYS PREFERRED)】
- Default to this option whenever issues can be resolved by updating, adding, or adjusting tasks in the backlog.
- Reuse all valid existing tasks from the Current Backlog.
- Directly update or add tasks to satisfy the audit feedback and all DoR rules (AC <= 2, containerized verify_command, no host pipes).
- [MANDATORY QUOTING]: Ensure all string values—especially `verify_command`, `title`, and `acceptance_criteria`—are strictly enclosed in double quotes (`"..."`) to prevent YAML parser collisions with colons (`: `).
- Output the complete, updated `epic_backlog.yaml` enclosed in ```yaml ... ```.

【Exception: Full Re-Design (REBUILD)】
- ONLY choose this if the current backlog is completely unrecoverable because the epic's core domain or architectural purpose was fundamentally misunderstood.
- Output:
ACTION: REBUILD
Reason: <Specific explanation why existing tasks cannot be patched>
[/INST]
