# Loop Controller Agent Policy (Clean Architecture - ldap-es-syncer Standard)

## 🐹 Core Go Architecture & Execution Principles

1. **Standard Go Project Layout (ldap-es-syncer Pattern)**:
   - `cmd/main.go`: Application entrypoint calling `di.NewContainer()` / `di.Initialize()`.
   - `internal/domain/model/`: Pure Go structs & value objects (e.g. `avatar.go`). NO algorithms or hash logic here.
   - `internal/domain/repository/`: Pure Go interface contracts (e.g. `avatar_repository.go`).
   - `internal/application/usecase/`: Application business orchestration using repository interfaces. NO low-level hash/grid math here!
   - `internal/infrastructure/config/`: Configuration loader (`config.go`).
   - `internal/infrastructure/generator/`: Concrete identicon generator engine (MD5 hash, 5x5 grid calculation, PNG drawing).
   - `internal/infrastructure/handler/`: HTTP handlers & endpoints (`avatar_handler.go`).
   - `internal/di/`: Dependency Injection container (`di.go` assembles all components).

2. **Package Collision Prevention (image/color)**:
   - ALWAYS use standard Go `image/color` package (`color.RGBA`) for color representations.
   - NEVER create custom packages named `color` or files like `domain/color/` to avoid collision with standard `image/color`.

3. **Test & Debugging Integrity (テスト改ざん・論理迷走の厳禁)**:
   - When tests or compilation fail, NEVER modify, weaken, or delete test assertions or discuss changing business logic!
   - ALWAYS fix the underlying implementation code in `internal/...` to satisfy the interface contract.
   - Compare `image/color.RGBA` directly with `==` (never invent non-existent methods like `.Equal()`).

4. **Go Code Quality & Code Smell Prevention**:
   - NO LONG PARAMETER LISTS: Maximum 3 parameters per function. Use struct literals (`&model.Avatar{...}`) or Parameter DTOs.
   - Permissive 3rd-party Go packages (`gin`, `chi`, `wire`, `prometheus`, `gorm`, `viper`) are ENCOURAGED.
   - Co-create matching `*_test.go` unit tests for every feature component created.

5. **Executor Output Format Enforcement**:
   - Executor MUST reply ONLY using code blocks preceded by `# FILE: relative/path.ext`.

5. **Flexible Debugging & Repair Scope (デバッグ修復時の一括修正許可)**:
   - Feature Creation Phase: Keep 1 feature + 1 matching test per step.
   - Repair/Debugging Phase (when Harness Fails): Evaluator MUST instruct fixing ALL broken, mismatched, or out-of-sync files simultaneously in a single step (including `*_test.go`, `di/di.go`, and implementation files) to break compile loops instantly!

6. **Living Spec (README.md) Protection Mandate**:
   - `README.md` is the SINGLE SOURCE OF TRUTH.
   - Evaluator MUST NOT delete, simplify, or degrade the core architecture, algorithm, or domain specifications in `README.md`.
   - Updating `README.md` is ONLY permitted for updating actual created file paths and execution/test commands!

7. **Symbol & Import Integrity (モグラ叩き防止)**:
   - NEVER delete existing exported constructors or methods (e.g. `NewGrid`, `NewAvatar`) when cleaning up unused imports or fixing compiler errors!
   - ALWAYS preserve established type definitions, interfaces, and function signatures.
