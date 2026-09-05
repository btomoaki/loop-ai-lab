# 🐹 Go Language Guidelines & Clean Architecture

## 1. Directory & Package Layout (Standard Go Project Layout)
- `cmd/`: Main application entrypoints (e.g. `cmd/server/main.go`).
- `internal/domain/model/`: Pure Go struct schemas and value definitions (pure data containers with exported fields ONLY; strictly NO functions, methods, constructors, validations, return statements, or test files (`*_test.go`)).
- `internal/domain/service/`: Domain validations, computations, algorithms, and transformations (e.g. input seed validation, grid symmetry generation, color/hash extraction; stateless, zero external dependencies).
- `internal/usecase/`: Application business workflow handlers and orchestrators.
- `internal/interface/`: Delivery adapters (HTTP handlers, CLI parsers, OpenAPI/Swagger endpoints).
- `internal/infrastructure/`: Concrete drivers (storage, file I/O, external network clients).

## 2. Idiomatic Go Practices
1. **Interface Segregation**: Accept interfaces in constructors (`NewService(repo DomainRepo)`), return concrete structs (`*Service`).
2. **Standard Tooling**: Code must format cleanly with `gofmt` and pass `go test ./...`.
3. **Explicit Error Handling**: Always check and wrap/propagate errors (`if err != nil`).
4. **Third-Party Libraries & Dependencies**: Avoid reinventing the wheel. Actively adopt popular, well-maintained, and trending third-party packages in the modern Go ecosystem for common requirements (such as HTTP routing, testing assertions, structured logging, or image processing) where standard library extensions would become complex. The selection of libraries must reflect current industry best practices.
5. **Domain Model Purity (Zero Logic & Zero Tests in Model Package)**: Structs in `internal/domain/model/` must strictly remain pure data structures (fields only). Zero functions, constructors (`NewX`), methods, 'return' statements, or test files (`*_test.go`) are permitted in `internal/domain/model/` (enforced by automated test harnesses). All constructors, validations, algorithms, transformations, AND their corresponding unit tests MUST reside in `internal/domain/service/`.

## 3. Go Module & Dependency Wiring
- **Explicit Module Initialization**: A new Go workspace repository MUST be initialized explicitly with `go mod init <module_name>` at the very start of the development lifecycle, establishing the canonical module root before writing domain code or executing tests.
- The Go module name must match the defined project/repository module name.
- **Checksum & Dependency Resolution**: Generating fake or manual `go.sum` checksum entries is strictly forbidden. All dependency locking MUST be performed via `go mod tidy` pulling from official Go proxy repositories.
- **Harness Wiring**: If `go.mod` or DI wiring configuration (e.g., `google/wire`) exists, the test harness must run dependency resolution (e.g., `go mod tidy`) and generate DI code before running tests.
- **Terminology**: Always refer to dependency injection as "Dependency Wiring" or "DI Wiring" (avoid the term "DI Container" to prevent confusion with Docker/OCI containers).

## 4. Import Resolution & Entrypoint
- Internal package imports must be prefixed with the project's root module name (do not use external placeholders or relative paths).
- The main entrypoint must always be located at `cmd/server/main.go`.
