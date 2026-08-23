# 🏗️ Go Clean Architecture & Dependency Injection Rules

## 1. 4-Layer Separation Standard
- **Domain Layer (`internal/domain/`)**: Pure business entities, structs, and domain interface definitions. ZERO external dependencies.
- **Usecase Layer (`internal/usecase/`)**: Application logic orchestration. Depends ONLY on Domain interfaces.
- **Delivery Layer (`internal/delivery/`)**: HTTP handlers, router wiring, request/response DTOs. Depends ONLY on Usecase interfaces.
- **DI Container & Wiring (`cmd/server/main.go` or `internal/di/`)**: Constructor-based assembly of concrete implementations.

## 2. 💉 Interface Injection & UT Mockability Directive (CRITICAL)
1. **Accept Interfaces, Return Structs**:
   - Every layer boundary MUST accept Go interfaces as parameters to constructors/functions (e.g., `NewAvatarUsecase(repo domain.AvatarRepository)`).
   - Functions MUST return concrete structs or interfaces depending on usage.
2. **Framework-Free DI**:
   - Do NOT use reflection-heavy DI frameworks (e.g. `uber-go/dig`, `wire` unless explicitly required).
   - Use clean, explicit constructor interface injection.
3. **Unit Testability (UT)**:
   - Interface injection ensures all dependencies can be cleanly mocked using standard Go mocks or stub structs in `_test.go` files without spinning up external servers or databases.

## 3. 🛑 Graceful Shutdown & Cloud-Native Execution Directive
- **Signal Notification**:
  - `cmd/server/main.go` MUST listen for OS signals (`syscall.SIGINT`, `syscall.SIGTERM`) via `signal.Notify(quit, os.Interrupt, syscall.SIGTERM)`.
- **Server Shutdown**:
  - Upon signal catch, trigger `srv.Shutdown(ctx)` with `context.WithTimeout(context.Background(), 10*time.Second)` to allow clean request draining without 503 errors during Cloud Run scaling/redeployments.

## 4. 📜 OpenAPI 3.0 (Swagger) Specification Standard
- **Contract Specification**:
  - API delivery boundaries MUST be documented via OpenAPI 3.0 specification (`docs/openapi.yaml`).
- **Endpoint Documentation**:
  - Explicitly document `/avatar` or `/identicon` endpoints, `seed` query validation, HTTP 200 `image/png` binary response, and error payload schemas.
