# 🐳 Docker & Docker Compose Prerequisite & Lifecycle Standards

This standard governs the execution prerequisites, file dependency mappings, container lifecycles, and security boundaries for Docker and Docker Compose workflows across all initiatives.

---

## 1. 📂 Universal Target File Existence & Dependency Principle (ファイル先行配備の原則)

Docker CLI and Docker Compose commands MUST NEVER be invoked or verified against configuration files that do not physically exist at the time of task execution.

### A. Default Command Invocations (引数なしデフォルト実行)
- **`docker build .` / `docker run ...`**:
  - The default `Dockerfile` at the root directory MUST be physically created and committed before invoking or verifying default Docker CLI build commands.
- **`docker compose run ...` / `docker compose up ...`**:
  - The default `compose.yaml` (or `compose.yml` / `docker-compose.yaml`) at the root directory MUST be physically created and committed before invoking or verifying default Docker Compose commands.
- **Task DAG Requirement**:
  - Any task specifying a default `docker compose` or `docker build` in its `verify_command` MUST explicitly include the task that creates the target file in its `depends_on` list, or MUST be the dedicated environment bootstrap task (e.g., `TASK-1.1`) that creates the file within that same task.

### B. Custom & Multi-Environment File Invocations (任意別名・カスタム指定実行)
- **Custom Dockerfile Invocations (`docker build -f <path> ...`)**:
  - Custom file naming and directory structures (e.g., `Dockerfile.dev`, `Dockerfile.prod`, `Dockerfile.stg`, `build/Dockerfile`, `docker/Dockerfile.worker`) are **fully supported and permitted**.
  - **Single Universal Condition**: The specific physical file path passed to `-f` / `--file` MUST be physically created and verified by a prerequisite task before any command targets that path.
- **Custom Compose Invocations (`docker compose -f <path> ...`)**:
  - Custom Compose file naming and multi-file overrides (e.g., `compose.override.yaml`, `compose.dev.yaml`, `compose.test.yml`, `infra/compose.db.yaml`) are **fully supported and permitted**.
  - **Single Universal Condition**: The target file path specified with `-f` / `--file` MUST exist and be valid before running any compose command pointing to it.

---

## 2. 🛡️ Container Lifecycle Pair & Ephemeral Execution (ライフサイクル破棄保証)

- **One-Shot Verification Principle**:
  - All automated test, lint, and validation commands in sprint backlogs MUST be ephemeral and one-shot: `docker compose run --rm <service> ...` or `docker compose -f <path> run --rm <service> ...`.
  - The `--rm` flag guarantees that containers are immediately destroyed upon command exit, eliminating host resource leaks.
- **Zero Host Piping & Chaining Prohibition (ホストパイプ・連鎖コマンドの完全禁止)**:
  - `verify_command` MUST NEVER pipe container output to host shell commands (e.g. `docker compose run ... | grep` is STRICTLY FORBIDDEN as it invokes `grep` on the host machine).
  - `verify_command` MUST NEVER chain host commands using `&&` or `;` (e.g. `docker compose up -d && echo OK` or `docker compose run ... && echo OK` are STRICTLY FORBIDDEN).
  - If output inspection or compound checks are necessary, they MUST execute ENTIRELY inside the container: `docker compose run --rm <service> sh -c "ls -la | grep go.mod"`, or adopt lightweight image-independent verification: `docker compose run --rm <service> echo OK`.
- **Prohibition of Orphaned / Unpaired Background Containers**:
  - Standalone/unpaired `docker compose up -d` or `docker run -d` without automated teardown handlers is strictly forbidden in automated test verification scripts.
  - Verification commands MUST NEVER rely on host-level backgrounding (`&`) or manual `pkill` / `kill` commands.
- **Lightweight Image-Independent Verification**:
  - For setup, skeleton, and configuration verification tasks (e.g., directory layout), use `docker compose run --rm <service> echo OK` to assert container operational readiness without coupling to image-specific CLI tools or introducing binary mismatch failures.

---

## 3. 🔒 Supply Chain & Network Security Standards

- **Immutable Version Tag Pinning**:
  - Using mutable floating tags (such as `:latest`, `:latest-alpine`, `:alpine`, or `:stable`) is strictly prohibited for reproducible CI/CD and SLSA supply chain security.
  - All base images MUST pin explicit versions (e.g., `golang:1.22-alpine`, `nginx:1.27-alpine`, `golangci/golangci-lint:v1.59-alpine`, `gcr.io/distroless/static:nonroot`).
- **Network Security & Port Publishing Standards**:
  - For single-binary/microservice deployments, the application container (`app`) may publish its designated port (e.g. `8080:8080`) directly for development access.
  - When an explicit reverse proxy (e.g. `proxy` / Nginx) is configured in multi-container setups, backend services should use internal container networking (`expose: ["8080"]`) with the proxy managing external entrypoints.
