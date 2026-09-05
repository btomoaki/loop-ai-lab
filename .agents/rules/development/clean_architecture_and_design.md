# 🏗️ Clean Architecture & Software Design Standards

## 1. Layer Separation Principles
1. **Domain Layer**: 
   - **Models / Entities / Value Objects**: Strictly pure data structures and schema representations (fields only). Never embed functions, constructors, validation logic, or return statements directly in model files.
   - **Domain Services**: Stateless business validations, calculations, generation algorithms, and transformations that operate on entities. Zero external dependencies.
2. **Usecase / Service Layer**: Application workflows and business orchestration. Depends only on Domain.
3. **Interface / Delivery Layer**: Entrypoints, HTTP/REST controllers, CLI commands, and client handlers.
4. **Infrastructure Layer**: Concrete adapters for persistence (SQL/NoSQL databases, caches), message brokers (MQ queues/subscribers), file systems, third-party network clients, and external drivers.

## 2. Dependency Inversion & Middleware Decoupling
- High-level modules (Domain, Usecase) must not depend on low-level modules (Infrastructure, DB, MQ); both must depend on abstractions/interfaces.
- Database access (repositories) and Message Queue operations (publishers/consumers) MUST be defined as interfaces in domain/usecase and implemented as concrete adapters in `internal/infrastructure/`.
- Constructors should accept interfaces and return concrete implementations to ensure 100% test mockability and seamless infrastructure replacement.

## 3. Domain Model Purity
- Keep Entities and Models decoupled from algorithmic complexity. Business algorithms (such as hash calculation, matrix symmetry generation, and encoding) belong in Domain Services or dedicated engines, keeping models simple, testable, and reusable.

## 4. 🧘 Anti-Complexity & YAGNI (You Aren't Gonna Need It)
- **Eliminate Premature Abstractions**: Avoid speculative generic frameworks, unnecessary interfaces with only a single implementation, or over-engineered design patterns not justified by the requirements.
- **Strict Adherence to Architectural Decisions (ADR)**: Stick strictly to the agreed decisions (`references/decisions.md`). Strictly forbid adding unrequested external libraries, alternative formats (e.g. SVG when PNG is specified), or redundant wrapper layers.
- **Single Responsibility & Minimal Surface Area**: Every package, struct, and function must have one single, unambiguous responsibility and expose the minimal necessary public API.
