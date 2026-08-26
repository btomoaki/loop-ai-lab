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
