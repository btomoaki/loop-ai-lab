# 🛠️ Continuous Development & CI/CD Environment Policy

All generated projects and initiatives MUST adhere to continuous development, operational readiness, and developer experience standards from the initial sprints without polluting the developer's host machine.

## 1. 🐳 Clean Containerized Development Environment (Docker Compose - Mandatory)
Every workspace repository MUST provide a standard `compose.yaml` at the root directory to ensure an isolated, zero-host-pollution development environment:
- **Environment First (実装前環境整備の原則)**: コード実装に着手する前に、まず開発・検証環境（`test`, `lint`, 必要に応じた `app`）を整備・疎通確認するのは当たり前の前提である。
- **Zero Host Toolchain Pollution**: Developers and contributors must NOT be required to install specific language runtimes, compilers, or linters directly onto their host machines (only Docker is required).
- **Shift-Left Containerization（開発・検証環境の先行配備・最優先タスク化原則）**:
  - Ceremony 1（エピック分解）および Ceremony 2（スプリント計画）において、**Epic 1 の第1スプリント初手（TASK-1.1）で最優先に `compose.yaml`（`test` / `lint` サービス等）を配備するタスクを計画すること**。
  - **TASK-1.1 Environment Bootstrap Phase**: TASK-1.1 は開発・検証環境の疎通確認フェーズであり、アプリ実装を含まない。`docker compose run --rm test go version` や `docker compose run --rm lint golangci-lint --version`、`docker compose run --rm test echo OK` によって Compose ツールチェーンの正常稼働をブートストラップ検証する。
  - ホストマシン上の特定CLIツール（`golangci-lint`, `pytest`, `eslint` 等）の存在を前提としたタスク検証を厳禁とし、**すべてのタスクの `verify_command` はコンテナ経由（例: `docker compose run --rm test ...` または `docker compose run --rm lint ...`）で記述すること**。
  - これにより、開発者はホスト環境を一切汚染することなく、初回のスプリントからDockerのみで一貫したテスト・リント検証を実行できる。
- **Service Composition**:
  - `app`: Runs the application in development mode with source code volume mounts (`.:/app` or equivalent) for immediate feedback.
  - `test`: Executes unit/integration test suites inside the isolated container (`docker compose run --rm test` or equivalent).
  - `lint`: Runs static analysis and formatting checks inside the container (`docker compose run --rm lint` or equivalent).
  - `proxy` (Optional): Reverse proxy serving as the single entrypoint when multiple backend services or web UIs require unified routing.
- **Composable Infrastructure & Middleware (DB / MQ)**:
  - When persistence (e.g. PostgreSQL, Redis) or asynchronous messaging/queues (e.g. RabbitMQ) are required, compose them as official service containers within `compose.yaml`.
  - Always implement robust healthchecks and startup ordering via `depends_on: { condition: service_healthy }`.
  - Adhere to official environment variable conventions (e.g. `POSTGRES_PASSWORD`, `RABBITMQ_DEFAULT_USER`) without custom prefixes.

## 2. ⚙️ Standard Developer Shortcuts (Optional Makefile)
- A `Makefile` is OPTIONAL.
- If a `Makefile` is provided, its targets (e.g. `make up`, `make test`, `make lint`) MUST act as lightweight wrappers around `docker compose` commands (e.g. `docker compose up`, `docker compose run --rm test`), rather than invoking host-installed toolchains directly.

## 3. 🚀 Automated CI/CD Pipeline (GitHub Actions)
Initial architectural milestones and sprint backlogs MUST include continuous integration setup:
- A GitHub Actions workflow MUST be defined at `.github/workflows/ci.yml`.
- The pipeline MUST automatically run on pull requests and pushes to `main`, validating:
  1. Build compilation
  2. Test execution and code coverage reporting
  3. Linter / formatting validation

## 4. 📦 Reproducible Production Image & Operational Readiness
- Deliver a lightweight, hardened production `Dockerfile` (multi-stage build targeting distroless/scratch/alpine) for deployment.
- Expose standard operational health check endpoints (e.g. `/healthz` or `/livez`) when running as a network service.
