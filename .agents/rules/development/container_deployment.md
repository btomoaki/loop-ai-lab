# Containerization & Cloud Run Deployment Rule

## 1. Epic 5: Containerization Requirements
- **Multi-stage Dockerfile**: Build stage with Go toolchain, final stage using Distroless (`gcr.io/distroless/static-debian12`).
- Minimal Distroless image packaging with strictly essential runtime tools.

## 2. Epic 6: Cloud Run Deployment Requirements
- **Non-root Execution**: Container MUST run under a nonroot user account.
- **Dynamic PORT Binding**: Server MUST bind to `PORT` environment variable required by Cloud Run.
