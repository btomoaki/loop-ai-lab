# 🏗️ Clean Architecture & Software Design Standards

## 1. Layer Separation Principles
1. **Domain Layer**: 
   - **Models / Entities / Value Objects**: Strictly pure data structures and schema representations (fields only). Never embed functions, constructors, validation logic, or return statements directly in model files.
   - **Domain Services**: Stateless business validations, calculations, generation algorithms, and transformations that operate on entities. Zero external dependencies.
   - **Domain Interfaces (Ports)**:
     - **Output Ports**: Interfaces for external drivers (e.g. `Rasterizer`, `Repository`) owned by `domain/`.
     - **Input Ports**: Interfaces for application usecases (e.g. `AvatarUsecase`) owned by `domain/usecase/` to allow delivery controllers to mock business logic completely.
2. **Application / Usecase Layer (`internal/application/usecase/`)**: Application workflows and orchestration implementing domain input ports and depending on domain output ports.
3. **Delivery Layer (`internal/delivery/http/`)**: Entrypoints, HTTP/REST controllers, CLI commands, and client handlers. Strictly avoid naming package `interface` (reserved keyword in Go/Java). Depends only on `domain/usecase/` input ports.
4. **Infrastructure Layer (`internal/infrastructure/`)**: Concrete adapters for persistence, rasterization, file systems, third-party network clients, and external drivers implementing domain output ports.

## 2. Dependency Inversion & Double-Mockability
- **High-level modules (Domain, Usecase) must not depend on low-level modules (Infrastructure, DB, Delivery)**; all dependencies point inward.
- **Double-Mockability for 100% Isolated Unit Testing**:
  - **Delivery UT**: HTTP controllers accept `domain/usecase` interfaces in constructors, allowing 100% isolated controller tests with mock usecases.
  - **Usecase UT**: Application usecases accept `domain` output port interfaces in constructors, allowing 100% isolated workflow tests with mock drivers.
- Constructors should accept interfaces and return concrete implementations to ensure 100% test mockability and seamless component replacement.

## 3. Domain Model Purity
- Keep Entities and Models decoupled from algorithmic complexity. Business algorithms (such as hash calculation, matrix symmetry generation, and encoding) belong in Domain Services or dedicated engines, keeping models simple, testable, and reusable.

## 4. 🧘 Anti-Complexity & YAGNI (You Aren't Gonna Need It)
- **Eliminate Premature Abstractions**: Avoid speculative generic frameworks, unnecessary interfaces with only a single implementation, or over-engineered design patterns not justified by the requirements.
- **Strict Adherence to Architectural Decisions (ADR)**: Stick strictly to the agreed decisions (`references/decisions.md`). Strictly forbid adding unrequested external libraries, alternative formats (e.g. SVG when PNG is specified), or redundant wrapper layers.
- **Single Responsibility & Minimal Surface Area**: Every package, struct, and function must have one single, unambiguous responsibility and expose the minimal necessary public API.
