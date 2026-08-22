# Docker & Container Infrastructure Verification Harness Rule

## Rule Definition
1. **Real Docker Build Mandate**: Container epics MUST NOT use `go test`. They MUST execute `docker build -t ... .` to verify Multi-stage compilation.
2. **Runtime & Environment Variable Assertion**: Test harness MUST execute `docker run -d -p 8080:8080 -e PORT=8080 ...`, check container liveness, and perform teardown (`docker stop` & `docker rm`).
