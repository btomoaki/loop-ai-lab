# 🏃 Ceremony 3: Autonomous TDD Dev Executor Instructions

## 1. Output Format Mandatory Rule (CRITICAL)
- Generate complete implementation and test code files using `# FILE: <relative_path>` format.
- Do NOT use generic placeholders inside file paths. Always use concrete relative paths inside the target workspace.

### Example Format:
# FILE: main.ext
// Main entrypoint implementation...

# FILE: internal/domain/entity.ext
// Domain entity implementation...

## 2. General Execution Directives
- Follow all architecture, language, and repository rules provided in `.agents/rules/`.
- Write complete, production-ready source code and corresponding unit tests.
- Ensure all created and modified files strictly adhere to the target workspace boundaries.
- **NEVER generate or hallucinate package lockfiles** (e.g. `go.sum`, `package-lock.json`, `poetry.lock`). Declare dependencies ONLY in manifest files (e.g. `go.mod`, `package.json`).


