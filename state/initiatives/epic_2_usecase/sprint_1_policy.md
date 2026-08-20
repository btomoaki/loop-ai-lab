```markdown
# Sprint 1 Implementation Policy: Avatar Generation UseCase & Domain Orchestration

## 1. Executive Summary & Objective

- **Epic:** Epic 2: Application UseCase & Business Logic
- **Sprint:** 1
- **Task Name:** Implement Avatar Generation UseCase and Domain Orchestration
- **Target Files:**
  - `workspace/avatar-service/internal/application/usecase/avatar_usecase.go`
  - `workspace/avatar-service/internal/application/usecase/avatar_usecase_test.go`
- **Primary Goal:** Construct the application use case layer responsible for orchestrating domain entity creation (`model.Avatar`) and delegating image rasterization to the domain output port (`repository.AvatarRenderer`). Ensure strict adherence to Go Clean Architecture, zero external dependencies, 100% statement/branch test coverage, and complete data-race freedom.

---

## 2. Clean Architecture & Layer Boundary Rules

### 2.1 Inward Dependency Rule
The Application layer (`internal/application/usecase`) occupies the second layer of the Clean Architecture model, situated between Presentation/Infrastructure and the Domain Core.

```
┌────────────────────────────────────────────────────────┐
│ Infrastructure (PNG Renderer, HTTP Handlers, Config)   │
│   │                                                    │
│   ▼                                                    │
│ Application (AvatarUseCase) ◄── [THIS SPRINT]          │
│   │                                                    │
│   ▼                                                    │
│ Domain (model.Avatar, model.Grid, repository.Renderer) │
└────────────────────────────────────────────────────────┘
```

1. **Permitted Imports:**
   - Standard Go library (e.g., `errors`, `fmt`, `strings`, `unicode/utf8`, `testing`).
   - Domain Model: `avatar-service/internal/domain/model`
   - Domain Repository / Ports: `avatar-service/internal/domain/repository`
2. **Strictly Prohibited Imports:**
   - Infrastructure packages (`avatar-service/internal/infrastructure/...`)
   - Presentation / HTTP packages (`net/http`, `avatar-service/internal/interface/...`)
   - Entrypoint packages (`avatar-service/cmd/...`)
   - Any third-party Go modules (Standard library only).
3. **Package Safety:** Never define custom packages named `color` or import custom color types. Use domain model types directly.

---

## 3. Technical Specification & Interface Contracts

### 3.1 Interface Definition (`AvatarUseCase`)
The `AvatarUseCase` interface defines the boundary for invoking avatar generation business workflows:

```go
package usecase

import (
    "avatar-service/internal/domain/model"
    "avatar-service/internal/domain/repository"
)

// AvatarUseCase specifies the primary use case contract for generating avatars.
type AvatarUseCase interface {
    // Generate creates an avatar from the given seed string and returns the rendered PNG binary.
    Generate(seed string) ([]byte, error)
}
```

### 3.2 Private Struct & Constructor Function
To enforce encapsulation and interface-driven programming:

- **Private Struct:**
  ```go
  type avatarUseCase struct {
      renderer repository.AvatarRenderer
  }
  ```
- **Provider Constructor:**
  ```go
  // NewAvatarUseCase creates a new instance of AvatarUseCase injected with an AvatarRenderer port.
  func NewAvatarUseCase(renderer repository.AvatarRenderer) AvatarUseCase {
      return &avatarUseCase{
          renderer: renderer,
      }
  }
  ```

### 3.3 Domain Orchestration Workflow
The `Generate(seed string) ([]byte, error)` method must execute the following sequence:

1. **Seed Handling:** Accept arbitrary seed strings (including empty strings, whitespace, ASCII, and multi-byte UTF-8).
2. **Domain Entity Instantiation:** Call `model.NewAvatar(seed)` to construct the `*model.Avatar` entity (which encapsulates MD5 hash computation, 5×5 symmetric grid construction, and RGB color derivation).
3. **Rasterization Delegation:** Pass the domain entity to the injected renderer port: `uc.renderer.Render(avatar)`.
4. **Error Propagation:** If `Render` returns an error, wrap or propagate the error gracefully without panic, without exposing infrastructure internals, and without leaking raw pointers.

---

## 4. Error Handling & Defensive Programming

1. **Zero Panics:** The use case must never panic on nil input, empty string, malformed strings, or downstream rendering failures.
2. **Graceful Degradation & Error Wrapping:** All errors returned by `renderer.Render(avatar)` must be returned as standard Go errors.
3. **Nil Safety:** Ensure the constructor or method safely handles unexpected nil conditions if passed invalid dependencies during testing.

---

## 5. Unit Testing & Quality Gate Standards

### 5.1 Test Suite Architecture (`avatar_usecase_test.go`)
- **Package:** `package usecase_test` or `package usecase` (table-driven tests).
- **Mocking Strategy:** Implement a lightweight in-memory mock struct satisfying `repository.AvatarRenderer`:
  ```go
  type mockAvatarRenderer struct {
      renderFunc func(avatar *model.Avatar) ([]byte, error)
  }

  func (m *mockAvatarRenderer) Render(avatar *model.Avatar) ([]byte, error) {
      if m.renderFunc != nil {
          return m.renderFunc(avatar)
      }
      return []byte("fake-png-data"), nil
  }
  ```

### 5.2 Mandatory Test Scenarios & Vectors
The test suite must validate:

| Test Case | Input Seed | Expected Behavior |
| :--- | :--- | :--- |
| **Standard ASCII** | `"user@example.com"`, `"alice"` | Successfully returns rendered bytes from mock renderer. |
| **Empty Seed** | `""` | Validates deterministic handling without panicking. |
| **Whitespace Seed** | `"   "`, `"\t\n"` | Correctly passes seed to domain model. |
| **Multi-byte UTF-8** | `"ユーザー"`, `"🌟🚀"`, `"こんにちは世界"` | Correctly processes UTF-8 characters without byte corruption. |
| **Renderer Failure** | `"error-seed"` | Propagates error returned by `renderer.Render` to caller. |
| **Nil Model Verification** | Injected mock receives valid non-nil `*model.Avatar` with populated grid and colors. |

---

## 6. Definition of Done (DoD) & Verification Checklist

- [ ] Target files are placed strictly in `internal/application/usecase/`.
- [ ] `AvatarUseCase` interface and `NewAvatarUseCase` constructor match the required signatures.
- [ ] Application layer contains zero imports from infrastructure or external third-party libraries.
- [ ] `go vet ./internal/application/usecase/...` passes with 0 warnings.
- [ ] `go test -race ./internal/application/usecase/...` passes with 0 failures and 0 race conditions.
- [ ] Unit test statement and branch coverage reaches **100%**.
- [ ] The test harness script `sprint_1_harness.sh` executes and exits with status code `0`.
```
