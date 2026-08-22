# Unit Test & Language-Agnostic Project Manifest Verification Rule

## Rule Definition
1. **Mandatory Project Manifest Verification**:
   - Verification harnesses MUST NOT skip test execution or return Exit 0 when the project's language-standard module manifest (e.g. `go.mod`, `package.json`, `pyproject.toml`, `Cargo.toml`) is missing.
   - If the required module manifest does not exist in the target workspace, the harness MUST return Exit 2 (Failure).
2. **Dev Agent Project Initialization Mandate**:
   - Dev Agent MUST produce the appropriate language module manifest in the initial sprint task.
3. **Strict Language Test Runner Execution**:
   - Once the manifest is present, the harness MUST execute real language-standard linting and test suite assertions.
