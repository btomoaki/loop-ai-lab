# 🏗️ Clean Architecture & Software Design Standards

## 1. Layer Separation Principles
1. **Domain Layer**: Core business models, value objects, and pure algorithmic logic. Must have zero external dependencies.
2. **Usecase / Service Layer**: Application workflows and business orchestration. Depends only on Domain.
3. **Interface / Delivery Layer**: Entrypoints, HTTP/REST controllers, CLI commands, and client handlers.
4. **Infrastructure Layer**: Persistence, file systems, third-party integrations, and external drivers.

## 2. Dependency Inversion
- High-level modules must not depend on low-level modules; both must depend on abstractions/interfaces.
- Constructors should accept interfaces and return concrete implementations to ensure 100% test mockability.
