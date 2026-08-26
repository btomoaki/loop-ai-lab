# 🛠️ Continuous Development & CI/CD Environment Policy

All generated projects and initiatives MUST adhere to continuous development, operational readiness, and developer experience standards from the initial sprints.

## 1. ⚙️ Standard Developer Interface (Makefile)
Every workspace repository MUST provide a standard `Makefile` at the root directory defining the following lifecycle targets:
- `make build`: Compiles the binary or production artifact.
- `make test`: Runs unit and integration test suites with race detection (`go test -race ./...`).
- `make lint`: Executes static analysis / linter checks (e.g. `golangci-lint run`).
- `make run`: Starts the application locally.

## 2. 🚀 Automated CI/CD Pipeline (GitHub Actions)
Initial architectural milestones and sprint backlogs MUST include continuous integration setup:
- A GitHub Actions workflow MUST be defined at `.github/workflows/ci.yml`.
- The pipeline MUST automatically run on pull requests and pushes to `main`, validating:
  1. Build compilation
  2. Test execution and code coverage reporting
  3. Linter / formatting validation

## 3. 📦 Reproducible Environment & Operational Readiness
- Deliver a lightweight `Dockerfile` (multi-stage build targeting scratch/alpine) for containerized deployment.
- Expose standard operational health check endpoints (e.g. `/healthz` or `/livez`) when running as a network service.
