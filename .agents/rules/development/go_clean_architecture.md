# Go Clean Architecture Development Standard

## 1. Clean Architecture Layer Hierarchy
All Go applications developed in this project must strictly conform to the 4-layer Clean Architecture layout:

1. **Domain Layer (`internal/domain/`)**:
   - Contains pure business entities (`model/`) and repository interfaces (`repository/`).
   - Must have zero external third-party dependencies.

2. **Application Layer (`internal/application/`)**:
   - Contains usecases (`usecase/`) orchestrating business logic and flow control.
   - Depends only on the Domain layer interface contracts.

3. **Infrastructure Layer (`internal/infrastructure/`)**:
   - Implements domain repository interfaces (e.g., persistence, hashing, image generation, external clients).

4. **Interface Adapter Layer (`internal/interface/adapter/` & `cmd/`)**:
   - Contains HTTP handlers, REST API routing, CLI entrypoints, and static asset embedding (`cmd/server/main.go`).

## 2. Dependency & Licensing Policy
- **Go Standard Library Priority**: Leverage standard Go built-in packages (`net/http`, `crypto`, `image`, `encoding/json`, `os`, `fmt`) whenever applicable.
- **Approved Commercial OSS Licenses**: Permitted 3rd-party packages must use commercial-friendly open-source licenses (**MIT, Apache-2.0, or BSD**).

## 3. Mandatory Unit Testing Standard
- Every implementation file (`*.go`) must be paired with unit test coverage (`*_test.go`).
- Domain entities and Application usecases must pass unit tests with 100% harness verification.
