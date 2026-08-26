# 📌 Epic Granularity & Single Responsibility Rules

## 1. Single Responsibility Principle
- Each classified Epic MUST represent a single responsibility domain (e.g. `epic_1_input_validation`).
- Do NOT create monolithic multi-domain composite epics.

## 2. 🛑 Feature & Infrastructure Epics Rule
- **Feature & Infrastructure Epics**:
  - Epics MUST be extracted for functional components (domain logic, validation, API) AND infrastructure/deployment domains explicitly specified in `references/*.md` (e.g. `epic_docker_containerization`, `epic_cloud_run_deployment`).
- **Mandatory Cloud & Container Epics**:
  - Requirements specified in `references/*.md` for **Docker Containerization** (`gcr.io/distroless/static-debian12`) AND **Google Cloud Run Public Cloud Deployment & Release** MUST be extracted as dedicated, independent Epics!
- **No Test-only Epics**:
  - Do NOT create standalone Epics exclusively for unit tests or benchmarking. Include testing tasks under their corresponding feature Epics.
