# 💻 Universal Developer & Engineering Standards

Every developer and AI agent MUST naturally and instinctively enforce the following baseline engineering disciplines across all initiatives:

---

## 1. 🛠️ Reproducible Development Environment (Mandatory Baseline)
- **Environment First Principle (環境整備先行の原則)**: 実装前に開発・検証環境（`compose.yaml`）を完璧に整備するのはエンジニアリングとして当たり前の前提である。
- **Zero Host Toolchain Pollution**: Never require developers to install specific language compilers, runtimes, or linters directly onto their host machines. All local development workflows (running, building, testing, linting) must be self-contained and isolated within Docker Compose (`compose.yaml`).
- **Containerized Verification Commands (`verify_command`)**: Every sprint task's automated verification command (`verify_command`) MUST invoke containerized tools via Docker Compose (e.g. `docker compose run --rm test ...` or `docker compose run --rm lint ...`), strictly forbidding bare host commands (e.g. bare `go test`, `pytest`, `npm test`, or `golangci-lint run` directly on the host machine).
- **Target File Existence & Prerequisite Governance (`container_and_compose_standards.md`)**:
  - Commands targeting `compose.yaml` (or `-f <path>`) and `Dockerfile` (or `-f <path>`) MUST ensure the target configuration file exists before executing verification commands.
  - Tasks specifying `docker compose` verifications MUST explicitly declare dependency (`depends_on`) on the task deploying that compose configuration, or deploy it as part of the initial bootstrap phase (`TASK-1.1`).
- **Task-Appropriate Verification (タスクの性質に応じた検証の原則)**:
  - **TASK-1.1: 開発・検証環境ブートストラップフェーズ (Environment Bootstrap Phase)**:
    - TASK-1.1 is strictly dedicated to establishing Docker Compose infrastructure (`compose.yaml`, `go.mod`, directory skeleton with `.gitkeep`) and verifying toolchain operational readiness.
    - TASK-1.1 MUST NOT contain application logic, constructors, or HTTP server code.
    - Verification commands for TASK-1.1 MUST be limited to toolchain/syntax verification (e.g. `docker compose run --rm test go version`, `docker compose run --rm lint golangci-lint --version`, `docker compose run --rm test echo OK`, or `.gitkeep` file checks).
    - NEVER enforce premature compilation (`go build ./cmd/server`) or domain tests (`go test ./...`) on TASK-1.1 before application code is created in subsequent tasks!
  - **Setup / Skeleton / Config Tasks (環境・骨格・設定タスク)**:
    - For configuration or skeleton tasks (e.g. directory layout, infrastructure config), use lightweight, image-independent one-shot verification: `docker compose run --rm <service> echo OK` (e.g. `docker compose run --rm test echo OK`), ensuring clean verification without relying on specific binaries inside disparate images or creating lingering containers.
    - NEVER enforce premature compilation or test commands on skeleton tasks!
  - **Code & Logic Tasks (ドメイン・ユースケース・インフラ実装タスク)**: Verify via containerized unit tests and linters (`docker compose run --rm test go test -v ./...`).
- **No Ambiguity & Explicit Enumeration Mandate (受入条件における具体化と省略禁止の原則)**:
  - Acceptance Criteria (AC) MUST NEVER use `"etc."`, `"and so on"`, or vague placeholders.
  - All targets, directories, configurations, and assertions MUST be explicitly and exhaustively enumerated.
  - For directory skeleton tasks, all required Clean Architecture directories (e.g. `cmd/server/`, `internal/domain/model/`, `internal/domain/service/`, `internal/usecase/`, `internal/interface/`, `internal/infrastructure/`, and `docs/`) and their `.gitkeep` files MUST be explicitly stated in the AC.
  - For Docker Compose tasks, service definitions, ports (e.g. `8080:8080`), base images, working directories (`/app`), and volume mounts (`.:/app`) MUST be explicitly stated in the AC to guarantee 100% specification traceability.
- **Self-Contained Execution**: Ensure new contributors can clone and immediately start developing, testing, and linting with single `docker compose` commands (e.g. `docker compose up`, `docker compose run --rm test`).

---

## 2. 🧪 Automated Testing Discipline (Code Without Tests is Incomplete)
- **Mandatory Test Coverage**: Every domain logic, usecase handler, and edge-case calculation MUST be accompanied by automated unit/integration tests.
- **Regression Prevention**: Test positive paths, negative paths, boundary inputs (nil/null, empty strings, payload limits), and expected error codes.
- **Automated Verification**: Ensure all tests run and pass cleanly inside containerized testing environments (`docker compose run --rm test` or equivalent standard tooling).
- **🚫 Strict Prohibition of Fake Grep Testing (ハーネス形骸化の完全禁止)**:
  - Verification commands (`verify_command`) MUST NOT pass executable scripts (e.g. `scripts/health-check.sh`, smoke tests) via mere static grep inspection (e.g. `grep -q 'trap' scripts/health-check.sh && echo OK`).
  - All executable test/health scripts MUST actually be executed and verified with zero exit code (`sh scripts/health-check.sh`).
- **🌐 Mandatory Real E2E HTTP Communication & Asset Smoke Test (実通信・実画像検証の義務化)**:
  - Applications exposing HTTP APIs MUST include automated containerized smoke tests verifying actual network delivery:
    1. **Live Health Probe**: `curl -s -f http://localhost:8080/healthz` returning HTTP `200` with `status: ok`.
    2. **Real Binary Download & Magic Bytes Verification**: `curl -s -f "http://localhost:8080/api/avatar?seed=test" -o /tmp/avatar.png` followed by binary format verification (`file /tmp/avatar.png | grep -q "PNG image data, 250 x 250"` and `Content-Type: image/png` validation).

---

