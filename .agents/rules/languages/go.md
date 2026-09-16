# 🐹 Go Language Guidelines & Clean Architecture

## 1. Directory & Package Layout (Standard Go Clean Architecture Layout)
- `cmd/server/`: Main application entrypoint (`cmd/server/main.go` - binds `$PORT`, graceful shutdown, wire dependencies).
- `internal/domain/model/`: Pure Go struct schemas and value definitions (pure data containers with exported fields ONLY; strictly NO functions, methods, constructors, validations, return statements, or test files (`*_test.go`)).
- `internal/domain/service/`: Domain validations, computations, algorithms, and transformations (e.g. input seed validation, grid symmetry generation, color/hash extraction; stateless, zero external dependencies + Unit Tests).
- `internal/domain/rasterizer.go`: Output Port interface (`type Rasterizer interface`) owned by domain.
- `internal/domain/usecase/`: Input Port interfaces (e.g. `internal/domain/usecase/avatar_usecase.go` defining `type AvatarUsecase interface`). Owned by domain so delivery controllers can mock usecases completely without importing concrete application logic.
- `internal/application/usecase/`: Concrete application business workflow orchestrators (e.g. `internal/application/usecase/avatar_usecase.go` implementing `domain/usecase.AvatarUsecase`, accepting `domain.Rasterizer` for 100% isolated usecase UT).
- `internal/delivery/http/`: Delivery adapters (HTTP handlers `AvatarHandler`, `HealthHandler`, `StaticHandler`). **STRICT PROHIBITION on naming package `interface`** (Go reserved keyword causing fatal `syntax error: unexpected interface, expected package name`). Handlers must depend strictly on `domain/usecase` interfaces.
- `internal/infrastructure/png/`: Concrete drivers (e.g. `PNGRasterizer` implementing `domain.Rasterizer` using standard `image/png`).
- `web/static/`: Static assets embedded into binary via `//go:embed web/static/*`.

## 2. Idiomatic Go Practices
1. **Interface Segregation**: Accept interfaces in constructors (`NewAvatarHandler(u usecase.AvatarUsecase)`), return concrete structs (`*AvatarHandler`).
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

## 5. Clean Architecture DIP & Double-Mockability Mandate
1. **Double-Mockability for 100% Isolated Unit Tests**:
   - **HTTP Controller UT**: Handlers in `internal/delivery/http/` depend strictly on input port interfaces in `internal/domain/usecase/`. In handler unit tests, inject mock usecases to test HTTP query parsing, status codes, and headers in sub-millisecond isolation without running application logic.
   - **Application Usecase UT**: Orchestrators in `internal/application/usecase/` depend strictly on output port interfaces in `internal/domain/` (e.g. `domain.Rasterizer`). In usecase unit tests, inject mock drivers to test orchestration flow without executing graphic rendering.
   - **Domain Service UT**: Algorithms in `internal/domain/service/` are pure stateless functions tested with zero mocks.
2. **Interface Placement in Domain**: In accordance with Clean Architecture and Dependency Inversion Principle (DIP), repository, rasterizer, and usecase contract interfaces MUST be defined strictly within `internal/domain/` or `internal/domain/usecase/`.
3. **Implementation in Infrastructure & Application**: `internal/infrastructure/` implements domain output interfaces; `internal/application/usecase/` implements domain input interfaces. Defining interfaces in outer layers and importing them from inward layers is strictly prohibited.
4. **Strict Inward Dependency**: Inward layers (`internal/domain/` and `internal/application/`) are STRICTLY FORBIDDEN from importing outer layers (`internal/infrastructure/` or `internal/delivery/`) to eliminate Go's fatal `import cycle not allowed` compiler error.
5. **Interface Definition Scope Exemption**: Downstream sprints (e.g. infrastructure rasterizer, CI verification, delivery adapters) are explicitly permitted to add new interface contract files (e.g. `internal/domain/rasterizer.go`, `internal/domain/usecase/avatar_usecase.go`) in the domain package to satisfy DIP without scope deadlocks. Modifying existing domain calculation logic or struct definitions remains forbidden.

## 6. Single HTTP Stack Mandate & Ghost Package Prohibition
1. **Unified HTTP Router**: Standard library `net/http` (Go 1.22+ routing) is the primary HTTP standard.
2. **Zero Conflicting Frameworks**: Never concurrently import or mix disparate HTTP frameworks (e.g. `github.com/gin-gonic/gin` and `github.com/gorilla/mux`). Unused handler files must be purged immediately to keep `go.mod` and `go.sum` clean.

## 7. Container Base Image & Compiler Synchronization
1. **Modern Alpine Base**: Dockerfiles must specify maintained, modern compiler base images (e.g. `golang:alpine`) rather than obsolete fixed toolchains (e.g. `golang:1.21`), preventing `go.mod requires go >= X` build failures.

