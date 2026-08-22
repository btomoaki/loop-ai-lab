# Go Clean Architecture & Strict File Naming Rules

## 1. Architectural Layers & File Naming Conventions
- **Domain Models (`internal/domain/model/`)**:
  - File MUST be named after the target struct: `<struct_name>.go` (e.g. `avatar.go`, `grid.go`). Never use generic `model.go`.
- **Domain Repositories (`internal/domain/repository/`)**:
  - Contains ONLY Go interface definitions.
  - File MUST be named: `<interface_name>_repository.go` (e.g. `avatar_repository.go`).
- **Domain Services (`internal/domain/service/`)**:
  - Contains domain business logic and factories.
  - File MUST be named: `<service_name>_service.go` (e.g. `avatar_service.go`).
- **Application UseCases (`internal/usecase/`)**:
  - File MUST be named: `<usecase_name>_usecase.go` (e.g. `avatar_usecase.go`).

## 2. Module Import & Zero-External-Dependency Rule
- All internal package imports MUST use the exact module path: `avatar-service/internal/...` (NEVER use `workspace/avatar-service/`).
- Domain Core layer MUST use Go standard library ONLY (e.g. `context`, `crypto/rand`). NO third-party packages (e.g. `uuid`, `mgo`).

## 3. Implementation Order
1. Step 1 (Domain Data: `<struct_name>.go`)
2. Step 2 (Domain Interfaces: `<interface_name>_repository.go`)
3. Step 3 (Domain Services: `<service_name>_service.go`)
4. Step 4 (UseCases: `<usecase_name>_usecase.go`)
5. Step 5 (Infrastructure)
6. Step 6 (Interface Adapters)
