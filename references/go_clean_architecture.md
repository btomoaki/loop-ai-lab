# Go Clean Architecture & Coding Standards

## 🏛️ Clean Architecture Layout Standard
- `cmd/server/main.go`: Entry point initializing `di.NewContainer()`
- `internal/domain/model/`: Pure domain models, structs & value objects (No external dependencies)
- `internal/domain/repository/`: Domain repository ports (interfaces)
- `internal/application/usecase/`: Application business logic
- `internal/infrastructure/handler/`: HTTP handlers & routing
- `internal/di/`: Dependency Injection container (`di.go`)

## ⚠️ Package Collision Prevention
- ALWAYS use standard Go `image/color` package (`color.RGBA`).
- NEVER create custom packages named `color` or files like `domain/color`.

## 🛡️ Symbol & Import Integrity
- NEVER delete existing exported constructors (`NewGrid`, `NewAvatar`) or established interfaces when cleaning imports.
