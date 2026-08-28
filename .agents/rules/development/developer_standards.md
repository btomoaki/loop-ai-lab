# 💻 Universal Developer & Engineering Standards

Every developer and AI agent MUST naturally and instinctively enforce the following baseline engineering disciplines across all initiatives:

---

## 1. 🛠️ Reproducible Development Environment (Mandatory Baseline)
- **Zero-Friction Local Setup**: Always provide a clean, reproducible development workflow. Standard lifecycle commands (e.g. `make build`, `make test`, `make run`, `make lint`) or clean container environments must be established naturally alongside application code.
- **Self-Contained Execution**: Ensure new contributors or automated CI runners can clone, build, and test the project with a single command.

---

## 2. 🧪 Automated Testing Discipline (Code Without Tests is Incomplete)
- **Mandatory Test Coverage**: Every domain logic, usecase handler, and edge-case calculation MUST be accompanied by automated unit/integration tests.
- **Regression Prevention**: Test positive paths, negative paths, boundary inputs (nil/null, empty strings, payload limits), and expected error codes.
- **Automated Verification**: Ensure all tests run and pass cleanly via standard test tooling (`go test ./...`, `pytest`, `npm test`).

---

## 3. 📜 Modern API & Delivery Standards
- **Formal API Contracts**: When building web/HTTP delivery endpoints, accompany them with formal OpenAPI 3.0 / Swagger YAML specifications (`docs/openapi.yaml`) as standard industry practice.
- **Client Usability**: Ensure clear endpoint routing, structured error responses, and discoverable documentation.

---

## 4. 🧩 Interface Segregation & Test Mockability
- **Accept Interfaces, Return Structs**: Design minimal, focused interfaces at delivery and infrastructure boundaries to allow straightforward mocking during automated tests.

---

## 5. 📖 Comprehensive Project Documentation (Mandatory README)
Every repository/workspace MUST include a comprehensive and standard `README.md` at the root directory documenting:
- **Build & Test Executions**: Step-by-step instructions for local validation (e.g. `make build`, `make test`, `make lint`).
- **Development Environment Setup**: Prerequisites, toolchains, and initial workspace bootstrap procedures.
- **Directory Structure Map**: A text-based tree view demonstrating Clean Architecture layer mapping.
- **API Reference & OpenAPI (Swagger)**: High-level overview of endpoints and instructions on how to locate and view the OpenAPI contract (`docs/openapi.yaml`).
- **Configuration & Environment Variables**: Namespace-grouped environment variables table (names, types, default values, descriptions).
- **Container Verification Guide**: Steps to build the Docker image, run it locally, and verify non-root UID execution (`docker run --user 65532 ...`).
- **CI/CD pipeline Status**: GitHub Actions status verification and workflow overview.
- **Architectural Reference Links**: Clear pointers to project ADRs (`references/decisions.md`) for architectural alignment.
