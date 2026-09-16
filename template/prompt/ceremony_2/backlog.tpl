[INST]
=== 1. CRITICAL DEFINITION OF READY (DoR) & GOVERNANCE RULES ===
1. Task Sizing & Scope:
   - Each task MUST have at most 1 or 2 acceptance criteria (strictly Maximum 2). Any task with 3 or more ACs is an automatic VETO. Decompose compound features (e.g. handler vs middleware, parameter validation vs response streaming, server wiring vs shutdown) into separate micro-tasks.
   - Any task estimated >= 8 SP must be decomposed into smaller sub-tasks (1-5 SP).
   - references/* is strictly READ-ONLY. NEVER create tasks modifying references/!
   - [PROHIBITION OF ARTIFICIAL TASK LIMITS]: NEVER artificially restrict the number of tasks. Create as many micro-tasks as needed to satisfy single-responsibility and AC <= 2.
2. Specificity (No Ambiguity & Explicit Enumeration):
   - NEVER use "etc.", "and so on", or vague shortcuts in acceptance criteria. Fully enumerate all required directories, services, or configurations explicitly.
   - [EXPLICIT TARGET FILE PATH MANDATE]: Every task MUST explicitly state its concrete physical target file path (e.g. `web/static/index.html`, `app.js`, `internal/delivery/http/static_embed.go`, etc.) directly from Section 2 Scope in its description and acceptance criteria. Never omit the target file path!
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
5. Mandatory String Quoting (Strict YAML Syntax):
   - Every `verify_command`, `title`, and item in `acceptance_criteria` MUST be enclosed in explicit double quotes (`"..."`).
   - Unquoted strings containing colons followed by spaces (e.g. `: `, CSS properties like `width: 250px`, or regex patterns) cause fatal YAML parser collisions and are strictly prohibited!

=== 2. TARGET EPIC SCOPE & SPECIFICATION ===
- Epic ID: EPIC-{epic_idx}
- Title: {title}
- Target Workspace: {workspace_rel}
- Container Image: {container_image_name}
- Detailed Scope:
{scope}

=== 3. CEREMONY RETROSPECTIVE & AUDIT FEEDBACK (IF ANY) ===
{retro_content}

[TASK: GENERATE EPIC BACKLOG YAML FOR {title}]
Generate a valid YAML block containing micro-scoped, dependency-ordered tasks for {title}.
Ensure 100% traceability to all specifications and address any audit feedback above.

Output MUST be a valid YAML block enclosed in ```yaml ... ```:
```yaml
epic_id: EPIC-{epic_idx}
title: "{title}"
workspace_rel: "{workspace_rel}"
tasks:
  - id: TASK-{epic_idx}.1
    title: "Setup domain foundation and interfaces"
    description: "Detailed task scope"
    story_points: 1
    depends_on: []
    acceptance_criteria:
      - "Criterion 1 (Concrete assertion)"
      - "Criterion 2 (Concrete assertion)"
    verify_command: "docker compose run --rm test echo OK"
  - id: TASK-{epic_idx}.2
    title: "Implement core functionality"
    description: "Detailed task scope"
    story_points: 2
    depends_on: ["TASK-{epic_idx}.1"]
    acceptance_criteria:
      - "Criterion 1 (Concrete assertion)"
      - "Criterion 2 (Concrete assertion)"
    verify_command: "docker compose run --rm test go test -v ./..."
  - id: TASK-{epic_idx}.3
    title: "Document epic specifications"
    description: "Create or update documentation for this epic"
    story_points: 1
    depends_on: ["TASK-{epic_idx}.2"]
    acceptance_criteria:
      - "Specification file exists and passes validation"
    verify_command: "docker compose run --rm test echo OK"
```
[/INST]
