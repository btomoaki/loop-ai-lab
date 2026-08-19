# Project Rules and Guidelines for ldap-es-syncer

This document defines specific architectural rules, design requirements, and workflows for this repository.

## 1. Project Structure (Clean Architecture)
Follow this directory structure strictly to ensure a technology-agnostic Domain layer:

- `internal/di/`: Dependency Injection container and wiring.
  - **Responsibility:** Initialize all providers (Infrastructure, Application, Domain) and resolve dependencies.
- `internal/domain/`: Core Business Logic
  - `model/`: Domain Entities and their associated business logic methods.
  - `repository/`: Interface definitions (Ports) for data persistence and external access.
  - `service/`: Domain Services that orchestrate complex business rules.
- `internal/application/`: Application Use Cases that coordinate the flow of data (e.g., UseCase orchestration).
- `internal/infrastructure/`: Concrete Implementations (Adapters)
  - `[provider_name]/`: Specific technology implementations (e.g., Database, External APIs, Message Brokers).
  - `config/`: Configuration and Environment variables.
    - **Responsibility:** Loading environment variables (using Go's `os` package or specialized config libraries) and providing individual configuration structs to the DI container.
- `cmd/`: Application entry points (Main functions).

## 2. Design Rules
- **Dependency Rule:** All dependencies must flow **inwards** (Infrastructure -> Application -> Domain). The Domain layer must have zero knowledge of specific technologies (e.g., no SQL, no LDAP specific logic).
- **Abstractions over Concretions:** Use interfaces defined in the Domain layer to interact with the Infrastructure layer.
- **Dependency Injection (DI):** Maintain loose coupling by injecting concrete infrastructure adapters into the application/domain via DI containers or constructors.
- **Naming Conventions:** Use generic names in the Domain layer (e.g., `UserRepository`) and specific names in the Infrastructure layer (e.g., `LdapUserRepository`).
- **Project-Specific Environment Variable Prefixes:** In alignment with global environment variable design standards, this project structures custom variables using the following namespaces in `.env`:
  - `APP_`: Global application lifecycle settings.
  - `SYNC_`: Sync workflow and daemon execution control.
- **Cloud-Native Logging Rule (Resource Efficiency):** The application is designed for cloud environments. Do not emit verbose success logs inside loops (e.g., "Successfully synchronized user X"). 
  - Restrict standard output (`stdout`) to lifecycle events (e.g., "Process started/completed") and single-line summary statistics (e.g., "Total processed: X/Y").
  - Detailed context must be reserved strictly for error logs (`stderr`) when an operation fails, ensuring that log storage and ingestion costs are minimized without sacrificing production debuggability.

## 3. Dependency Injection (DI) Implementation Rules
- **Decoupled Initialization:** The `internal/di` package must act strictly as a "Wiring Layer." It should not contain logic for instantiating concrete objects manually inside a single monolithic function.
- **Provider Pattern:** Each infrastructure adapter and application service must provide its own "Constructor" (Provider) function that returns an interface, not a concrete struct.
- **Dependency Resolution:**
  - The DI container should resolve dependencies by matching required interfaces with provided implementations.
  - If using a DI library, follow its idiomatic patterns (e.g., providing constructors to the container).
  - If using manual DI, the DI container should be composed of small, injectable factory functions to maintain high reusability.
- **Config Injection:** Do not pass the entire `Config` object to every provider. Inject only the specific configuration segment (e.g., `LdapConfig`) required by that specific provider.

## 4. Testing Rules
- **Unique Test Passwords:** When writing tests (unit tests or integration tests) that involve password verification, always use unique, robust, and distinct password strings (including alphanumeric characters and special symbols) for each test user/scenario instead of reusing a single common password (e.g., do not use `adminpassword` for all users; use `admin-password-1!`, `admin-password-2@`, etc.). This ensures tests are robust, adhere to strict security policies, and that assertions map correctly to individual test identities.
