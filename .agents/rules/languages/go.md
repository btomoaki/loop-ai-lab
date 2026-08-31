# 🐹 Go Language Guidelines & Clean Architecture

## 1. Directory & Package Layout (Standard Go Project Layout)
- `cmd/`: Main application entrypoints (e.g. `cmd/server/main.go`).
- `internal/domain/`: Pure Go structs, domain interfaces, and pure business logic (no external dependencies).
- `internal/usecase/`: Application business workflow handlers and orchestrators.
- `internal/interface/`: Delivery adapters (HTTP handlers, CLI parsers, OpenAPI/Swagger endpoints).
- `internal/infrastructure/`: Concrete drivers (storage, file I/O, external network clients).

## 2. Idiomatic Go Practices
1. **Interface Segregation**: Accept interfaces in constructors (`NewService(repo DomainRepo)`), return concrete structs (`*Service`).
2. **Standard Tooling**: Code must format cleanly with `gofmt` and pass `go test ./...`.
3. **Explicit Error Handling**: Always check and wrap/propagate errors (`if err != nil`).
4. **Third-Party Libraries & Dependencies**: Avoid reinventing the wheel. Actively adopt popular, well-maintained, and trending third-party packages in the modern Go ecosystem for common requirements (such as HTTP routing, testing assertions, structured logging, or image processing) where standard library extensions would become complex. The selection of libraries must reflect current industry best practices.

## 3. Go Module & Dependency Wiring
- The Go module name must match the defined project/repository module name.
- **Harness Wiring**: If `go.mod` or DI wiring configuration (e.g., `google/wire`) exists, the test harness must run dependency resolution (e.g., `go mod tidy`) and generate DI code before running tests.

## 4. Import Resolution & Entrypoint
- Internal package imports must be prefixed with the project's root module name (do not use external placeholders or relative paths).
- The main entrypoint must always be located at `cmd/server/main.go`.