## 3. 📜 Platform vs Application Responsibility Boundary & Delivery Standards
- **Formal API Contracts**: When building web/HTTP delivery endpoints, accompany them with formal OpenAPI 3.0 / Swagger YAML specifications (`docs/openapi.yaml`) as standard industry practice. Document all endpoints, parameters, and error codes.
- **Platform vs Application Responsibility Boundary (プラットフォームとアプリの責務分解点)**:
  - **Platform Responsibility (インフラ/プラットフォームの責務)**: IP-based Rate Limiting, DDoS / WAF protection, SSL/TLS termination, and ingress routing are strictly the responsibility of the edge platform (e.g. Cloud Armor, API Gateway, or Reverse Proxy).
  - **Application Responsibility (アプリケーションの責務)**: The application MUST remain strictly stateless and lightweight. It MUST NOT embed in-memory IP rate limiters (which break stateless auto-scaling and cause unnecessary memory leaks).
  - **Platform Co-operation Contract (PFとの協調契約)**: The application must fulfill its platform contract via:
    1. Dynamic port binding via `$PORT` (defaulting to 8080).
    2. Lightweight health probe endpoint (`GET /healthz` returning `200 OK {"status":"ok"}`).
    3. Graceful shutdown on `SIGTERM` / `SIGINT` (draining within 10s).
    4. Internal request timeout enforcement (`context.WithTimeout`) to prevent thread leakage.
- **Client Usability**: Ensure clear endpoint routing, structured error responses, and discoverable documentation.

---

## 4. 🛡️ Container Security & Cloud-Native Statelessness (FinOps & Hardening)
- **Container Hardening (Non-Root Execution)**: Production Docker images MUST run as a dedicated non-root user (e.g. UID `65532:65532` for Distroless) to enforce least-privilege security.
- **Stateless Operation**: Design services for stateless execution suitable for Google Cloud Run (auto-scaling 0 to N, zero reliance on local disk persistence, graceful shutdown within 10s on SIGTERM/SIGINT).
- **Resource Efficiency (FinOps)**: Optimize for low memory footprint and CPU efficiency, avoiding memory leaks and unnecessary background threads.
- **Container Verification Standards (Zero Flakiness & Non-Destructive Testing)**:
  - **Image Size Assertion**: When validating image size constraints (e.g. < 500MB / MySQL image baseline), use canonical arithmetic inspection:
    `docker image inspect <image> --format '{{.Size}}' | awk '{if ($1/1024/1024 < 500) exit 0; else exit 1}'`
    Do NOT use fragile regex on string output or broken awk syntax.
  - **Non-Root Assertion**: Validate execution user statically via `docker image inspect <image> --format '{{.Config.User}}' | grep -E '^(65532|nonroot)'`.
  - **Container Lifecycle Pair & Guaranteed Cleanup (起動・停止のペア義務化)**:
    - **One-Shot Ephemerality (`--rm`)**: All single-use test, lint, and build verification commands MUST use `docker compose run --rm <service>` to ensure instant and automatic container cleanup upon exit.
    - **Multi-Container E2E Guaranteed Cleanup**: Multi-container test scripts (e.g. spinning up a server and querying it via client) MUST guarantee complete teardown under all circumstances (including failures and interrupts) via `trap 'docker compose down -v' EXIT INT TERM` or `docker compose up --abort-on-container-exit --exit-code-from <test-service>`.
    - **Prohibition of Naked / Unpaired Background Containers**: Never execute standalone background commands (`docker run -d`, `docker start`, or host `&`) without an automated guaranteed cleanup mechanism. Never execute blocking foreground `docker run` inside automated verification commands.

---

## 5. 🧩 Interface Segregation & Test Mockability
- **Accept Interfaces, Return Structs**: Design minimal, focused interfaces at delivery and infrastructure boundaries to allow straightforward mocking during automated tests.

---

## 6. 📖 Comprehensive Project Documentation (Mandatory README)
Every repository/workspace MUST include a comprehensive and standard `README.md` at the root directory documenting:
- **Clean Containerized Setup**: Instructions for running, testing, and linting via Docker Compose (e.g. `docker compose up`, `docker compose run --rm test`, `docker compose run --rm lint`) without host toolchain pollution.
- **Development Environment Prerequisites**: Explicitly state that only Docker & Docker Compose are required on the host machine.
- **Directory Structure Map**: A text-based tree view demonstrating Clean Architecture layer mapping.
- **API Reference & OpenAPI (Swagger)**: High-level overview of endpoints and instructions on how to locate and view the OpenAPI contract (`docs/openapi.yaml`).
- **Configuration & Environment Variables**: Namespace-grouped environment variables table (names, types, default values, descriptions).
- **Container Verification Guide**: Steps to build the hardened production Docker image, run it locally, and verify non-root UID execution (`docker run --user 65532 ...`).
- **CI/CD Pipeline Status**: GitHub Actions status verification and workflow overview.
- **Architectural Reference Links**: Clear pointers to project ADRs (`references/decisions.md`) for architectural alignment.

---

## 7. 🚫 Prohibition of Package Lockfile Hallucination (パッケージ管理ロックファイルのハルシネーション禁止)
- **Zero Lockfile Generation by LLM**: AI agents and developers MUST NEVER generate, edit, or hallucinate package manager lockfiles containing cryptographic checksums (e.g. `go.sum`, `package-lock.json`, `poetry.lock`, `Cargo.lock`).
- **Manifest-Only Dependency Declaration**: All dependencies and version constraints MUST strictly be declared in human-managed manifest files (e.g. `go.mod`, `package.json`, `pyproject.toml`).
- **Toolchain Exclusive Ownership**: Lockfiles must strictly and exclusively be created, resolved, and updated by official package management toolchains (e.g. Go compiler, npm, cargo) during container execution.

